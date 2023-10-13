import bpy
import numpy as np
import matplotlib.pyplot as plt
import os
from mathutils import Matrix #for shifting origin of graphs

from .utils import ShowMessageBox as out
from .utils import set_material_to_object, set_material_color
from .utils import remove_curve
import shutil

SCALE = (.01, 1)

## ------------------------------ Section Graph container -----------------------------------

class SectionGraph():
    '''
        Container class for storing a graph object from the data in in BlenderSection
    '''
    
    def __init__(self,
                 filepath,
                 animation_folder = 'anims',
                 ):
        self.filepath = filepath
        self.animation_folder = animation_folder
        self.mat = None
        
        self.SCALE = SCALE
        self.CREATE_ON_SECTION_TIP = True
        
        self.data_from = 'voltage_array'
        # self.sections_dicts = load_sections_dicts(self.filepath) # Loading sections dictionary

        self.parent_section = bpy.context.selected_objects[0]
        self.name = f'graph_{self.parent_section.name}'
        
        self.ob = None
        self.plot_type = None
        self.build_graph() #sets self.ob
        self.create_curve_to_section()
        
        # move object to tip of segment
        if self.CREATE_ON_SECTION_TIP:
            empty_loc = self.parent_section.parent.location
            vi = np.argmax([(v.co - empty_loc).length for v in self.parent_section.data.vertices])
            self.ob.location = self.parent_section.data.vertices[vi].co
    
    def create_curve_to_section(self):  
        ''' Create a bezier curve from the graph to the NEURON section: sg object'''

        print("Creating curve to section")        
        name = f'sg_{self.parent_section.name}'

        curve = bpy.data.curves.new('curve_' + name, 'CURVE')
        spline = curve.splines.new('BEZIER')
        obj = bpy.data.objects.new(name, curve)

        spline.bezier_points.add(1)

        empty_loc = self.parent_section.parent.location
        
        #hook to furthest edge of section
        i=0
        p = spline.bezier_points[i]
        vi = np.argmax([(v.co - empty_loc).length for v in self.parent_section.data.vertices])
        p.co = self.parent_section.data.vertices[vi].co
        p.handle_right_type = 'AUTO'
        p.handle_left_type = 'AUTO'
        h = obj.modifiers.new(self.parent_section.name, 'HOOK')
        h.object = self.parent_section
        h.vertex_indices_set([a + i*3 for a in range(3)])
        
        #hook to graph origin
        i=1
        p = spline.bezier_points[i]
        p.co = self.ob.location
        p.handle_right_type = 'AUTO'
        p.handle_left_type = 'AUTO'
        h = obj.modifiers.new(self.ob.name, 'HOOK')
        h.object = self.ob
        h.vertex_indices_set([a + i*3 for a in range(3)])
        
        obj.data.bevel_depth = 0.02
        bpy.context.scene.collection.objects.link(obj)
        
        #make material for curve if needed and assign it
        sg_name = 'sg_' + self.parent_section.name
        mat_sg_name = 'mat_sg_' + self.parent_section.name
        
        # set the material for the graph object and change the color
        color = bpy.context.scene.blenderspicy_graphbuild.graph_color
        mat_sg,_ = set_material_to_object(sg_name, mat_sg_name)
        set_material_color(mat_sg_name, color)
         
    def _load_voltage_data(self):
        
        if self.data_from == 'sections dict':
            section_type,section_id = self.parent_section.name.split('_')
            section_id = int(section_id)

            filtered_data = [entry for entry in self.sections_dicts if 
                            entry['type'] == section_type and 
                            entry['ID'] == section_id]
            
            data = filtered_data[0]['Voltage']
            voltage_data = np.array([np.mean(data[vals]) for vals in data])
            
            
        elif self.data_from == 'parent section by frame':
            #extract data from parent_section for every frame and take mean
            voltage_data = []
            current_frame = bpy.context.scene.frame_current
            bpy.context.scene.render.use_lock_interface = True # This is to ensure render doesn't crash
            for f in range(bpy.context.scene.frame_end):
                bpy.context.scene.frame_set(f)
                
                voltage = self.parent_section.data.attributes['Voltage']
                n = len(voltage.data)
                vals = [0.] * n
                voltage.data.foreach_get("value", vals)
                
                voltage_data.append(np.mean(vals))
            bpy.context.scene.frame_set(current_frame)
            
        #### Probably the best method ####
        elif self.data_from == 'voltage_array':
            voltage_data = self.parent_section.parent['voltage_array'][self.parent_section['ID']]
        
        return(voltage_data)
    
    def build_graph(self):
        voltage_data = self._load_voltage_data()
        plot_mode = bpy.context.scene.blenderspicy_graphbuild.plot_mode
        animate = bpy.context.scene.blenderspicy_graphbuild.animate
        
        self.plot_mode = plot_mode
        
        if   plot_mode == 'MPL':
            self.ob = self._build_MPL_graph(
                voltage_data,
                self.animation_folder,
                self.parent_section.name
                )
            
        elif plot_mode == 'Native':
            if not animate:
                self.ob = self._native_line(
                    voltage_data,
                    'static',
                )
            elif animate:
                self.ob = self._native_line(
                    voltage_data,
                    'animate',
                )
            
        self.ob['plot_mode'] = plot_mode
        bpy.ops.object.select_all(action='DESELECT')
        self.ob.select_set(True)

    def _build_MPL_graph(self,
                         data, 
                         folder,
                         name, 
                         ):
        # open pickle file and process to plots
        folder_path = f'{folder}{name}'
        self._make_separate_plots(folder_path,data)
        
        files = [{"name": 'f', "name": f} 
                 for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
         
        bpy.ops.import_image.to_plane(files=files, 
                                      directory=folder_path, 
                                      image_sequence=True, 
                                      relative=False)
        graph = bpy.context.selected_objects[0]
        graph.name = f'graph_{name}'
        
        #set origin to lower left
        me = graph.data
        mw = graph.matrix_world
        origin = me.vertices[0].co#sum((v.co for v in me.vertices), Vector()) / len(me.vertices)

        T = Matrix.Translation(-origin)
        me.transform(T)
        mw.translation = mw @ origin
        
        # set material
        mat = graph.active_material
        mat.name = f'mat_{name}'
        mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
        mat.node_tree.links.remove(mat.node_tree.nodes["Image Texture"].outputs[0].links[0])
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = bpy.context.scene.blenderspicy_graphbuild.graph_color
        
        return(graph)
    
    def _check_data_dimensionality(self,):
        pass
    
    def _make_separate_plots(self,
                            folder_path,
                            voltage_data : np.array,
                            colval=1,
                            coldivs=10,
                            lw=6,
                            dpi=50,
                            zero_start=True
                            ):
        fig = plt.figure(dpi=dpi,frameon=False)
        ax = fig.add_axes([0,0,1,1])
        plt.axis('off')
        plt.margins(x=0.01)
        plt.margins(y=0.01)
        
        # voltage plot
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            images_name = bpy.path.display_name_from_filepath(folder_path)

            if zero_start:
                y = np.array([np.min(voltage_data)] + list(voltage_data))
            else:
                y = voltage_data
            x = np.array(range(y.size), dtype=int)
            
            line, = plt.plot([], [], lw=lw)

            def _save_frames(i):
                line.set_data(x[:i], y[:i])
                filename = folder_path + f'/{images_name}_{i:04d}.png'
                plt.savefig(filename, transparent=True)
                
                return line,

            #first plot last for dimesions of axis
            line.set_data(x, y)
            ax.add_line(line)
            
            #plot all frames and save them
            frames = range(1,x.size) if zero_start else range(x.size)
            for i in frames:
                _save_frames(i)
        else:
            print('Graph animation already generated')
            pass
    
    def _native_line(self, data, plot_type='static', name="object_name", z=0):
        '''
            Creates a curve as a line plot from the input data
        '''
        name = self.name
        props = bpy.context.scene.blenderspicy_graphbuild
        
        xs = np.array( list(range(len(data))) ) * self.SCALE[0] * props.t_scalar
        
        ymin = bpy.context.scene.blenderspicy_materials.min_value
        ymax = bpy.context.scene.blenderspicy_materials.max_value
        ys = np.clip(data,ymin,ymax)
        ys = (np.array(ys)-np.min(ys)) * self.SCALE[1] * props.v_scalar
        
        data = zip(xs,ys)
        
        if   plot_type == 'static':
            obj = self._plot_line_static(data, name, z)
            
        elif plot_type == 'animate':
            obj = self._plot_line_animate(data, name, z)
            
        obj.data.bevel_depth = props.line_width
        obj.data.use_fill_caps = True
        
        graph_name = self.name
        mat_name = 'mat_' + self.parent_section.name
        
        # set the material for the graph object and change the color
        color = props.graph_color
        mat,_ = set_material_to_object(graph_name, mat_name)
        set_material_color(mat_name, color)
        
        return(obj)
    
    def _curve_spline_line(self, data, z=0):
        points = [[x,y,z] for (x,y) in data]
        
        # make a new curve with a new spline
        curve = bpy.data.curves.new('curve_' + self.name, 'CURVE')
        curve.dimensions = '3D'
        spline = curve.splines.new(type='POLY')
        spline.points.add(len(points)-1) # theres already one point by default
        
        for p, new_co in zip(spline.points, points):
            p.co = (new_co + [1.0]) # add nurbs weight
        
        return(curve,spline)
    
    def _plot_line_static(self, data, name="object_name", z=0):
        
        curve,_ = self._curve_spline_line(data,z)
        
        # make a new object with the curve
        obj = bpy.data.objects.new(name, curve)
        bpy.context.scene.collection.objects.link(obj)
        
        return(obj)
        
    def _plot_line_animate(self, data, name="object_name", z=0):
        
        curve,spline = self._curve_spline_line(data,z)
                
        # make a new object with the curve
        obj = bpy.data.objects.new(name, curve)
        bpy.context.scene.collection.objects.link(obj)

        for f,point in enumerate(spline.points):
            point.radius = 0
            point.keyframe_insert(data_path="radius", frame = f)
            point.radius = 1
            point.keyframe_insert(data_path="radius", frame = f+1)
            
        # obj.data.bevel_factor_end = 0
        # obj.data.keyframe_insert(data_path="bevel_factor_end", frame = 1)
        # obj.data.bevel_factor_end = 1
        # number_of_points = len(obj.data.splines[0].points)
        # obj.data.keyframe_insert(data_path="bevel_factor_end", frame = number_of_points)
        
        return(obj)
        
    def _plot_2Dt_line(points_2Dt, name="object_name", z=0):
        return NotImplementedError
        
        points_3Dt = [[[point[0],point[1],Z] for point in points_2D] for points_2D in points_2Dt]
        
        # make a new curve
        crv = bpy.data.curves.new('crv', 'CURVE')
        crv.dimensions = '3D'

        # make a new spline in that curve
        spline = crv.splines.new(type='POLY')

        # a spline point for each point
        spline.points.add(len(points_3Dt[0])-1) # theres already one point by default
        print(len(points_3Dt[0]))
        
        for i, points_3D in enumerate(points_3Dt):
            print(len(points_3D))
            for p, new_co in zip(spline.points, points_3D):
                p.co = (new_co + [1.0]) # (add nurbs weight)
            for point in spline.points:
                point.keyframe_insert(data_path="co", frame = i)

        # make a new object with the curve
        obj = bpy.data.objects.new(name, crv)
        obj.data.bevel_depth = .2
        obj.data.use_fill_caps = True
        bpy.context.scene.collection.objects.link(obj)
        
    def plot_2Dscatter(points_2D, name="object_name", z=0):
        points_3D = [[point[0],point[1],Z] for point in points_2D]
        
        ico = bpy.data.meshes.new('ICOSPHERE')
        
        for point in points_3D:
            # make a new object with the curve
            obj = bpy.data.objects.new(name, ico)
    #        obj.data.diameter = 1
            bpy.context.scene.collection.objects.link(obj)

# Callback functions
def update_native_graph(property: str, value: str):
    
    def func(self, context):
        props = context.scene.blenderspicy_graphbuild
        for graph in props.graphs:
            obj = bpy.data.objects['graph_' + graph.name]
            setattr(obj.data, property, getattr(props, value))
            
    return(func)

def update_sg_curve(property: str, value: str):
    
    def func(self, context):
        props = context.scene.blenderspicy_graphbuild
        for graph in props.graphs:
            obj = bpy.data.objects['curve_' + graph.name]
            setattr(obj.data, property, getattr(props, value))
            
    return(func)

def update_line_width(self, context):
    update_graphs = update_native_graph('bevel_depth','line_width')
    update_graphs(self,context)
    
    update_vt_bars(self, context)

def update_scale(self,context):
    props = context.scene.blenderspicy_graphbuild
    
    x = props.t_scalar
    y = props.v_scalar
    
    xp,yp = props.graph_scale
        
    matrixp = Matrix.Scale(1/xp, 4, (1.0, 0.0, 0.0)) @ Matrix.Scale(1/yp, 4, (0.0, 1.0, 0.0))
    matrix  = Matrix.Scale(x   , 4, (1.0, 0.0, 0.0)) @ Matrix.Scale(y   , 4, (0.0, 1.0, 0.0))
    
    for graph in props.graphs:
        obj = bpy.data.curves['curve_graph_' + graph.name]
        
        obj.transform(matrixp)
        obj.transform(matrix)
        
        for p in obj.splines[0].points:
            p.radius = 1
    
    props.graph_scale[0] = x
    props.graph_scale[1] = y
    
    if props.vt_bars_option:
        update_vt_bars(self,context)

def update_vt_bars_option(self, context):
    voltage_bar_name = 'voltage_scale_bar'
    time_bar_name = 'time_scale_bar'
    props = context.scene.blenderspicy_graphbuild
    
    bpy.ops.object.select_all(action='DESELECT')    
    if self.vt_bars_option:
        #add scale bars
        for bar in [voltage_bar_name,time_bar_name]:
            curve = bpy.data.curves.new('curve_' + bar, 'CURVE')
            spline = curve.splines.new('BEZIER')
            obj = bpy.data.objects.new(bar, curve)
            
            text_curve = bpy.data.curves.new(type="FONT", name="text_curve_" + bar)
            obj.data.bevel_depth = props.line_width*2
            
            x1,y1 = (0,0)
            
            if bar == voltage_bar_name:
                x2,y2 = (0,props.v_bar_magnitude*SCALE[1]*props.v_scalar)
                
                text_curve.body = f"{props.v_bar_magnitude} mV"
                text_curve.align_x = 'RIGHT'
                text_curve.align_y = 'CENTER'
                text_curve.offset_x = -props.line_width*2
                text_curve.offset_y = y2/2
            
            elif bar == time_bar_name:
                x2,y2 = (props.t_bar_magnitude*SCALE[0]*props.t_scalar,0)
                
                text_curve.body = f"{props.t_bar_magnitude} ms"
                text_curve.align_x = 'CENTER'
                text_curve.align_y = 'TOP'
                text_curve.offset_x = x2/2-.5
                text_curve.offset_y = -props.line_width*2
                
            spline.bezier_points.add(1)
            spline.bezier_points[0].co = (x1,y1, 0)
            spline.bezier_points[1].co = (x2,y2, 0)
            
            bpy.context.scene.collection.objects.link(obj)
            obj.select_set(True)
            
            text_obj = bpy.data.objects.new(name='text_' + bar, object_data=text_curve)
            bpy.context.scene.collection.objects.link(text_obj)
            text_obj.parent = obj
            text_obj.select_set(True)
            
    elif not self.vt_bars_option:
        #destroy scale bars
        remove_curve(voltage_bar_name)
        remove_curve(time_bar_name)

def update_object_data(obj_name: str, property: str, value: str, callback=None):
    func = None
    
    if callback!=None:
        if not callable(callback):
            raise ValueError("func2 must be a callable function")
        
        def func(self, context):
            props = context.scene.blenderspicy_graphbuild
            prop = getattr(props, property)
            obj = bpy.data.objects[obj_name]
            setattr(obj.data, prop, getattr(prop, value))
        
        callback()
    else:
        
        def func(self, context):
            props = context.scene.blenderspicy_graphbuild
            prop = getattr(props, property)
            obj = bpy.data.objects[obj_name]
            setattr(obj.data, prop, getattr(prop, value))
        
    return(func)

def update_vt_bars(self, context):
    props = context.scene.blenderspicy_graphbuild
    
    props.vt_bars_option = False
    props.vt_bars_option = True

def update_graph_color(self, context):
    '''This function will be called when the graph_color property changes'''
    # You can access the updated value with self.graph_color
    props = context.scene.blenderspicy_graphbuild
    
    #change all graphs colors
    for graph in props.graphs:
        # set the material for the graph object and change the color
        graph_name = 'graph_' + graph.name
        mat_name = 'mat_' + graph.name
        mat,_ = set_material_to_object(graph_name, mat_name)
        set_material_color(mat_name, self.graph_color)
        
        # set the material for the graph-section object and change the color
        sg_name = 'sg_' + graph.name
        mat_sg_name = 'mat_sg_' + graph.name
        mat_sg,_ = set_material_to_object(sg_name, mat_sg_name)
        set_material_color(mat_sg_name, self.graph_color)

def update_plot_mode(self, context):
    pass

############################ Properties ########################################

class GraphBuilderProps(bpy.types.PropertyGroup):
    '''
        Property group for holding graph builder parameters
    '''

    filepath: bpy.props.StringProperty(
        name="data",
        subtype="FILE_PATH"
    )

    animation_folder: bpy.props.StringProperty(
        name="plot storage",
        subtype="DIR_PATH"
    )
    
    plot_mode : bpy.props.EnumProperty(
        name = "MPL or Native",
        description = "Mode of plotting",
        items = [
            ('Native', 'Native', 'Generated from blender objects only, no textures'),           
            ('MPL', 'MPL', 'Matplotlib generated pngs in a texture'),           
        ],
        default = 'Native',
        update=update_plot_mode
    )
    
    sg_option : bpy.props.BoolProperty(
        name="Section-graph curve",
        default = True,
        # update=update_sg_option,
    )
    
    vt_bars_option : bpy.props.BoolProperty(
        name="scale bars for Voltage and time",
        default = False,
        update=update_vt_bars_option,
    )

    v_bar_magnitude : bpy.props.IntProperty(
        name="Voltage scale bar magnitude in mV",
        default = 10,
        update=update_vt_bars,
    )
    
    t_bar_magnitude : bpy.props.IntProperty(
        name="Time scale bar magnitude in ms",
        default = 500,
        update=update_vt_bars,
    )
 
    v_scalar : bpy.props.FloatProperty(
        name="Voltage scalar",
        default = 1,
        min = .1,
        max = 100,
        update=update_scale,
    )
    
    t_scalar : bpy.props.FloatProperty(
        name="Time scalar",
        default = 1,
        min = .1,
        max = 100,
        update=update_scale,
    )
    
    graph_scale : bpy.props.FloatVectorProperty(
        name="Scale current scalars",
        default=(1.0, 1.0),
        subtype='TRANSLATION',
        size=2
    )
    
    animate : bpy.props.BoolProperty(
        name="Animate",
        default = True,
    )
    
    line_width : bpy.props.FloatProperty(
        name="Line width",
        min=0.001,
        soft_max=100,
        default = .02,
        update=update_line_width,
    )
    
    graphs : bpy.props.CollectionProperty(
        type=bpy.types.PropertyGroup,
        name="Graphs"
    )
    
    graph_color : bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        size = 4,
        description="color picker",
        update=update_graph_color,
    )

    voltage_array : bpy.props.CollectionProperty(
        type=bpy.types.PropertyGroup,
        name="Voltage array"
    )

