import bpy
import importlib
import subprocess
import sys

bl_info = {
    "name" : "BlenderSpiky",
    "author" : "Artem Kirsanov & Niels Burghoorn",
    "description" : "Bring NEURON animations to Blender",
    "blender" : (3, 3, 0),
    "version" : (1, 0, 0),
    "location" : "View3D > BlenderSpiky",
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
from .graph_builder import BLENDERSPIKY_OT_GraphBuilder
from .graph_builder import BLENDERSPIKY_OT_GraphRemover
from .graph_builder import BLENDERSPIKY_OT_ScalebarBuilder
from .graph_builder import BLENDERSPIKY_OT_ScalebarRemover
from .graph_builder import BLENDERSPIKY_OT_SgcurveBuilder
from .graph_builder import BLENDERSPIKY_OT_SgcurveRemover
from .graph_builder import BLENDERSPIKY_OT_ReferenceBuilder
from .graph_builder import BLENDERSPIKY_OT_ReferenceRemover

#neuron_builder
from .neuron_builder import NeuronBuilderProps
from .neuron_builder import BLENDERSPIKY_OT_NeuronBuilder

#animation_manager
from .animation_manager import BLENDERSPIKY_OT_HandlerRemover
from .animation_manager import BLENDERSPIKY_OT_AnimationLoader

#materials
from .materials import VoltageMaterialProps
from .materials import BLENDERSPIKY_OT_MaterialCreator
from .materials import BLENDERSPIKY_OT_RemoveMatertials
from .materials import BLENDERSPIKY_OT_SetupWorld

#UI_panels
from .UI_panels import BLENDERSPIKY_PT_NeuronBuilder
from .UI_panels import BLENDERSPIKY_PT_GraphBuilder
from .UI_panels import BLENDERSPIKY_PT_MaterialCreator
from .UI_panels import BLENDERSPIKY_PT_AnimationManager

ordered_classes = [
    # Property Groups
    NeuronBuilderProps,
    GraphBuilderProps,
    VoltageMaterialProps,

    # Operators
    BLENDERSPIKY_OT_NeuronBuilder,
    BLENDERSPIKY_OT_HandlerRemover,
    
    BLENDERSPIKY_OT_GraphBuilder,
    BLENDERSPIKY_OT_GraphRemover,
    BLENDERSPIKY_OT_ScalebarBuilder,
    BLENDERSPIKY_OT_ScalebarRemover,
    BLENDERSPIKY_OT_SgcurveBuilder,
    BLENDERSPIKY_OT_SgcurveRemover,
    BLENDERSPIKY_OT_ReferenceBuilder,
    BLENDERSPIKY_OT_ReferenceRemover,
    
    BLENDERSPIKY_OT_MaterialCreator,
    BLENDERSPIKY_OT_RemoveMatertials,
    
    BLENDERSPIKY_OT_AnimationLoader,
    BLENDERSPIKY_OT_SetupWorld,

    # UI Panels
    BLENDERSPIKY_PT_NeuronBuilder,
    BLENDERSPIKY_PT_GraphBuilder,
    BLENDERSPIKY_PT_AnimationManager,
    BLENDERSPIKY_PT_MaterialCreator
]

def register():
    for cl in ordered_classes:
        bpy.utils.register_class(cl)

    #add property classes
    bpy.types.Scene.blenderspiky_neuronbuild = bpy.props.PointerProperty(type = NeuronBuilderProps)
    bpy.types.Scene.blenderspiky_graphbuild = bpy.props.PointerProperty(type = GraphBuilderProps)
    bpy.types.Scene.blenderspiky_materials = bpy.props.PointerProperty(type = VoltageMaterialProps)

def unregister():
    for cl in reversed(ordered_classes):
        bpy.utils.unregister_class(cl)
        
    #remove property classes
    del bpy.types.Scene.blenderspiky_neuronbuild
    del bpy.types.Scene.blenderspiky_graphbuild
    del bpy.types.Scene.blenderspiky_materials

if __name__ == "__main__":    
    register()
    