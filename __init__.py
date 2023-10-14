import bpy
import importlib
import subprocess
import sys

bl_info = {
    "name" : "BlenderSpicy",
    "author" : "Artem Kirsanov & Niels Burghoorn",
    "description" : "Bring NEURON animations to Blender",
    "blender" : (3, 3, 0),
    "version" : (1, 0, 0),
    "location" : "View3D > BlenderSpicy",
    "warning" : "",
    "category" : "3D View"
}

def check_and_install_modules():
    '''
        Automatically install required Python modules
    '''
    required_modules_import_names = ["matplotlib","seaborn", "cmasher", "numpy", "os", "shutil"]  # Required Python modules
    required_modules_install_names = ["matplotlib","seaborn", "cmasher", "numpy", "os", "shutil"]


    missing_modules = []
    for k,module_name in enumerate(required_modules_import_names):
        try:
            importlib.import_module(module_name)
            print(f"Module {module_name} is already installed. Importing...")
        except ImportError:
            missing_modules.append(required_modules_install_names[k])
            
    if missing_modules:
        print("Found missing modules: ", missing_modules)
        for module in missing_modules: 
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"{module} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {module}.")


check_and_install_modules() # This is called before any imports from the submodules

#graph_builder
from .graph_builder import GraphBuilderProps
from .graph_builder import BLENDERSPICY_OT_GraphBuilder
from .graph_builder import BLENDERSPICY_OT_GraphRemover
from .graph_builder import BLENDERSPICY_OT_ScalebarBuilder
from .graph_builder import BLENDERSPICY_OT_ScalebarRemover
from .graph_builder import BLENDERSPICY_OT_SgcurveBuilder
from .graph_builder import BLENDERSPICY_OT_SgcurveRemover
from .graph_builder import BLENDERSPICY_OT_ReferenceBuilder
from .graph_builder import BLENDERSPICY_OT_ReferenceRemover

#neuron_builder
from .neuron_builder import NeuronBuilderProps
from .neuron_builder import BLENDERSPICY_OT_NeuronBuilder

#animation_manager
from .animation_manager import BLENDERSPICY_OT_HandlerRemover
from .animation_manager import BLENDERSPICY_OT_AnimationLoader

#materials
from .materials import VoltageMaterialProps
from .materials import BLENDERSPICY_OT_MaterialCreator
from .materials import BLENDERSPICY_OT_RemoveMatertials
from .materials import BLENDERSPICY_OT_SetupWorld

#UI_panels
from .UI_panels import BLENDERSPICY_PT_NeuronBuilder
from .UI_panels import BLENDERSPICY_PT_GraphBuilder
from .UI_panels import BLENDERSPICY_PT_MaterialCreator
from .UI_panels import BLENDERSPICY_PT_AnimationManager

ordered_classes = [
    # Property Groups
    NeuronBuilderProps,
    GraphBuilderProps,
    VoltageMaterialProps,

    # Operators
    BLENDERSPICY_OT_NeuronBuilder,
    BLENDERSPICY_OT_HandlerRemover,
    
    BLENDERSPICY_OT_GraphBuilder,
    BLENDERSPICY_OT_GraphRemover,
    BLENDERSPICY_OT_ScalebarBuilder,
    BLENDERSPICY_OT_ScalebarRemover,
    BLENDERSPICY_OT_SgcurveBuilder,
    BLENDERSPICY_OT_SgcurveRemover,
    BLENDERSPICY_OT_ReferenceBuilder,
    BLENDERSPICY_OT_ReferenceRemover,
    
    BLENDERSPICY_OT_MaterialCreator,
    BLENDERSPICY_OT_RemoveMatertials,
    
    BLENDERSPICY_OT_AnimationLoader,
    BLENDERSPICY_OT_SetupWorld,

    # UI Panels
    BLENDERSPICY_PT_NeuronBuilder,
    BLENDERSPICY_PT_GraphBuilder,
    BLENDERSPICY_PT_AnimationManager,
    BLENDERSPICY_PT_MaterialCreator
]

def register():
    for cl in ordered_classes:
        bpy.utils.register_class(cl)

    #add property classes
    bpy.types.Scene.blenderspicy_neuronbuild = bpy.props.PointerProperty(type = NeuronBuilderProps)
    bpy.types.Scene.blenderspicy_graphbuild = bpy.props.PointerProperty(type = GraphBuilderProps)
    bpy.types.Scene.blenderspicy_materials = bpy.props.PointerProperty(type = VoltageMaterialProps)

def unregister():
    for cl in reversed(ordered_classes):
        bpy.utils.unregister_class(cl)
        
    #remove property classes
    del bpy.types.Scene.blenderspicy_neuronbuild
    del bpy.types.Scene.blenderspicy_graphbuild
    del bpy.types.Scene.blenderspicy_materials

if __name__ == "__main__":
    #addon specific blender settings
    bpy.context.space_data.overlay.show_relationship_lines = False
    
    register()
    

    