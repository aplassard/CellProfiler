'''imagej2 - in-process connection to ImageJ 2.0

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2013 Broad Institute

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''

import logging
logger = logging.getLogger(__name__)

import numpy as np
import os
import sys
import time

import cellprofiler.utilities.jutil as J

REQUIRED_SERVICES = [
    "imagej.script.ScriptService",
    "imagej.event.EventService",
    "imagej.object.ObjectService",
    "imagej.platform.PlatformService",
    "imagej.plugin.PluginService",
    "imagej.module.ModuleService",
    'imagej.display.DisplayService',
    "imagej.command.CommandService",
    'imagej.data.DatasetService',
    'imagej.data.display.OverlayService',
    'imagej.ui.UIService'    
]

'''Field type = integer'''
FT_INTEGER = "INTEGER"
'''Field type = floating point'''
FT_FLOAT = "FLOAT"
'''Field type = string'''
FT_STRING = "STRING"
'''Field type = image'''
FT_IMAGE = "IMAGE"
'''Field type = boolean'''
FT_BOOL = "BOOL"
'''Field type = overlay'''
FT_OVERLAY = "OVERLAY"
'''Field type = java.io.File'''
FT_FILE = "FILE"
'''Field type = imagej.util.ColorRGB'''
FT_COLOR = "COLOR"
'''Field type = imagej.data.table.TableDisplay'''
FT_TABLE = "TABLE"

field_mapping = {
    'java.io.File': FT_FILE,
    'java.lang.Byte': FT_INTEGER,
    'java.lang.Short': FT_INTEGER,
    'java.lang.Integer': FT_INTEGER,
    'java.lang.Long': FT_INTEGER,
    'int': FT_INTEGER,
    'short': FT_INTEGER,
    'byte': FT_INTEGER,
    'long': FT_INTEGER,
    'java.lang.Float': FT_FLOAT,
    'java.lang.Double': FT_FLOAT,
    'float': FT_FLOAT,
    'double': FT_FLOAT,
    'java.lang.String': FT_STRING,
    'java.lang.Boolean': FT_BOOL,
    'boolean': FT_BOOL,
    'imagej.util.ColorRGB': FT_COLOR
}

def field_class_mapping():
    return (
        (J.class_for_name('imagej.data.display.ImageDisplay'), FT_IMAGE),
        (J.class_for_name('imagej.data.Dataset'), FT_IMAGE),
        (J.class_for_name('imagej.data.display.DatasetView'), FT_IMAGE),
        (J.class_for_name('imagej.data.table.TableDisplay'), FT_TABLE)
    )

def run_imagej(*args):
    J.static_call("imagej/Main", "main", "([Ljava/lang/String;)V",
                  *[unicode(arg) for arg in args])

def create_context(service_classes):
    '''Create an ImageJ context for getting services

    This is an imagej.ImageJ, which at one point was the context.
    Call self.getContext() to get the org.scijava.Context which may be 
    what you want.
    '''
    class Context(object):
        def __init__(self):
            if service_classes is None:
                classes = None
                ctxt_fn = J.run_script(
                    """new java.util.concurrent.Callable() {
                        call: function() {
                            return new Packages.imagej.ImageJ(false);
                        }
                    }""")
            else:
                classes = [ 
                    J.class_for_name(x) 
                    for x in service_classes or REQUIRED_SERVICES]
                classes = J.make_list(classes)
                ctxt_fn = J.run_script(
                    """new java.util.concurrent.Callable() {
                        call: function() {
                            return new Packages.imagej.ImageJ(classes);
                        }
                    }""", dict(classes = classes.o))
            
            self.o = J.execute_future_in_main_thread(
                J.make_future_task(ctxt_fn))
        
        def getService(self, class_name):
            '''Get a service with the given class name
            
            class_name - class name in dotted form
            
            returns the class or None if no implementor loaded.
            '''
            klass = J.class_for_name(class_name)
            return J.call(self.o, 'get', 
                          '(Ljava/lang/Class;)Lorg/scijava/service/Service;', klass)
        getContext = J.make_method("getContext", "()Lorg/scijava/Context;")
    return Context()

the_imagej_context = None
def get_context():
    '''Get the ImageJ context
    
    This is a singleton ImageJ context. We need a singleton for now because
    of http://trac.imagej.net/ticket/1413
    This is an imagej.ImageJ, which at one point was the context.
    Call self.getContext() to get the org.scijava.Context which may be 
    what you want.
    '''
    global the_imagej_context
    if the_imagej_context is None:
        the_imagej_context = create_context(None)
    return the_imagej_context

def get_module_service(context):
    '''Get the module service for a given context
    
    context - the instance of ImageJ created by create_context
    
    returns a module service
    '''
    o = context.getService('imagej.module.ModuleService')
    class ModuleService(object):
        def __init__(self):
            self.o = o
        def getModules(self):
            modules = J.call(o, "getModules", "()Ljava/util/List;")
            if modules is None:
                return []
            module_iterator = J.call(modules, "iterator", 
                                     "()Ljava/util/Iterator;")
            return [wrap_module_info(x) for x in J.iterate_java(module_iterator)]
        
        def getIndex(self):
            index = J.call(self.o, "getIndex", "()Limagej/module/ModuleIndex;")
            index = J.get_collection_wrapper(index, wrap_module_info)
            index.getC = lambda c: J.get_collection_wrapper(
                J.call(index.o, "get", "(Ljava/lang/Class;)Ljava/util/List;",c),
                wrap_module_info)
            index.getS = lambda class_name: \
                index.getC(J.class_for_name(class_name))
            return index
        
        def run(self, module_info,
                pre = None,
                post = None,
                **kwargs):
            '''Run a module
            
            module_info - the module_info of the module to run
            
            pre - list of PreprocessorPlugins to run before running module
            
            post - list of PostprocessorPlugins to run after running module
            
            *kwargs - names and values for input parameters
            '''
            input_map = J.make_map(kwargs)
            if pre is not None:
                pre = J.static_call("java/util/Arrays", "asList",
                                    "([Ljava/lang/Object;)Ljava/util/List;",
                                    pre)
            if post is not None:
                post = J.static_call("java/util/Arrays", "asList",
                                     "([Ljava/lang/Object;)Ljava/util/List;",
                                     post)
            future = J.call(
                self.o, "run", 
                "(Limagej/module/ModuleInfo;"
                "Ljava/util/List;"
                "Ljava/util/List;"
                "Ljava/util/Map;)"
                "Ljava/util/concurrent/Future;",
                module_info, pre, post, input_map)
            return J.call(
                self.o, "waitFor", 
                "(Ljava/util/concurrent/Future;)Limagej/module/Module;",
                future)
    return ModuleService()

def wrap_module_info(instance):
    '''Wrap a java object of class imagej/module/ModuleInfo'''
    class ModuleInfo(object):
        def __init__(self):
            self.o = instance

        getInput = J.make_method(
            "getInput", 
            "(Ljava/lang/String;)Limagej/module/ModuleItem;", 
            doc = "Gets the input item with the given name.",
            fn_post_process=wrap_module_item)

        getOutput = J.make_method(
            "getOutput", 
            "(Ljava/lang/String;)Limagej/module/ModuleItem;",
            doc = "Gets the output item with the given name.",
            fn_post_process=wrap_module_item)

        getInputs = J.make_method(
            "inputs", "()Ljava/lang/Iterable;",
            """Get the module info's input module items""",
            fn_post_process=lambda iterator:
            map(wrap_module_item, J.iterate_collection(iterator)))
            
        getOutputs = J.make_method(
            "outputs", "()Ljava/lang/Iterable;",
            """Get the module info's output module items""",
            fn_post_process=lambda iterator:
            map(wrap_module_item, J.iterate_collection(iterator)))
        
        getTitle = J.make_method(
            "getTitle",
            "()Ljava/lang/String;")
        createModule = J.make_method(
            "createModule",
            "()Limagej/module/Module;",
            fn_post_process=wrap_module)
        getMenuPath = J.make_method(
            "getMenuPath", "()Lorg/scijava/MenuPath;")
        getMenuRoot = J.make_method(
            "getMenuRoot", "()Ljava/lang/String;")
        getName = J.make_method("getName", "()Ljava/lang/String;")
        getClassName = J.make_method("getClassName", "()Ljava/lang/String;")
    return ModuleInfo()

def wrap_module_item(instance):
    '''Wrap a Java object of class imagej.module.ModuleItem'''
    class ModuleItem(object):
        def __init__(self):
            self.o = instance
            
        IV_NORMAL = J.get_static_field("org/scijava/ItemVisibility",
                                       "NORMAL",
                                       "Lorg/scijava/ItemVisibility;")
        IV_TRANSIENT = J.get_static_field("org/scijava/ItemVisibility",
                                          "TRANSIENT",
                                          "Lorg/scijava/ItemVisibility;")
        IV_INVISIBLE = J.get_static_field("org/scijava/ItemVisibility",
                                          "INVISIBLE",
                                          "Lorg/scijava/ItemVisibility;")
        IV_MESSAGE = J.get_static_field("org/scijava/ItemVisibility",
                                        "MESSAGE",
                                        "Lorg/scijava/ItemVisibility;")
                
        
        def getType(self):
            jtype = J.call(self.o, "getType", "()Ljava/lang/Class;")
            type_name = J.call(jtype, "getCanonicalName", "()Ljava/lang/String;")
            if field_mapping.has_key(type_name):
                return field_mapping[type_name]
            for class_instance, result in field_class_mapping():
                if J.call(class_instance, "isAssignableFrom",
                          "(Ljava/lang/Class;)Z", jtype):
                    return result
            return None
            
            
        getWidgetStyle = J.make_method("getWidgetStyle",
                                       "()Ljava/lang/String;")
        getMinimumValue = J.make_method("getMinimumValue",
                                        "()Ljava/lang/Object;")
        getMaximumValue = J.make_method("getMaximumValue",
                                        "()Ljava/lang/Object;")
        getStepSize = J.make_method("getStepSize",
                                    "()Ljava/lang/Number;")
        getColumnCount = J.make_method("getColumnCount", "()I")
        getChoices = J.make_method("getChoices", "()Ljava/util/List;")
        getValue = J.make_method("getValue", 
                                 "(Limagej/module/Module;)Ljava/lang/Object;")
        setValue = J.make_method(
            "setValue", "(Limagej/module/Module;Ljava/lang/Object;)V",
            "Set the value associated with this item on the module")
        getName = J.make_method("getName", "()Ljava/lang/String;")
        getLabel = J.make_method("getLabel", "()Ljava/lang/String;")
        getDescription = J.make_method("getDescription", "()Ljava/lang/String;")
        loadValue = J.make_method("loadValue", "()Ljava/lang/Object;")
        isInput = J.make_method("isInput", "()Z")
        isOutput = J.make_method("isOutput", "()Z")
    return ModuleItem()
    
def wrap_module(module):
    class Module(object):
        def __init__(self, o = module):
            self.o = o
            
        getInfo = J.make_method("getInfo", "()Limagej/module/ModuleInfo;")
        getInput = J.make_method("getInput", "(Ljava/lang/String;)Ljava/lang/Object;")
        getOutput = J.make_method("getOutput", "(Ljava/lang/String;)Ljava/lang/Object;")
        setInput = J.make_method("setInput", "(Ljava/lang/String;Ljava/lang/Object;)V")
        setOutput = J.make_method("setOutput", "(Ljava/lang/String;Ljava/lang/Object;)V")
        isResolved = J.make_method("isResolved", "(Ljava/lang/String;)Z")
        setResolved = J.make_method("setResolved", "(Ljava/lang/String;Z)V")
    return Module()

def wrap_menu_entry(menu_entry):
    '''Wrap an instance of imagej.ext.MenuEntry'''
    class MenuEntry(object):
        def __init__(self, o = menu_entry):
            self.o = o
        setName = J.make_method("setName", "(Ljava/lang/String;)V")
        getName = J.make_method("getName", "()Ljava/lang/String;")
        setWeight = J.make_method("setWeight", "(D)V")
        getWeight = J.make_method("getWeight", "()D")
        setMnemonic = J.make_method("setMnemonic", "(C)V")
        getMnemonic = J.make_method("getMnemonic", "()C")
        setAccelerator = J.make_method(
            "setAccelerator", "(Lorg/scijava/input/Accelerator;)V")
        getAccelerator = J.make_method(
            "getAccelerator", "()Lorg/scijava/input/Accelerator;")
        setIconPath = J.make_method("setIconPath", "(Ljava/lang/String;)V")
        getIconPath = J.make_method("getIconPath", "()Ljava/lang/String;")
        assignProperties = J.make_method("assignProperties", 
                                         "(Limagej/MenuEntry;)V")
    return MenuEntry(menu_entry)

def get_command_service(context):
    '''Get the command service for a given context
    
    The command service is used to run modules with command pre and post
    processing.
    '''
    command_service = context.getService("imagej.command.CommandService")
    class CommandService(object):
        def __init__(self):
            self.o = command_service
        run = J.make_method(
            "run", 
            "(Limagej/module/ModuleInfo;Ljava/util/Map;)"
            "Ljava/util/concurrent/Future;",
            doc = """Run the command associated with a ModuleInfo
            
            Runs the command with pre and post processing plugins.
            
            module_info - the ModuleInfo that defines a command
            
            inputs - a java.util.map of parameter name to value
            
            returns a java.util.concurrent.Future that can be redeemed
            for the module after the module has been run.
            """, 
            fn_post_process=J.get_future_wrapper)
        getCommandS = J.make_method(
            "getCommand", "(Ljava/lang/String;)Limagej/command/CommandInfo;",
            doc = """Get command by class name
            
            className - dotted class name, e.g. imagej.core.commands.app.AboutImageJ
            """,
            fn_post_process=wrap_module_info)
        
    return CommandService()

def get_display_service(context):
    '''Get the display service for a given context
    
    context - the ImageJ context for the thread
    '''
    o = context.getService('imagej.display.DisplayService')
    class DisplayService(object):
        def __init__(self):
            self.o = o
        def createDisplay(self, name, dataset):
            '''Create a display that contains the given dataset'''
            #
            # Must be run on the gui thread
            #
            jcallable = J.run_script(
                """new java.util.concurrent.Callable() {
                    call:function() {
                        return displayService.createDisplay(name, dataset);
                    }
                };
                """, dict(displayService=self.o,
                          name = name,
                          dataset = dataset.o))
            future = J.make_future_task(jcallable,
                                        fn_post_process = wrap_display)
            return J.execute_future_in_main_thread(future)
        def getActiveDisplay(self, klass=None):
            '''Get the first display, optionally of the given type from the list
            
            klass - if not None, return the first display of this type, 
                    otherwise return the first display
            '''
            if klass is None:
                return wrap_display(J.call(
                    self.o, "getActiveDisplay",
                    "()Limagej/display/Display;"))
            else:
                return wrap_display(J.call(
                    self.o, "getActiveDisplay",
                    "(Ljava/lang/Class;)Limagej/display/Display;", klass))

        def getActiveImageDisplay(self):
            '''Get the active imagej.data.display.ImageDisplay'''
            return wrap_display(J.call(
                self.o, "getActiveDisplay",
                "()Limagej/display/Display;",
                J.class_for_name("imagej.data.display.ImageDisplay")))
        
        def setActiveDisplay(self, display):
            '''Make this the active display'''
            # Note: has to be run in GUI thread on mac
            r = J.run_script(
                """new java.lang.Runnable() {
                    run:function() { displayService.setActiveDisplay(display); }
                }
                """, dict(displayService=self.o, display=display.o))
            J.execute_runnable_in_main_thread(r, True)
        getDisplays = J.make_method(
            "getDisplays", 
            "()Ljava/util/List;",
            fn_post_process = lambda x: 
            map(wrap_display, J.iterate_collection(x)))
        getDisplay = J.make_method(
            "getDisplay",
            "(Ljava/lang/String;)Limagej/display/Display;",
            fn_post_process=wrap_display)
        isUniqueName = J.make_method("isUniqueName", "(Ljava/lang/String;)Z")
        
    return DisplayService()

def wrap_display(display):
    class ImageDisplay(object):
        def __init__(self):
            self.o = display
        #
        # List<DataView> methods
        #
        size = J.make_method("size", "()I")
        isEmpty = J.make_method("isEmpty", "()Z")
        contains = J.make_method("contains", "(Ljava/lang/Object;)Z")
        def __iter__(self):
            return J.iterate_collection(self.o)
        toArray = J.make_method(
            "toArray", "()[Ljava/lang/Object;",
            fn_post_process=
            lambda o:[wrap_data_view(v) 
                      for v in J.get_env().get_object_array_elements(o)])
        addO = J.make_method("add", "(Ljava/lang/Object;)Z")
        removeO = J.make_method("remove", "(Ljava/lang/Object;)Z")
        clear = J.make_method("clear", "()V")
        get = J.make_method("get", "(I)Ljava/lang/Object;",
                            fn_post_process = wrap_data_view)
        set = J.make_method("set", "(ILjava/lang/Object;)V")
        addI = J.make_method("add", "(ILjava/lang/Object;)V")
        removeI = J.make_method("remove", "(I)V")
        #
        # Display methods
        #
        canDisplay = J.make_method(
            "canDisplay", "(Ljava/lang/Object;)Z",
            "Return true if display can display dataset")
        display = J.make_method(
            "display", "(Ljava/lang/Object;)V",
            "Display the given object")
        update = J.make_method("update", "()V",
                               "Signal display change")
        getName = J.make_method("getName", "()Ljava/lang/String;")
        setName = J.make_method("setName", "(Ljava/lang/String;)V")
        def close(self):
            '''Close the display
            
            This is run in the UI thread with synchronization.
            '''
            r = J.run_script(
                """new java.lang.Runnable() {
                run: function() { display.close(); }
                };
                """, dict(display=self.o))
            J.execute_runnable_in_main_thread(r, True)
        #
        # ImageDisplay methods
        #
        getActiveView = J.make_method(
            "getActiveView", "()Limagej/data/display/DataView;",
            fn_post_process=wrap_data_view)
        getActiveAxis = J.make_method(
            "getActiveAxis", "()Lnet/imglib2/meta/AxisType;")
        setActiveAxis = J.make_method(
            "setActiveAxis", "(Lnet/imglib2/meta/AxisType;)V")
        getCanvas = J.make_method(
            "getCanvas", "()Limagej/data/display/ImageCanvas;")
    return ImageDisplay()
                
def get_dataset_service(context):
    o = context.getService('imagej.data.DatasetService')
    class DatasetService(object):
        def __init__(self, o=o):
            self.o = o
            
        getAllDatasets = J.make_method(
            "getDatasets", "()Ljava/util/List;",
            doc = "Get all dataset objects in the context")
        getDatasets = J.make_method(
            "getDatasets", 
            "(Limagej/data/display/ImageDisplay)Ljava/util/List;",
            doc = """Get the datasets linked to a particular image display""")
        create1 = J.make_method(
            "create",
            "([JLjava/lang/String;[Lnet/imglib2/meta/AxisType;IZZ)"
            "Limagej/data/Dataset;",
            doc = """Create a dataset with a given bitdepth
            
            dims - # of dimensions
            
            name - name of dataset
            
            axes - the dataset's axis labels
            
            bitsPerPixel - dataset's bit depth / precision
            
            signed - whether the native type is signed or unsigned
            
            floating - whether the native type is floating or integer""",
            fn_post_process=wrap_dataset)
        create2 = J.make_method(
            "create",
            "(Lnet/imglib2/type/numeric/RealType;[JLjava/lang/String;[Lnet/imglib2/meta/AxisType;)"
            "Limagej/data/Dataset;",
            doc = """Create a dataset based on an IMGLIB type
            
            type - The type of the dataset.
	    dims - The dataset's dimensional extents.
            name - The dataset's name.
            axes - The dataset's dimensional axis labels.""",
            fn_post_process=wrap_dataset)
        create3 = J.make_method(
            "create",
            "(Lnet/imglib2/img/ImgFactory;"
            "Lnet/imglib2/type/numeric/RealType;"
            "[JLjava/lang/String;[Lnet/imglib2/meta/AxisType)"
            "Limagej/data/Dataset;",
            doc = """Create a dataset from an IMGLIB image factory
            
            factory - The ImgFactory to use to create the data.
            type - The type of the dataset.
            dims - The dataset's dimensional extents.
            name - The dataset's name.
            axes - The dataset's dimensional axis labels.""",
            fn_post_process=wrap_dataset)
        create4 = J.make_method(
            "create",
            "Lnet/imglib2/img/ImgPlus;",
            doc = """Create a dataset wrapped around an ImgPlus""",
            fn_post_process=wrap_dataset)
    return DatasetService()

def get_overlay_service(context):
    '''Get the context's overlay service'''
    o = context.getService('imagej.data.display.OverlayService')
    class OverlayService(object):
        def __init__(self, o=o):
            self.o = o
            
        getOverlays = J.make_method("getOverlays", "()Ljava/util/List;",
                                    fn_post_process=J.get_collection_wrapper)
        getDisplayOverlays = J.make_method(
            "getOverlays",
            "(Limagej/data/display/ImageDisplay;)Ljava/util/List;",
            fn_post_process=J.get_collection_wrapper)
        addOverlays = J.make_method(
            "addOverlays", 
            "(Limagej/data/display/ImageDisplay;Ljava/util/List;)V")
        removeOverlay = J.make_method(
            "removeOverlay",
            "(Limagej/data/display/ImageDisplay;Limagej/data/overlay/Overlay;)V")
        getSelectionBounds = J.make_method(
            "getSelectionBounds",
            "(Limagej/data/display/ImageDisplay;)Limagej/util/RealRect;")
    return OverlayService()

