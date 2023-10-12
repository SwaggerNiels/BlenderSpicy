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
        
        col = layout.column()
        # col.label(text="Paths", icon='FILE_TICK')
        # col.prop(props, "filepath")
        
        col = layout.column()
        col.label(text="Graphs", icon='GRAPH')
        
        #Mode specific UI (matplotlib textures or Blender native)
        row = layout.row()
        row.prop(props, "plot_mode", expand=True)
        
        box = layout.box()
        box.label(text="properties")

        # Create an inset for the lower section
        if props.plot_mode == 'MPL':
            box.prop(props, "animation_folder")
        elif props.plot_mode == 'Native':
            box.prop(props, "animate")
            
        row = box.row(align=True)
        row.prop(props, "line_width")
        row.prop(props, "graph_color")
        
        row = box.row(align=True)
        row.prop(props, "vt_bars_option")
        row.prop(props, "t_bar_magnitude")
        row.prop(props, "v_bar_magnitude")
        
        row = box.row(align=True)
        row.prop(props, "t_scalar")
        row.prop(props, "v_scalar")
            
        row = layout.row(align=True)
        row.scale_x = 1
        row.scale_y = 1.2
        row.alignment = 'CENTER'
        row.operator("blenderspicy.build_graph", icon='IMAGE_PLANE')
        row.separator()
        
        # List of generated graphs with delete buttons
        items = props.graphs
        for i, item in enumerate(items):
            row = layout.row()
            row.alignment = "RIGHT"
            
            row.label(text=item.name)
            row.operator("blenderspicy.delete_item", icon='TRASH', text='', emboss=False).index = i
            row.separator()

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
