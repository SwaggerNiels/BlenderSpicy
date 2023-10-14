import bpy

# ----------------------- NEURON BUILDER UI -----------------------

class BLENDERSPICY_PT_NeuronBuilder(bpy.types.Panel):
    
    bl_label =  'Neuron Builder'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderSpicy"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.blenderspicy_neuronbuild
        col = layout.column()
        col.prop(props, "filepath")
        col.label(text="Coordinates", icon="GRID")
        col.prop(props, "center_at_origin")
        col.prop(props, "downscale_factor")

        col.separator()
        col.label(text="Morphology", icon="MESH_UVSPHERE")
        col.prop(props, "segmentation")
        col.prop(props, "branch_base_thickness")
        col.prop(props, "branch_thickness_homogeneity")
        col.prop(props, "simplify_soma")
        col.prop(props, "with_caps")
        
    

        row = layout.row()
        row.operator("blenderspicy.build_neuron")

# ----------------------- GRAPH MANAGER UI ------------------------

class BLENDERSPICY_PT_GraphBuilder(bpy.types.Panel):
    
    bl_label =  'Graph builder'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderSpicy"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.blenderspicy_graphbuild
        
        # col.label(text="Paths", icon='FILE_TICK')
        # col.prop(props, "filepath")
        #Mode specific UI (matplotlib textures or Blender native)
        # row = layout.row()
        # row.prop(props, "plot_mode", expand=True)
        

        # Create an inset for the lower section
        # if props.plot_mode == 'MPL':
        #     col.prop(props, "animation_folder")
        # elif props.plot_mode == 'Native':
        #     col.prop(props, "animate")
            
        col = layout.column(align=True)
        col.operator("blenderspicy.build_graph", icon='GRAPH')
        row = col.row(align=True)
        row.scale_x = 1.5
        row.prop(props, "line_width")
        row.scale_x = .5
        row.prop(props, "graph_color")
        col.prop(props, "t_scalar")
        col.prop(props, "v_scalar")
        
        col = layout.column(align=True)
        if props.scale_bars:
            col.operator("blenderspicy.remove_scalebar", icon='FIXED_SIZE')
        else:
            col.operator("blenderspicy.build_scalebar", icon='FIXED_SIZE')
        row = col.row(align=True)
        row.scale_x = 1.5
        row.prop(props, "scale_width")
        row.scale_x = .5
        row.prop(props, "scale_color")
        col.prop(props, "t_bar_magnitude")
        col.prop(props, "v_bar_magnitude")
            
        col = layout.column(align=True)
        if props.ref_lines:
            col.operator("blenderspicy.remove_reference", icon='LINENUMBERS_OFF')
        else:
            col.operator("blenderspicy.build_reference", icon='LINENUMBERS_OFF')
        row = col.row(align=True)
        row.scale_x = 1.5
        row.prop(props, "ref_width")
        row.scale_x = .5
        row.prop(props, "ref_color")
        col.prop(props, "ref_height")
        
        col = layout.column(align=True)
        if props.sg_curves:
            col.operator("blenderspicy.remove_sgcurve", icon='IPO_LINEAR')
        else:
            col.operator("blenderspicy.build_sgcurve", icon='IPO_LINEAR')
        row = col.row(align=True)
        row.scale_x = 1.5
        row.prop(props, "sg_width")
        row.scale_x = .5
        row.prop(props, "sg_color")
        col.prop(props, "sg_thick")
        
        # List of generated graphs with delete buttons
        row = layout.row(align=True)
        col = layout.row(align=True)
        row.label(text="graphs made:")
        box = layout.box()
        col = box.column()
        items = props.graphs
        for i, item in enumerate(items):
            row = col.row(align=True)
            row.label(text=item.name)
            row.operator("blenderspicy.delete_item", icon='TRASH', text='', emboss=False).index = i

# ----------------------- ANIMATION MANAGER UI --------------------

class BLENDERSPICY_PT_AnimationManager(bpy.types.Panel):
    bl_label = 'Animation manager'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderSpicy"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.operator("blenderspicy.reload_animations") 

        row = layout.row()
        row.operator("blenderspicy.remove_handlers")

# ----------------------- SHADING UI ------------------------------

class BLENDERSPICY_PT_MaterialCreator(bpy.types.Panel):
    bl_label = 'Shading manager'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderSpicy"
    
    def draw(self, context):
        layout = self.layout
        
        props = context.scene.blenderspicy_materials
        col = layout.column()
        col.prop(props, "min_value")
        col.prop(props, "max_value")
        col.prop(props, "colormap")
        col.prop(props, "cmap_start")
        col.prop(props, "cmap_end")
        col.prop(props, "colormap_steps")
        col.prop(props, "emission_strength")
        


        row = layout.row()
        row.operator("blenderspicy.create_material")
        col = layout.column()
        col.operator("blenderspicy.remove_materials")
        col.operator("blenderspicy.setup_world")