class BLENDERSPICY_OT_GraphBuilder(bpy.types.Operator):
    '''
       Operator to load the NEURON voltage data from specific section and create graph
    '''
    
    bl_idname = 'blenderspicy.build_graph'
    bl_label =  'Build graph'
    
    def execute(self, context):

        props = context.scene.blenderspicy_graphbuild

        if ((bpy.context.selected_objects == []) or
            (not hasattr(bpy.context.selected_objects[0], "parent")) or 
            (not hasattr(bpy.context.selected_objects[0].parent, "name")) or 
            (not bpy.context.selected_objects[0].parent.name.startswith('NEURON'))):
            out('Please select a NEURON section before building a graph.')
            return {"FINISHED"}
            

        section_graph = SectionGraph(
            filepath=bpy.path.abspath(props.filepath),
            animation_folder=bpy.path.abspath(props.animation_folder),
            )
        
        update_scale(self,context)
        
        items = props.graphs
        item = items.add()
        item.name = section_graph.parent_section.name

        print("Built a graph from {}".format(props.filepath))
        print("Saved images in {}".format(props.animation_folder))
        return {"FINISHED"}

class BLENDERSPICY_OT_GraphRemove(bpy.types.Operator):
    bl_idname = "blenderspicy.delete_item"
    bl_label = "Delete Item"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.blenderspicy_graphbuild

        items = props.graphs
        animation_folder = bpy.path.abspath(props.animation_folder)
        
        try:
            plot_mode = bpy.data.objects["graph_" + items[self.index].name]['plot_mode']
        except:
            plot_mode = None
        
        #remove object
        try:
            remove_curve("graph_" + items[self.index].name)
        except:
            out(f'Could not remove object graph object')
        
        #remove section-graph curve
        try:            
            remove_curve("sg_" + items[self.index].name)
        except:
            out(f'Could not remove object section-graph curve')
        
        #remove from list
        try:
            items.remove(self.index)
        except:
            out(f'Could not remove graph from list below')
        
        #remove animation folder
        if plot_mode == 'MPL':
            try:
                folder_path = f'{animation_folder}{items[self.index].name}'
                shutil.rmtree(folder_path)
                out(f'Removed: {folder_path}')
            except:
                out(f'Could not remove folder: {folder_path}')
        
        return {'FINISHED'}


