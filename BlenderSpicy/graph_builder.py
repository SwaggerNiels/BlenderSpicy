import bpy
import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
import shutil

## ------------------------------ Blender Graph container -----------------------------------

class BlenderGraph():
    '''
        Container class for storing a voltage graph object
    '''
    def load_sections_dicts(self):
        ''' Load the dictionary of Sections data (exported from neuron) into the sections_dicts attribute'''
        with open(self.filepath, "rb") as f:
            self.sections_dicts = pickle.load(f)
    
    def __init__(self,
                 filepath,
                 animation_folder = 'anims',
                 parent_ob = None,
                 ):
        self.name = "GRAPH"
        self.filepath = filepath
        self.animation_folder = animation_folder
        
        self.load_sections_dicts() # Loading sections dictionary

        self.parent_segment = bpy.context.selected_objects[0]
        
        if parent_ob is None:
            self.create_parent_empty()
            self.set_parent_metadata()
        else:
            self.parent_ob = parent_ob
            self.name = parent_ob.name
    
    def create_parent_empty(self):
        ''' Create a parent EMPTY Blender object, which holds metadata'''

        print("Creating parent object")
        bpy.ops.object.empty_add(type='ARROWS',location=(self.sections_dicts[0]["X"][0],self.sections_dicts[0]["Y"][0],self.sections_dicts[0]["Z"][0]), rotation=(0, 0, 0))
        self.parent_ob = bpy.context.selected_objects[0]
        self.parent_ob.name = self.name
        
    def set_parent_metadata(self):
        ''' Store metadata in a custom properties of the parent EMPTY object '''
        attrs_to_save = ["filepath", "animation_folder"]
        for attr in attrs_to_save:
            self.parent_ob[attr] = getattr(self, attr)
        
    def make_separate_plots(self,
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

            if zero_start:
                y = np.array([np.min(voltage_data)] + list(voltage_data))
            else:
                y = voltage_data
            x = np.array(range(y.size), dtype=int)
            
            line, = plt.plot([], [], lw=lw)

            def _save_frames(i):
                line.set_data(x[:i], y[:i])
                filename = folder_path + f'/frame_{i:04d}.png'
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
    
    def build_graph(self,):
        desired_type,desired_id = self.parent_segment.name.split('_')
        desired_id = int(desired_id)

        filtered_data = [entry for entry in self.sections_dicts if 
                        entry['type'] == desired_type and 
                        entry['ID'] == desired_id]
        
        data = filtered_data[0]['Voltage']
        voltage_data = np.array([np.mean(data[vals]) for vals in data])
        
        folder_name = f'{desired_type}_{desired_id}'
        folder_path = f'{self.animation_folder}{folder_name}'
        
        # open pickle file and process to plots
        self.make_separate_plots(folder_path,voltage_data)
        
        files = [{"name": f, "name": f} 
                 for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        print(files)
        # file_array = 
        bpy.ops.import_image.to_plane(files=files, 
                                      directory=folder_path, 
                                      image_sequence=True, 
                                      relative=False)
    
    def remove_images(self, folder_path):
        # shutil.rmtree(folder_path)
        # os.makedirs(folder_path)
        pass


class GraphBuilderProps(bpy.types.PropertyGroup):
    '''
        Property group for holding graph builder parameters
    '''

    filepath: bpy.props.StringProperty(
        name="Path to .pickle",
        subtype="FILE_PATH"
    )

    animation_folder: bpy.props.StringProperty(
        name="Path to store graphs",
        subtype="FILE_PATH"
    )
    
    linewidth : bpy.props.IntProperty(
        name="Linewidth",
        min=1,
        soft_max=100,
        default = 5
    )

class BLENDERSPICY_OT_GraphBuilder(bpy.types.Operator):
    '''
       Operator to load the NEURON voltage data from specific segment and create graph
    '''
    
    bl_idname = 'blenderspicy.build_graph'
    bl_label =  'Build a graph'
    
    def execute(self, context):

        props = context.scene.blenderspicy_graphbuild

        graph = BlenderGraph(
            filepath=props.filepath,
            animation_folder=props.animation_folder,
            )
        
        graph.build_graph()

        print("Built a graph from {}".format(props.filepath))
        print("Saved images in {}".format(props.animation_folder))
        return {"FINISHED"}

    