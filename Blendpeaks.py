# Blendpeaks by oormi creations
# A free and open source add-on for Blender
# Creates mountain peaks with a procedural material.
# http://oormi.in


bl_info = {
    "name": "Blendpeaks",
    "description": "Creates Mountain Peaks",
    "author": "Oormi Creations",
    "version": (0, 1, 5),
    "blender": (2, 80, 0),
    "location": "3D View > Blendpeaks",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/oormicreations/Blendpeaks",
    "tracker_url": "https://github.com/oormicreations/Blendpeaks/issues",
    "category": "Object"
}

import bpy
from mathutils import *
from bpy import context
import random

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

def ShowMessageBox(message = "", title = "BlendPeak Says...", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    
    

def creatematerial(sstool):
    mat = bpy.data.materials.new(name="BlendpeaksMat")
    mat.use_nodes = True
    matnodes = mat.node_tree.nodes
    matnodes['Material Output'].location = Vector((1400,220))
    matnodes['Principled BSDF'].location = Vector((800,1220))
    bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'
    mat.cycles.displacement_method = 'BOTH'

    #displacement
    coodpeak = matnodes.new('ShaderNodeTexCoord')
    gradpeak = matnodes.new('ShaderNodeTexGradient')
    mappeak  = matnodes.new('ShaderNodeMapping')
    ramppeak = matnodes.new('ShaderNodeValToRGB')

    coodpeak.location = Vector((-1700,50))
    gradpeak.location = Vector((-1500,50))
    mappeak.location  = Vector((-1300,50))
    ramppeak.location = Vector((-1100,50))
    
    gradpeak.gradient_type = 'SPHERICAL'
    mappeak.vector_type = 'POINT'
    ramppeak.color_ramp.elements[0].position = 0.75
    ramppeak.color_ramp.interpolation = 'EASE'
    
    matlinks = mat.node_tree.links
    matlinks.new(coodpeak.outputs[3], gradpeak.inputs[0])
    matlinks.new(gradpeak.outputs[0], mappeak.inputs[0])
    matlinks.new(mappeak.outputs[0], ramppeak.inputs[0])


    coodmask = matnodes.new('ShaderNodeTexCoord')
    gradmask = matnodes.new('ShaderNodeTexGradient')
    mapmask  = matnodes.new('ShaderNodeMapping')
    rampmask = matnodes.new('ShaderNodeValToRGB')

    coodmask.location = Vector((-1700,500))
    gradmask.location = Vector((-1500,500))
    mapmask.location  = Vector((-1300,500))
    rampmask.location = Vector((-1100,500))
    
    gradmask.gradient_type = 'SPHERICAL'
    mapmask.vector_type = 'POINT'
    mapmask.inputs[1].default_value[0] = -0.2
    rampmask.color_ramp.interpolation = 'EASE'
    
    matlinks.new(coodmask.outputs[3], gradmask.inputs[0])
    matlinks.new(gradmask.outputs[0], mapmask.inputs[0])
    matlinks.new(mapmask.outputs[0], rampmask.inputs[0])
    
    #erosion
    noiseero = matnodes.new('ShaderNodeTexNoise')
    rampero = matnodes.new('ShaderNodeValToRGB')
    mathero = matnodes.new('ShaderNodeMath')
    
    noiseero.name = "Eroscale"
    rampero.name = "Ero"
    
    noiseero.location = Vector((-237, 597))
    rampero.location = Vector((-26, 620))
    mathero.location = Vector((340, 375))

    
    noiseero.inputs[2].default_value = sstool.p_eroscale/10.0
    noiseero.inputs[3].default_value = 16
    rampero.color_ramp.elements[0].position = sstool.p_ero/100 #0.47
    rampero.color_ramp.elements[1].position = 1 - (sstool.p_ero/100) #0.58
    mathero.operation = 'MULTIPLY'
    
    matlinks.new(noiseero.outputs[0], rampero.inputs[0])
    matlinks.new(rampero.outputs[0], mathero.inputs[0])
    matlinks.new(rampmask.outputs[0], mathero.inputs[1])




    #seed
    ncoodseed = matnodes.new('ShaderNodeTexCoord')
    nmapseed  = matnodes.new('ShaderNodeMapping')
    vcoodseed = matnodes.new('ShaderNodeTexCoord')
    vmapseed  = matnodes.new('ShaderNodeMapping')
    
    nmapseed.name = "NSeed"
    vmapseed.name = "VSeed"

    ncoodseed.location = Vector((-1300,-600))
    nmapseed.location = Vector((-1100,-600))
    vcoodseed.location = Vector((-600,-600))
    vmapseed.location = Vector((-400,-600))
    
    nmapseed.inputs[1].default_value[0] = sstool.p_seed/10
    vmapseed.inputs[1].default_value[0] = sstool.p_seed/10
    
    matlinks.new(ncoodseed.outputs[0], nmapseed.inputs[0])
    matlinks.new(vcoodseed.outputs[0], vmapseed.inputs[0])
    
    #noise
    noisegross = matnodes.new('ShaderNodeTexNoise')
    noisefine = matnodes.new('ShaderNodeTexNoise')
    mix1 = matnodes.new('ShaderNodeMixRGB')
    mix2 = matnodes.new('ShaderNodeMixRGB')

    noisegross.name = "Gross"
    noisefine.name = "Fine"
        
    noisegross.location = Vector((-600,-90))
    noisefine.location = Vector((-600,-300))
    mix1.location = Vector((-350,170))
    mix2.location = Vector((-150,170))

    noisegross.noise_dimensions = '3D'
    noisegross.inputs[2].default_value = sstool.p_gross/10
    noisegross.inputs[3].default_value = 0
    noisefine.noise_dimensions = '2D'
    noisefine.inputs[2].default_value = sstool.p_fine/10
    noisefine.inputs[3].default_value = 16
    mix2.blend_type = 'SOFT_LIGHT'
    mix2.inputs[0].default_value = 1

    matlinks.new(rampmask.outputs[0], mix1.inputs[0])
    matlinks.new(ramppeak.outputs[0], mix1.inputs[1])
    matlinks.new(noisegross.outputs[0], mix1.inputs[2])
    matlinks.new(mix1.outputs[0], mix2.inputs[1])
    matlinks.new(noisefine.outputs[0], mix2.inputs[2])
    matlinks.new(nmapseed.outputs[0], noisegross.inputs[0])
    
    vnoisegross = matnodes.new('ShaderNodeTexVoronoi')
    vnoisefine = matnodes.new('ShaderNodeTexVoronoi')
    math1 = matnodes.new('ShaderNodeMath')
    math2 = matnodes.new('ShaderNodeMath')
    
    vnoisegross.name = "RidgeGross"
    vnoisefine.name = "RidgeFine"
    
    vnoisegross.location = Vector((-70,-140))
    vnoisefine.location = Vector((-70,-440))
    math1.location = Vector((140,-140))
    math2.location = Vector((140,-440))

    vnoisegross.inputs[2].default_value = sstool.p_rgross/10
    vnoisefine.inputs[2].default_value = sstool.p_rfine/10
    math1.operation = 'MULTIPLY'
    math2.operation = 'MULTIPLY'
    math1.inputs[1].default_value = 2
    math2.inputs[1].default_value = 0.5
    
    matlinks.new(vnoisegross.outputs[0], math1.inputs[0])
    matlinks.new(vnoisefine.outputs[0], math2.inputs[0])
    matlinks.new(vmapseed.outputs[0], vnoisegross.inputs[0])

    mix3 = matnodes.new('ShaderNodeMixRGB')
    math3 = matnodes.new('ShaderNodeMath')
    math4 = matnodes.new('ShaderNodeMath')

    mix3.location = Vector((400,-140))
    math3.location = Vector((400,140))
    math4.location = Vector((640,-140))

    math3.operation = 'MULTIPLY'
    math4.operation = 'MULTIPLY'
    math3.inputs[1].default_value = 1.7
    math4.inputs[1].default_value = 1.2
    
    matlinks.new(mix2.outputs[0], math3.inputs[0])
    matlinks.new(mix3.outputs[0], math4.inputs[0])
    matlinks.new(math1.outputs[0], mix3.inputs[1])
    matlinks.new(math2.outputs[0], mix3.inputs[2])
    
    mix4 = matnodes.new('ShaderNodeMixRGB')
    mix4.name='finalmix'
    disp = matnodes.new('ShaderNodeDisplacement')
    
    mix4.location = Vector((900,220))
    disp.location = Vector((1100,220))
    
    mix4.blend_type = 'ADD'
    disp.space = 'OBJECT'
    disp.inputs[1].default_value = 0
    disp.inputs[2].default_value = sstool.p_height/10.0 #0.4
    
    #matlinks.new(rampmask.outputs[0], mix4.inputs[0])
    matlinks.new(mathero.outputs[0], mix4.inputs[0])
    matlinks.new(math3.outputs[0], mix4.inputs[1])
    matlinks.new(math4.outputs[0], mix4.inputs[2])
    matlinks.new(mix4.outputs[0], disp.inputs[0])
    matlinks.new(disp.outputs[0], matnodes['Material Output'].inputs[2])

    #colors
    ccood = matnodes.new('ShaderNodeTexCoord')
    csepxyz = matnodes.new('ShaderNodeSeparateXYZ')
    cramp = matnodes.new('ShaderNodeValToRGB')
    cinv = matnodes.new('ShaderNodeInvert')
    cnoise = matnodes.new('ShaderNodeTexNoise')
    cbump = matnodes.new('ShaderNodeBump')
    cramp.name = "Snow"
    
    ccood.location = Vector((-640,1060))
    csepxyz.location = Vector((-440,1060))
    cramp.location = Vector((-240,1060))
    cinv.location = Vector((340,1060))
    cnoise.location = Vector((340,940))
    cbump.location = Vector((540,940))

    cinv.inputs[0].default_value = 1
    cnoise.inputs[2].default_value = 4.6
    cnoise.inputs[3].default_value = 16
    cbump.inputs[0].default_value = 0.483
    cbump.inputs[1].default_value = 1

    cramp.color_ramp.interpolation = 'LINEAR'

    cramp.color_ramp.elements.new(0.432)
    cramp.color_ramp.elements.new(0.618)
    cramp.color_ramp.elements.new(0.682)
    
    cramp.color_ramp.elements[0].position = sstool.p_rock/100
    cramp.color_ramp.elements[1].position = 0.05 + sstool.p_snow/100
    cramp.color_ramp.elements[2].position = 0.10 + sstool.p_snow/100
    cramp.color_ramp.elements[3].position = 0.15 + sstool.p_snow/100
    
    cramp.color_ramp.elements[0].color = sstool.p_rockcolor
    cramp.color_ramp.elements[1].color = sstool.p_snowcolor1
    cramp.color_ramp.elements[2].color = sstool.p_snowcolor2
    cramp.color_ramp.elements[3].color = sstool.p_grasscolor2
    cramp.color_ramp.elements[4].color = sstool.p_grasscolor1

    matlinks.new(ccood.outputs[1], csepxyz.inputs[0])
    matlinks.new(csepxyz.outputs[2], cramp.inputs[0])
    matlinks.new(cramp.outputs[0], cinv.inputs[1])
    matlinks.new(cnoise.outputs[0], cbump.inputs[2])
    matlinks.new(cinv.outputs[0], matnodes['Principled BSDF'].inputs[7])
    matlinks.new(cramp.outputs[0], matnodes['Principled BSDF'].inputs[0])
    
    if bpy.app.version[1] > 90:
        matlinks.new(cbump.outputs[0], matnodes['Principled BSDF'].inputs[20])
    else:
        matlinks.new(cbump.outputs[0], matnodes['Principled BSDF'].inputs[19])
    
    matlinks.new(matnodes['Principled BSDF'].outputs[0], matnodes['Material Output'].inputs[0])


    return mat

##############################################################################################################


def createpeak(sstool):
    
    bpy.ops.mesh.primitive_plane_add(size=sstool.p_sz)
    bpy.ops.object.shade_smooth()
    bpy.context.object.name = "Blendpeak" + str(sstool.p_count)
    peakname = bpy.context.object.name #because name can change if exists already
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.subdivide(number_cuts=sstool.p_divs)
    bpy.ops.object.editmode_toggle()

    peak = bpy.data.objects.get(peakname)
    bpy.ops.object.material_slot_add()
    peak.data.materials[0] = creatematerial(sstool)
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.space_data.shading.type = 'RENDERED'

    sstool.p_count += 1
    
    return {'FINISHED'}

## Real time updates

def on_update_height(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["Displacement"].inputs[2].default_value = context.scene.bp_tool.p_height/10.0

def on_update_seed(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["NSeed"].inputs[1].default_value[0] = context.scene.bp_tool.p_seed/10.0
    bpy.context.object.data.materials[0].node_tree.nodes["VSeed"].inputs[1].default_value[1] = context.scene.bp_tool.p_seed/10.0

def on_update_gross(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["Gross"].inputs[2].default_value = context.scene.bp_tool.p_gross/10.0

def on_update_fine(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["Fine"].inputs[2].default_value = context.scene.bp_tool.p_fine/10.0

def on_update_rgross(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["RidgeGross"].inputs[2].default_value = context.scene.bp_tool.p_rgross/10.0

def on_update_rfine(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["RidgeFine"].inputs[2].default_value = context.scene.bp_tool.p_rfine/10.0

def on_update_ero(self, context):
    rampero = bpy.context.object.data.materials[0].node_tree.nodes["Ero"]
    val = context.scene.bp_tool.p_ero/100.0
    rampero.color_ramp.elements[0].position = val
    rampero.color_ramp.elements[1].position = 1-val

def on_update_eroscale(self, context):
    bpy.context.object.data.materials[0].node_tree.nodes["Eroscale"].inputs[2].default_value = context.scene.bp_tool.p_eroscale/10.0




def on_update_snow(self, context):
    cramp = bpy.context.object.data.materials[0].node_tree.nodes["Snow"]
    snow = context.scene.bp_tool.p_snow
    rock = context.scene.bp_tool.p_rock
    
    cramp.color_ramp.elements[0].position = rock/100
    cramp.color_ramp.elements[1].position = 0.05 + snow/100
    cramp.color_ramp.elements[2].position = 0.10 + snow/100
    cramp.color_ramp.elements[3].position = 0.15 + snow/100

def on_update_rock(self, context):
    cramp = bpy.context.object.data.materials[0].node_tree.nodes["Snow"]
    rock = context.scene.bp_tool.p_rock
    cramp.color_ramp.elements[0].position = rock/100
    
def on_update_scale(self, context):
    peak = bpy.context.view_layer.objects.active
    if peak == None:
        return
    pscale = context.scene.bp_tool.p_scale
    peak.scale = Vector((pscale, pscale, pscale))
    prock = context.scene.bp_tool.p_rock 
    if pscale>=1.0:
        context.scene.bp_tool.p_rock = 50.0/pscale
        context.scene.bp_tool.p_snow = 50.0/pscale
    else:
        context.scene.bp_tool.p_rock = 50.0*pscale
        context.scene.bp_tool.p_snow = 50.0*pscale

def on_update_colors(self, context):
    cramp = bpy.context.object.data.materials[0].node_tree.nodes["Snow"]
    cramp.color_ramp.elements[4].color = context.scene.bp_tool.p_grasscolor1
    cramp.color_ramp.elements[3].color = context.scene.bp_tool.p_grasscolor2
    cramp.color_ramp.elements[2].color = context.scene.bp_tool.p_snowcolor1
    cramp.color_ramp.elements[1].color = context.scene.bp_tool.p_snowcolor2
    cramp.color_ramp.elements[0].color = context.scene.bp_tool.p_rockcolor

def on_update_colors_rock(self, context):
    cramp = bpy.context.object.data.materials[0].node_tree.nodes["ColorRamp"]
    cramp.color_ramp.elements[1].color = context.scene.bp_tool.p_rockcolor1
    cramp.color_ramp.elements[0].color = context.scene.bp_tool.p_rockcolor2

def on_update_rockparam(self, context):
    t = context.scene.bp_tool
    n = bpy.context.object.data.materials[0].node_tree
    
    bpy.context.object.scale[2] = t.p_rockht
    
    n.nodes["Mapping"].inputs[1].default_value[0] = t.p_rockshape
    n.nodes["Noise Texture.001"].inputs[2].default_value = t.p_rockshapescale/10.0
    n.nodes["Displacement"].inputs[2].default_value = 20 - (t.p_rocksmooth/10.0)
    n.nodes["Noise Texture"].inputs[2].default_value = t.p_rockfine/100
    n.nodes["Noise Texture"].inputs[2].default_value = t.p_rockfinescale
    n.nodes["Mapping"].inputs[3].default_value[2] = t.p_rocklava
    

def randomizeall(sstool):
    sstool.p_height =  random.randrange(30, 60)/10
    sstool.p_seed = random.randrange(0, 100)
    sstool.p_gross = random.randrange(0, 50)
    sstool.p_fine = random.randrange(0, 200)
    sstool.p_rgross = random.randrange(0, 50)
    sstool.p_rfine = random.randrange(0, 200)
    sstool.p_snow = random.randrange(0, 70)
    sstool.p_rock = random.randrange(0, 70)    

def bakepeak(sstool):
    peakobj = bpy.context.view_layer.objects.active
    if peakobj == None:
        return 0
    
    mat = peakobj.active_material
    if mat == None:
        return 0
    
    mapsz = sstool.p_bakesz
    imgname = peakobj.name + "_Height_Bake"
    bpy.data.images.new(name=imgname, width = mapsz, height = mapsz, float_buffer=True)

    img = bpy.data.images[imgname]
    img.filepath = '//' + imgname + ".exr"

    n_image = len(bpy.data.images) - 1

    img.source = 'GENERATED'
    img.generated_type = 'BLANK'
    img.use_generated_float = True

    matnodes = mat.node_tree.nodes
    matlinks = mat.node_tree.links

    cmath = matnodes.new('ShaderNodeMath')
    cmath.operation = 'DIVIDE'
    cmath.inputs[1].default_value = 2

    cmath.location = 1100,440
    matlinks.new(matnodes['finalmix'].outputs[0], cmath.inputs[0])

    timage = matnodes.new('ShaderNodeTexImage')
    timage.location = 1100,-140
    timage.image = bpy.data.images[imgname]

    matlinks.new(cmath.outputs[0], matnodes['Material Output'].inputs[0])

    #remove disp link if present
    if len(matnodes['Material Output'].inputs[2].links) > 0:
        link = matnodes['Material Output'].inputs[2].links[0]
        mat.node_tree.links.remove(link)

    timage.select = True
    matnodes.active = timage

    bpy.ops.object.bake(type='COMBINED')

    img.file_format = 'OPEN_EXR'
    print(img.filepath)
    if img.filepath is None:
        return 1
    
    img.save()

    #switch to Eevee
    if sstool.p_toeevee:
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.space_data.shading.type = 'SOLID'

        bpy.ops.texture.new()
        l = len(bpy.data.textures)
        disptex = bpy.data.textures[l-1]
        disptex.image = bpy.data.images[imgname]
        bpy.ops.object.modifier_add(type='DISPLACE')
        mod = bpy.context.view_layer.objects.active.modifiers[0]
        mod.texture = disptex
        mod.mid_level = 0
    
    return 2

def createrock(sstool):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sstool.p_rockdiv, radius=sstool.p_rocksz, enter_editmode=False, location=(0, 0, 0))
    bpy.ops.object.shade_smooth()
    bpy.context.object.name = "Blendrock" + str(sstool.p_rcount)
    rockname = bpy.context.object.name #because name can change if exists already
    
    #height
    bpy.context.object.scale[2] = sstool.p_rockht
    
    mat = bpy.data.materials.new(name="NodeToScriptMat")
    mat.use_nodes = True
    matnodes = mat.node_tree.nodes
    matlinks = mat.node_tree.links

    bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'
    mat.cycles.displacement_method = 'BOTH'

    for n in matnodes:
        matnodes.remove(n)

    NoiseTexture = matnodes.new('ShaderNodeTexNoise')
    NoiseTexture001 = matnodes.new('ShaderNodeTexNoise')
    BrightContrast = matnodes.new('ShaderNodeBrightContrast')
    Math001 = matnodes.new('ShaderNodeMath')
    ColorRamp = matnodes.new('ShaderNodeValToRGB')
    Bump = matnodes.new('ShaderNodeBump')
    Mapping = matnodes.new('ShaderNodeMapping')
    PrincipledBSDF = matnodes.new('ShaderNodeBsdfPrincipled')
    Mix = matnodes.new('ShaderNodeMixRGB')
    Displacement = matnodes.new('ShaderNodeDisplacement')
    MaterialOutput = matnodes.new('ShaderNodeOutputMaterial')
    TextureCoordinate = matnodes.new('ShaderNodeTexCoord')


    NoiseTexture.location = Vector ((-113.9401, -15.4704))
    NoiseTexture001.location = Vector ((-207.2210, 250.1717))
    BrightContrast.location = Vector ((63.7708, -21.8994))
    Math001.location = Vector ((236.7996, -13.1770))
    ColorRamp.location = Vector ((73.8341, 607.8826))
    Bump.location = Vector ((94.9198, 351.3014))
    Mapping.location = Vector ((-394.1164, 253.8673))
    PrincipledBSDF.location = Vector ((428.0041, 730.4140))
    Mix.location = Vector ((424.8583, 109.6794))
    Displacement.location = Vector ((648.7039, 112.1413))
    MaterialOutput.location = Vector ((862.9899, 431.3890))
    TextureCoordinate.location = Vector ((-574.0769, 250.8262))

    #Links
    matlinks.new(Mapping.outputs['Vector'], NoiseTexture001.inputs['Vector'])
    matlinks.new(TextureCoordinate.outputs['Generated'], Mapping.inputs['Vector'])
    matlinks.new(Bump.outputs['Normal'], PrincipledBSDF.inputs['Normal'])
    matlinks.new(Displacement.outputs['Displacement'], MaterialOutput.inputs['Displacement'])
    matlinks.new(NoiseTexture001.outputs['Color'], Mix.inputs['Color1'])
    matlinks.new(Mix.outputs['Color'], Displacement.inputs['Normal'])
    matlinks.new(NoiseTexture.outputs['Fac'], BrightContrast.inputs['Color'])
    matlinks.new(ColorRamp.outputs['Color'], PrincipledBSDF.inputs['Base Color'])
    matlinks.new(NoiseTexture001.outputs['Fac'], Bump.inputs['Height'])
    matlinks.new(NoiseTexture001.outputs['Color'], ColorRamp.inputs['Fac'])
    matlinks.new(PrincipledBSDF.outputs['BSDF'], MaterialOutput.inputs['Surface'])
    matlinks.new(Math001.outputs['Value'], Mix.inputs['Color2'])
    matlinks.new(BrightContrast.outputs['Color'], Math001.inputs[0])

    #Values
    #shape
    Mapping.inputs['Location'].default_value = Vector((sstool.p_rockshape, 0.0000, 0.0000))
    Mapping.inputs['Rotation'].default_value = [0.0,0.0,0.0]
    Mapping.inputs['Scale'].default_value = Vector((1.0000, 1.0000, 1.0000))

    #shape scale
    NoiseTexture001.inputs['Scale'].default_value = sstool.p_rockshapescale/10
    NoiseTexture001.inputs['Detail'].default_value = 16.0
    NoiseTexture001.inputs['Distortion'].default_value = 0.0

    #smoothness
    Displacement.inputs['Height'].default_value = 1.0
    Displacement.inputs['Midlevel'].default_value = 0.0
    Displacement.inputs['Scale'].default_value = 20 - (sstool.p_rocksmooth/10.0)
    Displacement.inputs['Normal'].default_value = [0.0,0.0,0.0]

    #details
    Mix.inputs['Fac'].default_value = sstool.p_rockfine/100

    #details scale
    NoiseTexture.inputs['Scale'].default_value = sstool.p_rockfinescale
    NoiseTexture.inputs['Detail'].default_value = 16.0
    NoiseTexture.inputs['Distortion'].default_value = 0.0
    BrightContrast.inputs['Contrast'].default_value = 70
    
    #lava
    Mapping.inputs['Scale'].default_value = Vector((1.0000, 1.0000, sstool.p_rocklava))

    ColorRamp.inputs['Fac'].default_value = 0.5
    Bump.inputs['Strength'].default_value = 0.55
    Bump.inputs['Distance'].default_value = 2.0
    PrincipledBSDF.inputs['Roughness'].default_value = 0.65
    Math001.inputs[0].default_value = 0.5
    Math001.inputs[1].default_value = 1
    Math001.use_clamp = True
    Math001.operation = 'MULTIPLY'

    ColorRamp.color_ramp.elements[0].color = sstool.p_rockcolor2 #(0.012596523389220238,0.009892581030726433,0.007905444130301476,1.0)
    ColorRamp.color_ramp.elements[0].position = 0.0
    ColorRamp.color_ramp.elements[1].color = sstool.p_rockcolor1 #(0.03287532180547714,0.03428680822253227,0.02379169873893261,1.0)
    ColorRamp.color_ramp.elements[1].position = 0.6
    
    rock = bpy.data.objects.get(rockname)
    bpy.ops.object.material_slot_add()
    rock.data.materials[0] = mat
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.space_data.shading.type = 'RENDERED'

    sstool.p_rcount += 1

    return 1
    
#----------------------------------------------------------------------------------------
# Operators
#----------------------------------------------------------------------------------------

class CRD_OT_CResetPeakDefaults(bpy.types.Operator):
    bl_idname = "resetpeak.defaults"
    bl_label = "Reset Defaults"
    bl_description = "Reset Defaults."

    def execute(self, context):
        scene = context.scene
        sstool = scene.bp_tool
        
        sstool.p_divs = 100
        sstool.p_sz = 2
        sstool.p_height = 4
        sstool.p_seed = 10
        sstool.p_gross = 25
        sstool.p_fine = 80
        sstool.p_rgross = 75
        sstool.p_rfine = 120
        sstool.p_ero = 30
        sstool.p_eroscale = 30
        sstool.p_snow = 50
        sstool.p_rock = 50
        sstool.p_rand = False
        sstool.p_scale = 1
        
        sstool.p_rockht = 0.45
        sstool.p_rocksz = 1.0
        sstool.p_rockshape = 0
        sstool.p_rockshapescale = 15
        sstool.p_rocksmooth = 185
        sstool.p_rockfine = 12.5
        sstool.p_rockfinescale = 10
        sstool.p_rocklava = 0
        
        sstool.p_grasscolor1 = (0.048438, 0.040584, 0.007456, 1.0)
        sstool.p_grasscolor2 = (0.015930, 0.042520, 0.022400, 1.0)
        sstool.p_snowcolor1 = (0.5,0.5,0.45,1.0)
        sstool.p_snowcolor2 = (0.9,0.9,0.9,1.0)
        sstool.p_rockcolor = (0.008550, 0.006840, 0.006090, 1.0)
        sstool.p_rockcolor1 = (0.003213, 0.005759, 0.015993, 1)
        sstool.p_rockcolor2 = (0.147313, 0.075701, 0.040408, 1)

        if bpy.context.object is not None:
            try:
                cramp = bpy.context.object.data.materials[0].node_tree.nodes["Snow"]
                cramp.color_ramp.elements[0].color = (0.008550, 0.006840, 0.006090, 1.0)
                cramp.color_ramp.elements[1].color = (0.5,0.5,0.45,1.0)
                cramp.color_ramp.elements[2].color = (0.9,0.9,0.9,1.0)
                cramp.color_ramp.elements[3].color = (0.015930, 0.042520, 0.022400, 1.0)
                cramp.color_ramp.elements[4].color = (0.048438, 0.040584, 0.007456, 1.0)
            except:
                pass            
                    
        sstool.p_res = "Reset to defaults, except Divisions"
        return{'FINISHED'}  


class CCP_OT_CCreatePeak(bpy.types.Operator):
    bl_idname = "create.peak"
    bl_label = "Create Peak"
    bl_description = "Create Mountain Peak."

    def execute(self, context):
        scene = context.scene
        sstool = scene.bp_tool
        
        #prevents changing last peak
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
        
        if sstool.p_rand:
            
            randomizeall(sstool)
        
        createpeak(sstool)
        sstool.p_res = "Peak created !"
        return{'FINISHED'}

class CBP_OT_CBakePeak(bpy.types.Operator):
    bl_idname = "bake.peak"
    bl_label = "Bake Peak"
    bl_description = "Bake the height map."

    def execute(self, context):
        scene = context.scene
        sstool = scene.bp_tool
        
        res = bakepeak(sstool)
        if res==0 :
            ShowMessageBox("Please select a peak!")
        if res==1 :
            sstool.p_res = "Baked image could not be saved!"
            ShowMessageBox("Baked image could not be saved! Save it from Image Editor.")
            
        else:
            sstool.p_res = "Height Map Created and Saved!"
    
        return{'FINISHED'}

class CCR_OT_CCreateRock(bpy.types.Operator):
    bl_idname = "create.rock"
    bl_label = "Create Rock"
    bl_description = "Create a rock."

    def execute(self, context):
        scene = context.scene
        sstool = scene.bp_tool
        
        res = createrock(sstool)
        if res==0 :
            ShowMessageBox("Error: Could not create a rock!")
        else:
            sstool.p_res = "Rock created!"
    
        return{'FINISHED'}
        
#---------------------------------------------------------------------------------------------------------------------------
# Panels
#---------------------------------------------------------------------------------------------------------------------------
        

class OBJECT_PT_PeakPanel(bpy.types.Panel):

    bl_label = "Blendpeaks"
    bl_idname = "OBJECT_PT_PEAK_Panel"
    bl_category = "Blendpeaks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        sstool = scene.bp_tool
        
        layout.prop(sstool, "p_divs")
        #layout.prop(sstool, "p_sz")
        layout.prop(sstool, "p_rand")
        layout.operator("create.peak", text = "Create Peak", icon='HEART')
#        layout.prop(sstool, "p_adjust") 
        layout.prop(sstool, "p_height")
        layout.prop(sstool, "p_seed")
        layout.prop(sstool, "p_gross")
        layout.prop(sstool, "p_fine")
        layout.prop(sstool, "p_rgross")
        layout.prop(sstool, "p_rfine")
        layout.prop(sstool, "p_ero")
        layout.prop(sstool, "p_eroscale")
        
        layout.prop(sstool, "p_snow")
        layout.prop(sstool, "p_rock")
        layout.prop(sstool, "p_scale")
        row = layout.row(align=True)
        row.prop(sstool, "p_grasscolor1")
        row.prop(sstool, "p_grasscolor2")
        row.prop(sstool, "p_snowcolor1")
        row.prop(sstool, "p_snowcolor2")
        row.prop(sstool, "p_rockcolor")


class OBJECT_PT_MiscPeakPanel(bpy.types.Panel):

    bl_label = "Misc"
    bl_idname = "OBJECT_PT_MISCP_Panel"
    bl_category = "Blendpeaks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        sstool = scene.bp_tool
        
        layout.label(text = sstool.p_res)
        layout.operator("resetpeak.defaults", text = "Reset Defaults", icon='X')
        layout.operator("wm.url_open", text="Help | Source | Updates", icon='QUESTION').url = "https://github.com/oormicreations/Blendpeaks"
        layout.label(text = sstool.p_about)


class OBJECT_PT_BakePanel(bpy.types.Panel):

    bl_label = "Bake"
    bl_idname = "OBJECT_PT_BAKE_Panel"
    bl_category = "Blendpeaks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        sstool = scene.bp_tool
        
        #layout.label(text = sstool.p_res)
        layout.prop(sstool, "p_bakesz")
        layout.prop(sstool, "p_toeevee")
        layout.operator("bake.peak", text = "Bake Height Map", icon='OUTLINER_OB_IMAGE')


class OBJECT_PT_RockPanel(bpy.types.Panel):

    bl_label = "Rocks"
    bl_idname = "OBJECT_PT_ROCK_Panel"
    bl_category = "Blendpeaks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        sstool = scene.bp_tool
        
        layout.prop(sstool, "p_rockdiv")
        layout.prop(sstool, "p_rocksz")
        layout.prop(sstool, "p_rockht")
        layout.prop(sstool, "p_rockshape")
        layout.prop(sstool, "p_rockshapescale")
        layout.prop(sstool, "p_rocksmooth")
        layout.prop(sstool, "p_rockfine")
        layout.prop(sstool, "p_rockfinescale")
        layout.prop(sstool, "p_rocklava")
        #layout.prop(sstool, "p_rockcrack")
        #layout.prop(sstool, "p_rockcrackscale")
        #layout.prop(sstool, "p_rockcrackmix")
        row = layout.row(align=True)
        row.prop(sstool, "p_rockcolor1")
        row.prop(sstool, "p_rockcolor2")
        layout.operator("create.rock", text = "Create Rock", icon='MOD_FLUID')


      
#---------------------------------------------------------------------------------------------------
# Properties
#---------------------------------------------------------------------------------------------------

class CCProperties(PropertyGroup):

    p_count: IntProperty(
        name = "Count",
        description = "Index for naming, internal use only",
        default = 1,
      ) 
    p_rcount: IntProperty(
        name = "Rock Count",
        description = "Index for naming, internal use only",
        default = 1,
      ) 
          
    p_divs: IntProperty(
        name = "Divisions",
        description = "Number of Subdivisions, density of mesh",
        default = 200,
        min=1,
        max=2000        
      )   
      
    p_sz: FloatProperty(
        name = "Size",
        description = "Expanse of the landscape",
        default = 2,
        min=0.01,
        max=10000       
      )   

    p_scale: FloatProperty(
        name = "Scale",
        description = "Scales textures proportionately",
        default = 1,
        min=0.01,
        max=10,
        update=on_update_scale
      )   
      
    p_height: FloatProperty(
        name = "Height",
        description = "Height of the peak",
        default = 4.0,
        min=-100,
        max=1000,
        update=on_update_height
      )
      
    p_seed: FloatProperty(
        name = "Seed",
        description = "Randomized shape of the peak",
        default = 10.0,
        min=0,
        max=10000,
        update=on_update_seed
      )
      
    p_gross: FloatProperty(
        name = "Shape",
        description = "Gross shape of the peak",
        default = 25,
        min=0,
        max=10000,
        update=on_update_gross
      )

    p_fine: FloatProperty(
        name = "Shape Details",
        description = "Terrain finer details",
        default = 80,
        min=0,
        max=10000,
        update=on_update_fine
      )

    p_rgross: FloatProperty(
        name = "Ridges",
        description = "Sharp edges or ridges",
        default = 75,
        min=0,
        max=10000,
        update=on_update_rgross
      )

    p_rfine: FloatProperty(
        name = "Ridges Detail",
        description = "Finer ridges",
        default = 120,
        min=0,
        max=10000,
        update=on_update_rfine
      )

    p_ero: FloatProperty(
        name = "Erosion",
        description = "Erodes the terrain",
        default = 30,
        min=0,
        max=100,
        update=on_update_ero
      )
    
    p_eroscale: FloatProperty(
        name = "Erosion Scale",
        description = "Scale of erosion",
        default = 30,
        min=0,
        max=1000,
        update=on_update_eroscale
      )

    p_snow: FloatProperty(
        name = "Snow",
        description = "Amount of snow",
        default = 50,
        min=0,
        max=100,
        update=on_update_snow
      )

    p_rock: FloatProperty(
        name = "Rock",
        description = "Amount of rock",
        default = 50,
        min=0,
        max=100,
        update=on_update_rock
      )
    
    p_rand: BoolProperty(
        name = "Randomize",
        description = "Ignores the settings and creates a random peak",
        default = False
    )

#    p_adjust: BoolProperty(
#        name = "Adjust",
#        description = "Adjust the settings of an existing peak",
#        default = False
#    )
      
    p_res: StringProperty(
        name = "Result",
        description = "NA",
        default = "Ready..."
      )

    p_about: StringProperty(
        name = "About",
        description = "NA",
        default = "Oormi Creations | http://oormi.in"
      )

    p_bakesz: IntProperty(
        name = "Size",
        description = "Size in pixels of the image.",
        default = 1024,
        min=16,
        max=100000        
      ) 
      
    p_toeevee: BoolProperty(
        name = "Switch to Eevee",
        description = "Change renderer to Eevee",
        default = True
    )

    p_grasscolor1: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.048438, 0.040584, 0.007456, 1.0),
         update=on_update_colors
     )

    p_grasscolor2: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.015930, 0.042520, 0.022400, 1.0),
         update=on_update_colors
     )
          
    p_snowcolor1: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.5,0.5,0.45,1.0),
         update=on_update_colors
     )

    p_snowcolor2: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.9,0.9,0.9,1.0),
         update=on_update_colors
     )
     
    p_rockcolor: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.008550, 0.006840, 0.006090, 1.0),
         update=on_update_colors
     )   

    p_rockdiv: IntProperty(
        name = "Divisions",
        description = "Mesh density.",
        default = 5,
        min=1,
        max=10        
      ) 
    p_rocksz: FloatProperty(
        name = "Size",
        description = "Radius of the rock.",
        default = 1,
        min=0.00001,
        max=100000        
      ) 
    p_rockht: FloatProperty(
        name = "Height",
        description = "Z scale of the rock.",
        default = 0.4,
        min=0.00001,
        max=50,
        update=on_update_rockparam
      ) 

    p_rockshape: FloatProperty(
        name = "Shape",
        description = "Overall shape of the rock.",
        default = 1,
        min=0.00001,
        max=100000,
        update=on_update_rockparam
      ) 
    p_rockshapescale: FloatProperty(
        name = "Shape Scale",
        description = "Scale of the overall shape.",
        default = 15,
        min=0.00001,
        max=50,
        update=on_update_rockparam
      ) 
    p_rocksmooth: FloatProperty(
        name = "Smoothness",
        description = "Smoothness of the rock.",
        default = 185,
        min=0.0,
        max=200,
        update=on_update_rockparam
      ) 
      
    p_rockfine: FloatProperty(
        name = "Details",
        description = "Detailed features of the rock.",
        default = 0.125,
        min=0.00001,
        max=100,
        update=on_update_rockparam
      ) 
    p_rockfinescale: FloatProperty(
        name = "Details Scale",
        description = "Scale of the detailed features.",
        default = 10,
        min=0.00001,
        max=100,
        update=on_update_rockparam
      ) 
    p_rocklava: FloatProperty(
        name = "Lava",
        description = "Frozen lava rock.",
        default = 0,
        min=0.0000,
        max=100000,
        update=on_update_rockparam        
      ) 

    p_rockcrack: FloatProperty(
        name = "Cracks",
        description = "Cracks in the rock.",
        default = 1,
        min=0.0,
        max=100000,
        update=on_update_rockparam
      ) 
    p_rockcrackscale: FloatProperty(
        name = "Cracks Scale",
        description = "Scale of the cracks.",
        default = 9,
        min=0.0,
        max=100,
        update=on_update_rockparam
      ) 
    p_rockcrackmix: FloatProperty(
        name = "Crack Intensity",
        description = "Intensity of the cracks in the rock.",
        default = 1.0,
        min=0.0,
        max=10,
        update=on_update_rockparam   
      ) 

    p_rockcolor1: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.003213, 0.005759, 0.015993, 1), #(0.103585, 0.074843, 0.060272, 1),
         update=on_update_colors_rock
     )   
    p_rockcolor2: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.147313, 0.075701, 0.040408, 1), #(0.0, 0.0, 0.0, 1.0),
         update=on_update_colors_rock
     )   


 
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_PeakPanel,
    OBJECT_PT_BakePanel,
    OBJECT_PT_RockPanel,
    OBJECT_PT_MiscPeakPanel,
    CCProperties,
    CCP_OT_CCreatePeak,
    CRD_OT_CResetPeakDefaults,
    CBP_OT_CBakePeak,
    CCR_OT_CCreateRock
)

def register():
    bl_info['blender'] = getattr(bpy.app, "version")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.bp_tool = PointerProperty(type=CCProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.bp_tool



if __name__ == "__main__":
    register()