def select_overlay(display, overlay, select=True):
    '''Select or deselect an overlay
    
    display - the overlay's display
    
    overlay - the overlay to select
    '''
    for view in J.get_collection_wrapper(display, fn_wrapper = wrap_data_view):
        if J.call(overlay, "equals", "(Ljava/lang/Object;)Z", view.getData()):
            view.setSelected(select)
            break
    else:
        logger.info("Failed to select overlay")

class Axes(object):
    '''Represents the net.imglib2.img.Axes enum'''
    
    def get_named_axis(self, axis_name):
        return J.get_static_field("net/imglib2/meta/Axes", axis_name, 
                                  "Lnet/imglib2/meta/Axes;")
    @property
    def X(self):
        return self.get_named_axis("X")
    
    @property
    def Y(self):
        return self.get_named_axis("Y")
        
    @property
    def CHANNEL(self):
        return self.get_named_axis("CHANNEL")
    
def create_dataset(context, pixel_data, name = None, axes = None):
    '''Create a dataset from a numpy array
    
    pixel_data - numpy array where index 0 is the I or Y axis, index 1 is the
                 J or X axis and index 2, if it exists, is the channel axis.
                 
    name - optional name for the dataset
    '''
    dataset_service = get_dataset_service(context)
    if axes is None:
        if pixel_data.ndim == 2:
            axes = [Axes().X, Axes().Y]
            pixel_data = pixel_data.transpose((1,0))
        else:
            axes = [Axes().X, Axes().Y, Axes().CHANNEL]
            pixel_data = pixel_data.transpose((1,0,2))
    #
    # Create a dataset of the correct shape, with the correct axes.
    # We make a 64-bit floating point image.
    #
    dataset = dataset_service.create1(
        np.array(pixel_data.shape), name, axes, 64, True, True)
    imgplus = dataset.getImgPlus()
    #
    # Now use a copying utility to fill the imgplus with array data
    #
    strides = np.cumprod([1]+ list(pixel_data.shape[:0:-1]))[::-1]
    J.static_call("net/imglib2/util/ImgUtil", "copy",
                  "([DI[ILnet/imglib2/img/Img;)V",
                  pixel_data.flatten(), 0, strides, imgplus)
    return dataset

