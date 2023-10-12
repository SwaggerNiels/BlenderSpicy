import bpy
import numpy as np
import pickle
from scipy.interpolate import interp1d

def _get_make_node_material(mat_name):
    if mat_name in bpy.data.materials:
        mat = bpy.data.materials[mat_name]
        mat.use_nodes = True
    else:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
    return (mat)

def set_material_to_object(obj_name, mat_name):
    '''
        Quick material set to object and return both (obj,mat)
    '''
    mat = _get_make_node_material(mat_name)
    
    obj = bpy.data.objects[obj_name]
    if mat_name not in obj.data.materials:
        obj.data.materials.append(mat)
    
    return (obj,mat)

def set_material_color(mat_name, color_vector):
    '''
        Quick material set to color and return mat
    '''
    mat = _get_make_node_material(mat_name)
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color_vector
    
    return (mat)

def load_sections_dicts(path):
    ''' Load the dictionary of Sections data (exported from neuron) into the sections_dicts attribute'''
    with open(path, "rb") as f:
        sections_dicts = pickle.load(f)
    return(sections_dicts)

def linear_interpolation(source_data, n_points):
    '''
        Linearly resamples an array with n_points
    '''

    if(len(source_data)==1):
        return np.ones(n_points)*source_data[0]
    source_prop = np.linspace(0,1, len(source_data))
    output_prop = np.linspace(0,1, n_points)
    interF = interp1d(source_prop, source_data)
    output= interF(output_prop)
    
    return output
    
def remove_curve(obj_name):
    objs = bpy.data.objects
    
    mat_name = 'mat_' + obj_name
    curve_name = 'curve_' + obj_name
    
    print(objs)
    print(obj_name)
    for child in objs[obj_name].children:
        remove_curve(child.name)
    
    objs.remove(objs[obj_name], do_unlink=True)
    
    if objs.data.curves.get(curve_name) != None:
        objs.data.curves.remove(objs.data.curves.get(curve_name))
    
    if mat_name in bpy.data.materials:
        objs.data.materials.remove(objs.data.curves.get(mat_name))

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    '''
    Popup message. Syntax:
        ShowMessageBox("This is a message") 
        ShowMessageBox("This is a message", "This is a custom title")
        ShowMessageBox("This is a message", "This is a custom title", 'ERROR')
    '''

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)