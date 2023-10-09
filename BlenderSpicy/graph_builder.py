import bpy
import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
from mathutils import Matrix, Vector

from .utils import ShowMessageBox as out
from .neuron_builder import BlenderSection
import shutil

## ------------------------------ Blender Graph container -----------------------------------

class BlenderGraph():
    '''
        Container class for storing a graph object
    '''
    def load_sections_dicts(self):
        ''' Load the dictionary of Sections data (exported from neuron) into the sections_dicts attribute'''
        with open(self.filepath, "rb") as f:
            self.sections_dicts = pickle.load(f)
    
    def __init__(self,
                 filepath,
                 animation_folder = 'anims',
                 ):
        self.filepath = filepath
        self.animation_folder = animation_folder
        self.mat = None
        
        self.load_sections_dicts() # Loading sections dictionary

        self.parent_segment = bpy.context.selected_objects[0].name
        self.name = f'graph_{self.parent_segment}'
        print(self.name)
        print(self.parent_segment)
        self.build_graph()
        self.create_curve_to_segment()
    
    def create_curve_to_segment(self):
        ''' Create a bezier curve from the graph to the NEURON segment'''

        print("Creating curve to segment")
        graph_obj,segment_obj = [bpy.data.objects[self.name], bpy.data.objects[self.parent_segment]]
        
        name = f'bezier_{self.parent_segment}'

        curve = bpy.data.curves.new('curve_' + name, 'CURVE')
        spline = curve.splines.new('BEZIER')
        obj = bpy.data.objects.new(name, curve)

        spline.bezier_points.add(1)

        empty_loc = segment_obj.parent.location
        
        #hook to furthest edge of segment
        i=0
        p = spline.bezier_points[i]
        vi = np.argmax([(v.co - empty_loc).length for v in segment_obj.data.vertices])
        p.co = segment_obj.data.vertices[vi].co
        p.handle_right_type = 'AUTO'
        p.handle_left_type = 'AUTO'
        h = obj.modifiers.new(segment_obj.name, 'HOOK')
        h.object = segment_obj
        h.vertex_indices_set([a + i*3 for a in range(3)])
        
        #hook to graph origin
        i=1
        p = spline.bezier_points[i]
        p.co = graph_obj.location
        p.handle_right_type = 'AUTO'
        p.handle_left_type = 'AUTO'
        h = obj.modifiers.new(graph_obj.name, 'HOOK')
        h.object = graph_obj
        h.vertex_indices_set([a + i*3 for a in range(3)])
        
        obj.data.bevel_depth = 0.02
        bpy.context.scene.collection.objects.link(obj)
        
        #make material for curve if needed and assign it
        sg_mat = 'Segment-Graph_curves_material'
        color = bpy.context.scene.blenderspicy_graphbuild.graph_color
        if sg_mat in bpy.data.materials:
            bpy.data.materials[sg_mat].node_tree.nodes["Principled BSDF"].inputs[0].default_value = color
        else:
            new_mat = bpy.data.materials.new(sg_mat)
            new_mat.use_nodes = True
            new_mat.node_tree.nodes.get("Principled BSDF").inputs[0].default_value = color
            
            obj.data.materials.append(new_mat)

        # Link the material to the active object (assuming you have an active object)
        obj.active_material = bpy.data.materials[sg_mat]
    
    def build_graph(self):
        segment_type,segment_id = self.parent_segment.split('_')
        segment_id = int(segment_id)

        filtered_data = [entry for entry in self.sections_dicts if 
                        entry['type'] == segment_type and 
                        entry['ID'] == segment_id]
        
        data = filtered_data[0]['Voltage']
        voltage_data = np.array([np.mean(data[vals]) for vals in data])
        
        if bpy.context.scene.blenderspicy_graphbuild.plot_mode == 'MPL':
            graph = self._build_MPL_graph(voltage_data,
                                         self.animation_folder,
                                         self.parent_segment)
        
        return(graph)

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
        mat.name = f'anim_{name}'
        mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
        mat.node_tree.links.remove(mat.node_tree.nodes["Image Texture"].outputs[0].links[0])
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = bpy.context.scene.blenderspicy_graphbuild.graph_color
    
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
    