def make_bit_img(shape):
    '''Make an imglib img of BitType with the given shape
    
    shape - a sequence of image dimensions
    '''
    imgFactory = J.make_instance(
        "net/imglib2/img/planar/PlanarImgFactory", "()V")
    bit_type = J.make_instance("net/imglib2/type/logic/BitType", "()V")
    img = J.call(
        imgFactory, "create", 
        "([JLnet/imglib2/type/NativeType;)Lnet/imglib2/img/planar/PlanarImg;",
        np.array(shape), bit_type)
    return img
    
def create_overlay(context, mask):
    '''Create a bitmask overlay from a numpy boolean array
    
    mask - boolean numpy array organized as i,j = y,x
    '''
    assert mask.ndim == 2
    mask = mask.transpose()
    strides = np.array([mask.shape[1], 1], int)
    img = make_bit_img(mask.shape)
    
    J.static_call("net/imglib2/util/ImgUtil", 
                  "copy", "([ZI[ILnet/imglib2/img/Img;)V",
                  mask.flatten(), 0, strides, img)
    roi = J.make_instance(
        "net/imglib2/roi/BinaryMaskRegionOfInterest",
        "(Lnet/imglib2/img/Img;)V", img)
    overlay = J.make_instance(
        "imagej/data/overlay/BinaryMaskOverlay",
        "(Lorg/scijava/Context;Lnet/imglib2/roi/BinaryMaskRegionOfInterest;)V", 
        context.getContext(), roi)
    return overlay

