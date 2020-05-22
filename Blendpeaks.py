# Blendpeaks by oormi creations
# A free and open source add-on for Blender
# Creates mountain peaks with a procedural material.
# http://oormi.in


bl_info = {
    "name": "Blendpeaks",
    "description": "Creates Mountain Peaks",
    "author": "Oormi Creations",
    "version": (0, 1, 0),
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
    disp = matnodes.new('ShaderNodeDisplacement')
    
    mix4.location = Vector((900,220))
    disp.location = Vector((1100,220))
    
    mix4.blend_type = 'ADD'
    disp.space = 'OBJECT'
    disp.inputs[1].default_value = 0
    disp.inputs[2].default_value = sstool.p_height/10.0 #0.4
    
    matlinks.new(rampmask.outputs[0], mix4.inputs[0])
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
    
    ccood.location = Vector((-640,860))
    csepxyz.location = Vector((-440,860))
    cramp.location = Vector((-240,860))
    cinv.location = Vector((340,860))
    cnoise.location = Vector((340,740))
    cbump.location = Vector((540,740))

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
    
    cramp.color_ramp.elements[0].color = (0.00855, 0.00684, 0.00609, 1)
    cramp.color_ramp.elements[1].color = (0.504276, 0.503419, 0.503045, 1)
    cramp.color_ramp.elements[2].color = (1, 1, 1, 1)
    cramp.color_ramp.elements[3].color = (0.01593, 0.04252, 0.0224, 1)
    cramp.color_ramp.elements[4].color = (0.02642, 0.04844, 0.017, 1)

    matlinks.new(ccood.outputs[1], csepxyz.inputs[0])
    matlinks.new(csepxyz.outputs[2], cramp.inputs[0])
    matlinks.new(cramp.outputs[0], cinv.inputs[1])
    matlinks.new(cnoise.outputs[0], cbump.inputs[2])
    matlinks.new(cinv.outputs[0], matnodes['Principled BSDF'].inputs[7])
    matlinks.new(cramp.outputs[0], matnodes['Principled BSDF'].inputs[0])
    matlinks.new(cbump.outputs[0], matnodes['Principled BSDF'].inputs[19])
    matlinks.new(matnodes['Principled BSDF'].outputs[0], matnodes['Material Output'].inputs[0])


    return mat

##############################################################################################################


def createpeak(sstool):
    
    bpy.ops.mesh.primitive_plane_add(size=2)
    bpy.ops.object.shade_smooth()
    bpy.context.object.name = "Blendpeak.001"
    peakname = bpy.context.object.name #because name can change if exists already
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.subdivide(number_cuts=sstool.p_divs)
    bpy.ops.object.editmode_toggle()

    peak = bpy.data.objects.get(peakname)
    bpy.ops.object.material_slot_add()
    peak.data.materials[0] = creatematerial(sstool)
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.space_data.shading.type = 'RENDERED'
    
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

def randomizeall(sstool):
    sstool.p_height =  random.randrange(30, 60)/10
    sstool.p_seed = random.randrange(0, 100)
    sstool.p_gross = random.randrange(0, 50)
    sstool.p_fine = random.randrange(0, 200)
    sstool.p_rgross = random.randrange(0, 50)
    sstool.p_rfine = random.randrange(0, 200)
    sstool.p_snow = random.randrange(0, 70)
    sstool.p_rock = random.randrange(0, 70)    
    
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
        sstool.p_height = 4
        sstool.p_seed = 3
        sstool.p_gross = 25
        sstool.p_fine = 80
        sstool.p_rgross = 75
        sstool.p_rfine = 120
        sstool.p_snow = 50
        sstool.p_rock = 50
        sstool.p_rand = False
        
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
        layout.prop(sstool, "p_rand")
        layout.operator("create.peak", text = "Create Peak", icon='HEART')
#        layout.prop(sstool, "p_adjust") 
        layout.prop(sstool, "p_height")
        layout.prop(sstool, "p_seed")
        layout.prop(sstool, "p_gross")
        layout.prop(sstool, "p_fine")
        layout.prop(sstool, "p_rgross")
        layout.prop(sstool, "p_rfine")
        layout.prop(sstool, "p_snow")
        layout.prop(sstool, "p_rock")


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
      
#---------------------------------------------------------------------------------------------------
# Properties
#---------------------------------------------------------------------------------------------------

class CCProperties(PropertyGroup):
    
    p_divs: IntProperty(
        name = "Divisions",
        description = "Number of Subdivisions, density of mesh",
        default = 100,
        min=1,
        max=1000        
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
        default = 3.0,
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




    
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_PeakPanel,
    OBJECT_PT_MiscPeakPanel,
    CCProperties,
    CCP_OT_CCreatePeak,
    CRD_OT_CResetPeakDefaults
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
    del bpy.types.Scene.ss_tool



if __name__ == "__main__":
    register()