class BlenderNativeGraph():
    def make_spline():
        x = np.linspace(-5,5,100)
        y = np.sin(x*2)

        xt = np.meshgrid(np.linspace(-5,5,100),np.linspace(0,3,4))
        xt = xt[0]+xt[1]
        yt = np.sin(2*(xt))

        points = list(zip(x,y))
        points_t = np.array([ [(xi,yi) for xi,yi in zip(xyt[0],xyt[1])] for xyt in zip(xt,yt)])
            
        #plot_2D_line(points, name = '2D_line')
        print(points_t)
        plot_2Dt_line(points_t, name = '2Dt_line')
        #plot_2D_scatter(points, name = '2D_scatter')
        
    def plot_2D_line(points_2D, name="object_name", Z=0):
        points_3D = [[point[0],point[1],Z] for point in points_2D]
        
        # make a new curve
        crv = bpy.data.curves.new('crv', 'CURVE')
        crv.dimensions = '3D'

        # make a new spline in that curve
        spline = crv.splines.new(type='POLY')

        # a spline point for each point
        spline.points.add(len(points_3D)-1) # theres already one point by default

        # assign the point coordinates to the spline points
        for p, new_co in zip(spline.points, points_3D):
            p.co = (new_co + [1.0]) # (add nurbs weight)

        # make a new object with the curve
        obj = bpy.data.objects.new(name, crv)
        obj.data.bevel_depth = .2
        obj.data.use_fill_caps = True
        bpy.context.scene.collection.objects.link(obj)
        
    def plot_2Dt_line(points_2Dt, name="object_name", Z=0):
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
        
    def plot_2Dscatter(points_2D, name="object_name", Z=0):
        points_3D = [[point[0],point[1],Z] for point in points_2D]
        
        ico = bpy.data.meshes.new('ICOSPHERE')
        
        for point in points_3D:
            # make a new object with the curve
            obj = bpy.data.objects.new(name, ico)
    #        obj.data.diameter = 1
            bpy.context.scene.collection.objects.link(obj)

# Callback functions
def update_graph_color(self, context):
    # This function will be called when the graph_color property changes
    # You can access the updated value with self.graph_color
    props = context.scene.blenderspicy_graphbuild
    
    #change all graphs colors
    for graph in props.graphs:
        mat = bpy.data.materials['anim_' + graph.name]
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = self.graph_color
    
    #change all segment-graph curves colors
    sg_mat = 'Segment-Graph_curves_material'
    if sg_mat in bpy.data.materials:
        bpy.data.materials[sg_mat].node_tree.nodes["Principled BSDF"].inputs[0].default_value = self.graph_color
    else:
        new_mat = bpy.ops.material.new()
        new_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = self.graph_color

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
        subtype="FILE_PATH"
    )
    
    plot_mode : bpy.props.EnumProperty(
        name = "MPL or Native",
        description = "Mode of plottin",
        items = [
            ('MPL', 'MPL', 'Matplotlib generated pngs in a texture'),           
            ('Native', 'Native', 'Generated from blender objects only, no textures'),           
        ],
        update=update_plot_mode
    )
    
    linewidth : bpy.props.IntProperty(
        name="Line width",
        min=1,
        soft_max=100,
        default = 5
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

class BLENDERSPICY_OT_GraphBuilder(bpy.types.Operator):
    '''
       Operator to load the NEURON voltage data from specific segment and create graph
    '''
    
    bl_idname = 'blenderspicy.build_graph'
    bl_label =  'Build a graph'
    
    def execute(self, context):

        props = context.scene.blenderspicy_graphbuild

        if ((bpy.context.selected_objects == []) or
            (not hasattr(bpy.context.selected_objects[0], "parent")) or 
            (not hasattr(bpy.context.selected_objects[0].parent, "name")) or 
            (not bpy.context.selected_objects[0].parent.name.startswith('NEURON'))):
            out('Please select a NEURON segment before building a graph.')
            return {"FINISHED"}
            

        bgraph = BlenderGraph(
            filepath=props.filepath,
            animation_folder=props.animation_folder,
            )
        
        items = props.graphs
        item = items.add()
        item.name = bgraph.parent_segment

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
        
        #remove object and its segment curve
        try:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects["graph_" + items[self.index].name].select_set(True)
            bpy.ops.object.delete() 
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects["bezier_" + items[self.index].name].select_set(True)
            bpy.ops.object.delete() 
        except:
            out(f'Could not remove object: {"graph_" + items[self.index].name}')
            
        #remove animation folder
        try:
            folder_path = f'{props.animation_folder}{items[self.index].name}'
            shutil.rmtree(folder_path)
            out(f'Removed: {folder_path}')
        except:
            out(f'Could not remove folder: {folder_path}')
        
        #remove from list
        try:
            items.remove(self.index)
        except:
            out(f'Could not remove graph from list (index=): {self.index}')
        
        return {'FINISHED'}