def create_mask(display):
    '''Create a binary mask from a sequence of overlays
    
    display - an image display
    
    returns a binary mask
    '''
    jmask = J.static_call(
        "org/cellprofiler/ijutils/OverlayUtils",
        "extractMask",
        "(Limagej/data/display/ImageDisplay;)Lnet/imglib2/img/Img;",
        display.o)
    if jmask is None:
        return None
    return get_bit_data(jmask)

def wrap_data_view(view):
    class DataView(object):
        def __init__(self, o=view):
            self.o = o
        isCompatible = J.make_method("isCompatible", "(Limagej/data/Data;)Z")
        initialize = J.make_method("initialize", "(Limagej/data/Data;)V")
        getData = J.make_method("getData", "()Limagej/data/Data;")
        getPlanePosition = J.make_method(
            "getPlanePosition", "()Limagej/data/Position;")
        setSelected = J.make_method("setSelected", "(Z)V")
        isSelected = J.make_method("isSelected", "()Z")
        getPreferredWidth = J.make_method("getPreferredWidth", "()I")
        getPreferredHeight = J.make_method("getPreferredHeight", "()I")
        update = J.make_method("update", "()V")
        rebuild = J.make_method("rebuild", "()V")
        dispose = J.make_method("dispose", "()V")
    return DataView()

