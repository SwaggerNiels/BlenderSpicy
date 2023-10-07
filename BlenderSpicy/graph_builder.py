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
                 animation_folder = 'anims',
                 parent_ob = None,
                 ):
        self.animation_folder = animation_folder
        
        self.load_sections_dicts() # Loading sections dictionary

        if parent_ob is None:
            self.create_parent_empty()
            self.set_parent_metadata()
        else:
            self.parent_ob = parent_ob
            self.name = parent_ob.name
        
    def make_separate_plots(self,
                            foldername,
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
        folder_path = f'{self.animation_folder}/{foldername}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            shutil.rmtree(folder_path)
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
    
    def build_graph(self,):
        bpy.ops.import_image.to_plane(directory=self.animation_folder)
        # print('build graph')


class GraphBuilderProps(bpy.types.PropertyGroup):
    '''
        Property group for holding graph builder parameters
    '''

    animation_folder: bpy.props.StringProperty(
        name="Path to store graphs",
        subtype="FILE_PATH"
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
            neuron=props,
            filepath=props.filepath,
            animation_folder=props.animation_folder,
            )

        print("Built a graph from {}".format(props.filepath))
        return {"FINISHED"}