def calculate_transpose(actual_axes, desired_axes=None):
    '''Calculate the transpose tuple that converts the actual orientation to the desired
    
    actual_axes - a list of the AxisType arguments as fetched from
                  a display, ImgPlus, view or overlay
                  
    desired_axes - the desired orientation. By default, this is i,j = Y, X
    '''
    if desired_axes is None:
        desired_axes = [ Axes().Y, Axes().X]
        if len(actual_axes) > 2:
            desired_axes.append(Axes().CHANNEL)
    transpose = []
    for axis in desired_axes:
        matches = [i for i, actual_axis in enumerate(actual_axes)
                   if J.call(actual_axis, "equals", 
                             "(Ljava/lang/Object;)Z", axis)]
        if len(matches) != 1:
            raise ValueError("No match for %s axis" % J.to_string(axis))
        transpose.append(matches[0])
    return transpose

def wrap_dataset(dataset):
    
    class Dataset(object):
        def __init__(self, o=dataset):
            self.o = o
        getImgPlus = J.make_method("getImgPlus", "()Lnet/imglib2/img/ImgPlus;")
        setImgPlus = J.make_method("setImgPlus","(Lnet/imglib2/img/ImgPlus;)V")
        getAxes = J.make_method("getAxes","()[Lnet/imglib2/img/AxisType;")
        getType = J.make_method("getType", "()Lnet/imglib2/type/numeric/RealType;")
        isSigned = J.make_method("isSigned", "()Z")
        isInteger = J.make_method("isInteger", "()Z")
        getName = J.make_method("getName", "()Ljava/lang/String;")
        setName = J.make_method("setName","(Ljava/lang/String;)V")
        calibration = J.make_method("calibration", "(I)D")
        setCalibration = J.make_method("setCalibration", "(DI)V")
        def get_pixel_data(self, axes = None):
            imgplus = self.getImgPlus()
            pixel_data = get_pixel_data(imgplus)
            script = """
            var result = java.util.ArrayList();
            for (i=0;i<imgplus.numDimensions();i++) result.add(imgplus.axis(i));
            result"""
            inv_axes = J.run_script(script, dict(imgplus=imgplus))
            inv_axes = list(J.iterate_collection(inv_axes))
            transpose = calculate_transpose(inv_axes, axes)
            return pixel_data.transpose(transpose)
    return Dataset()

def get_pixel_data(img):
    '''Get the pixel data from an image'''
    interval = wrap_interval(img)
    dims = interval.dimensions()
    #
    # Make a Java double array
    #
    a = np.zeros(np.prod(dims), np.float64)
    ja = J.get_env().make_double_array(np.ascontiguousarray(a))
    strides = np.cumprod([1] + dims[:0:-1]).astype(int)[::-1]
    J.static_call("net/imglib2/util/ImgUtil", "copy", 
                  "(Lnet/imglib2/img/Img;[DI[I)V",
                  img, ja, 0, strides)
    a = J.get_env().get_double_array_elements(ja)
    a.shape = dims
    return a
        
def get_bit_data(img):
    '''Get the pixel data from a binary mask
    
    returns a Numpy array of boolean type
    '''
    interval = wrap_interval(img)
    dims = interval.dimensions()
    #
    # Make a Java boolean array
    #
    a = np.zeros(np.prod(dims), np.float64)
    ja = J.get_env().make_boolean_array(np.ascontiguousarray(a))
    strides = np.cumprod([1] + dims[:0:-1]).astype(int)[::-1]
    J.static_call("net/imglib2/util/ImgUtil", "copy", 
                  "(Lnet/imglib2/img/Img;[ZI[I)V",
                  img, ja, 0, strides)
    a = J.get_env().get_boolean_array_elements(ja)
    a.shape = dims
    return a

def wrap_interval(interval):
    '''Return a class wrapper around a net.imglib2.Interval
    
    Provides additional methods if it's a calibrated interval.
    '''
    class Interval(object):
        def __init__(self, o = interval):
            self.o = o
            
        numDimensions = J.make_method("numDimensions", "()I")
        min1D = J.make_method("min", "(I)J", 
                              "Retrieve the minimum coordinate for a single dimension")
        max1D = J.make_method("max", "(I)J",
                              "Retrieve the maximum coordinate for a single dimension")
        dimension = J.make_method("dimension", "(I)J",
                                  "Retrieve the number of pixels in the given dimension")
        def minND(self):
            return [self.min1D(i) for i in range(self.numDimensions())]
        
        def maxND(self):
            return [self.max1D(i) for i in range(self.numDimensions())]
        
        def dimensions(self):
            return [self.dimension(i) for i in range(self.numDimensions())]
        #
        # # # # # # # # # # # # # # #
        #
        # Calibrated interval methods
        #
        getAxes = J.make_method("getAxes", "()L[net.imglib2.meta.AxisType;")
        #
        # minimum and maximum by axis
        #
        def minAx(self, axis):
            '''Get the minimum of the interval along the given axis'''
            axes = self.getAxes()
            idx = axes.index(axis)
            return self.min1D(idx)
        
        def maxAx(self, axis):
            '''Get the maximum of the interval along the given axis'''
            axes = self.getAxes()
            idx = axes.index(axis)
            return self.max1D(idx)
        
    return Interval()

def get_script_service(context):
    '''Get the script service for a given context
    
    context - the instance of ImageJ created by create_context
    
    returns a script service
    '''
    o = context.getService('imagej.script.ScriptService')
    class ScriptService(object):
        def __init__(self, o=o):
            self.o = o
        
        getPluginService = J.make_method(
            "getPluginService", "()Lorg/scijava/plugin/PluginService;")
        getLogService = J.make_method(
            "getLogService", "()Lorg/scijava/log/LogService;")
        getIndex = J.make_method(
            "getIndex", "()Limagej/script/ScriptLanguageIndex;")
        getLanguages = J.make_method(
            "getLanguages", "()Ljava/util/List;",
            doc = "Return the script engine factories supported by this service",
            fn_post_process = lambda jlangs: [
                wrap_script_engine_factory(o) 
                for o in J.iterate_collection(jlangs)])
        getByFileExtension = J.make_method(
            "getByFileExtension", 
            "(Ljava/lang/String;)Ljavax/script/ScriptEngineFactory;",
            fn_post_process=wrap_script_engine_factory)
        getByName = J.make_method(
            "getByName", 
            "(Ljava/lang/String;)Ljavax/script/ScriptEngineFactory;",
            fn_post_process=wrap_script_engine_factory)
    return ScriptService()
        
def wrap_script_engine_factory(o):
    '''Wrap a javax.script.ScriptEngineFactory object'''
    class ScriptEngineFactory(object):
        def __init__(self, o=o):
            self.o = o
            
        getEngineName = J.make_method(
            "getEngineName", "()Ljava/lang/String;",
            doc = """Returns the full  name of the ScriptEngine.
            
            For instance an implementation based on the 
            Mozilla Rhino Javascript engine  might return 
            Rhino Mozilla Javascript Engine.""")
        getEngineVersion = J.make_method(
            "getEngineVersion", "()Ljava/lang/String;")
        getExtensions = J.make_method(
            "getExtensions", "()Ljava/util/List;",
            doc= "Get the list of supported filename extensions")
        getMimeTypes = J.make_method(
            "getMimeTypes", "()Ljava/util/List;")
        getNames = J.make_method(
            "getNames", "()Ljava/util/List;")
        getLanguageName = J.make_method(
            "getLanguageName", "()Ljava/lang/String;")
        getLanguageVersion = J.make_method(
            "getLanguageVersion", "()Ljava/lang/String;")
        getParameter = J.make_method(
            "getParameter", "(Ljava/lang/String;)Ljava/lang/Object;")
        getMethodCallSyntax = J.make_method(
            "getMethodCallSyntax", 
            "(Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;)"
            "Ljava/lang/String;")
        getOutputStatement = J.make_method(
            "getOutputStatement", 
            "(Ljava/lang/String;)Ljava/lang/String;")
        getProgram = J.make_method(
            "getProgram",
            "([Ljava/lang/String;)Ljava/lang/String;")
        getScriptEngine = J.make_method(
            "getScriptEngine", 
            "()Ljavax/script/ScriptEngine;",
            fn_post_process=wrap_script_engine)
    return ScriptEngineFactory()
        
def wrap_script_engine(o):
    '''Return a class wrapper for javax.script.ScriptEngine'''
    klass = 'javax/script/ScriptEngine'
    class ScriptEngine(object):
        def __init__(self, o=o):
            self.o = o
            
        ARGV = J.get_static_field(klass, "ARGV", "Ljava/lang/String;")
        FILENAME = J.get_static_field(klass, "FILENAME", "Ljava/lang/String;")
        ENGINE = J.get_static_field(klass, "ENGINE", "Ljava/lang/String;")
        ENGINE_VERSION = J.get_static_field(
            klass, "ENGINE_VERSION", "Ljava/lang/String;")
        NAME = J.get_static_field(klass, "NAME", "Ljava/lang/String;")
        LANGUAGE = J.get_static_field(klass, "LANGUAGE", "Ljava/lang/String;")
        LANGUAGE_VERSION = J.get_static_field(
            klass, "LANGUAGE_VERSION", "Ljava/lang/String;")
        evalSSC = J.make_method(
            "eval", 
            "(Ljava/lang/String;Ljavax/scriptScriptContext;)Ljava/lang/Object;",
            doc = """Evaluate a script within a context
            
            script - the script to run
            
            script_context - The context describing the operational scope
                             during the evaluation.""")
        evalRSC = J.make_method(
            "eval",
            "(Ljava/io/Reader;Ljavax/scriptScriptContext;)Ljava/lang/Object;",
            doc = """Evaluate a script within a context
            
            reader - read the script from this reader
            
            script_context - The context describing the operational scope
                             during the evaluation.""")
            
        evalS = J.make_method(
            "eval",
            "(Ljava/lang/String;)Ljava/lang/Object;",
            doc = """Evaluate a script within the engine's default context
            
            script - script to evaluate
            """)
        evalR = J.make_method(
            "eval",
            "(Ljava/io/Reader;)Ljava/lang/Object;",
            doc = """Evaluate a script within the engine's default context
            
            reader - read the script from here
            """)
        evalSB = J.make_method(
            "eval",
            "(Ljava/lang/String;Ljavax/script/Bindings;)Ljava/lang/Object;",
            doc = """Evaluate the script using the bindings as the ENGINE_SCOPE
            
            script - the script to be run
            
            bindings - bindings of values to variables which are combined with
                       the non ENGINE_SCOPE bindings of the default context
                       to provide an execution scope.""")
        evalRB = J.make_method(
            "eval",
            "(Ljava/io/Reader;Ljavax/script/Bindings;)Ljava/lang/Object;",
            doc = """Evaluate the script using the bindings as the ENGINE_SCOPE
            
            reader- read the script from here
            
            bindings - bindings of values to variables which are combined with
                       the non ENGINE_SCOPE bindings of the default context
                       to provide an execution scope.""")
        put = J.make_method(
            "put", "(Ljava/lang/String;Ljava/lang/Object;)V",
            doc = """Set the value for some script engine key
            
            For non-keywords, this generally adds a key/value binding to the default
            ENGINE_SCOPE for the script engine.
            
            key - name of the value to add
            
            value - the value to be given to the key
            """)
        get = J.make_method(
            "get", "(Ljava/lang/String;)Ljava/lang/Object;",
            doc = """Get a value set on the engine's state
            
            key - the key to look up
            """)
        ENGINE_SCOPE = J.get_static_field("javax/script/ScriptContext",
                                          "ENGINE_SCOPE", "I")
        GLOBAL_SCOPE = J.get_static_field("javax/script/ScriptContext",
                                          "GLOBAL_SCOPE", "I")
        getBindings = J.make_method(
            "getBindings", "(I)Ljavax/script/Bindings;",
            doc = """Returns a scope of named values.
            
            scope - either ScriptContext.ENGINE_SCOPE to get the values set on
                    this engine or ScriptContext.GLOBAL_SCOPE to get the values
                    set by a ScriptEngineManager.
            """)
        setBindings = J.make_method(
            "setBindings", "(Ljavax/script/Bindings;I)V",
            doc = """Sets the bindings to be used for the engine or global scope
            
            bindings - the bindings to use
            
            scope - ENGINE_SCOPE to set the script engine's bindings or
                    GLOBAL_SCOPE to set the scope at the manager level.
            """)
        createBindings = J.make_method(
            "createBindings", "()Ljavax/script/Bindings;",
            doc = """Return a bindings instance appropriate for this engine""")
        getContext = J.make_method(
            "getContext", "()Ljavax/script/ScriptContext;",
            doc = """Return the default ScriptContext for this engine""")
        setContext = J.make_method(
            "setContext", "(Ljavax/script/ScriptContext;)V",
            doc = """Set the default ScriptContext for this engine""")
        getFactory = J.make_method(
            "getFactory", "()Ljavax/script/ScriptEngineFactory;",
            doc = "Get this engine's factory")
    return ScriptEngine()

def get_ui_service(context):
    '''Return a wrapped imagej.ui.UIService for this context'''
    ui_service = context.getService('imagej.ui.UIService')
    if ui_service is None:
        return None
    class UIService(object):
        def __init__(self):
            self.o = ui_service
        def createUI(self):
            '''Create the ImageJ UI'''
            #
            # This has to be done via a future in order
            # for CP to run the Mac event loop.
            #
            r = J.run_script(
                """new java.lang.Runnable() {
                    run:function() {
                        uiService.showUI();
                    }
                };
                """, dict(uiService=self.o))
            J.execute_runnable_in_main_thread(r, True)
        def createUIS(self, arg):
            '''Create the ImageJ UI with a string argument'''
            r = J.run_script(
                """new java.lang.Runnable() {
                    run:function() {
                        uiService.showUI(arg);
                    }
                };
                """, dict(uiService=self.o, arg=arg))
            J.execute_runnable_in_main_thread(r, True)
        isVisible = J.make_method("isVisible", "()Z")
        getDefaultUI = J.make_method(
            "getDefaultUI", 
            "()Limagej/ui/UserInterface;",
            fn_post_process=wrap_user_interface)
        getUI = J.make_method(
            "getUI", "(Ljava/lang/String;)Limagej/ui/UserInterface;",
            fn_post_process=wrap_user_interface)
        
    return UIService()
    
def update_never_remind():
    '''Tell ImageJ never to remind us of updates
    
    Not as harsh as it sounds - this is done with headless preferences
    which go to /dev/null.
    '''
    never = J.get_static_field("java/lang/Long", "MAX_VALUE", "J")
    J.static_call("imagej/updater/core/UpToDate", 
                  "setLatestNag", "(J)V", never)
    
def wrap_user_interface(o):
    '''Return a wrapped imagej.ui.UserInterface'''
    class UserInterface(object):
        def __init__(self):
            self.o = o
        show = J.make_method("show", "()V")
        isVisible = J.make_method("isVisible", "()Z")
        
    return UserInterface()

if __name__=="__main__":
    jar_dir = os.path.join(os.path.split(__file__)[0], "jars")
    classpath = os.pathsep.join([
        os.path.join(jar_dir, filename) for filename in os.listdir(jar_dir)
        if filename.endswith(".jar")])
    J.start_vm(["-Djava.class.path="+classpath])
    my_context = create_context(REQUIRED_SERVICES)
    module_service = get_module_service(my_context)
    module_infos = module_service.getModules()
    for module_info in module_infos:
        print J.to_string(module_info.o)
