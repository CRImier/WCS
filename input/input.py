from evdev import InputDevice, list_devices, categorize, ecodes
import threading
import time
import os
import importlib
from config_parse import read_config
#TODO: add a function getting all the keys of listener

def to_be_enabled(func):
    """Decorator for KeyListener class. Is used on functions which require enabled KeyListener to be executed. 
       Currently assumes there has been an error and tries to re-enable the listener."""
    def wrapper(self, *args, **kwargs):
        if not self.enabled:
            if not self.enable():
                return None #TODO: think what's appropriate and what are the times something like that might happen
        else:
            return func(self, *args, **kwargs)
    return wrapper

class KeyListener():
    """A class which listens for input device events and calls according callbacks if set"""
    enabled = False
    listening = False
    keymap = {}
    stop_flag = False

    def __init__(self, path=None, name=None, keymap={}):
        """Init function for creating KeyListener object. Checks all the arguments and sets keymap if supplied."""
        if not name and not path: #No necessary arguments supplied
            raise TypeError("Expected at least path or name; got nothing. =(")
        if not path:
            path = get_path_by_name(name)
        if not name:
            name = get_name_by_path(path)
        if not name and not path: #Seems like nothing was found by get_input_devices
            raise IOError("Device not found")
        self.path = path
        self.name = name
        self.set_keymap(keymap)
        self.enable()

    def enable(self):
        """Enables listener - sets all the flags and creates devices. Does not start a listening or a listener thread."""
        #TODO: make it re-check path if name was used for the constructor
        #keep in mind that this will get called every time if there's something wrong
        #and input device file nodes aren't strictly mapped to their names
        #__init__ function remake is needed for this
        if debug: print "enabling listener"
        try:
            self.device = InputDevice(self.path)
        except OSError:
            raise
        try:
            self.device.grab() #Catch exception if device is already grabbed
        except IOError:
            pass
        self.enabled = True
        return True

    @to_be_enabled
    def force_disable(self):
        """Disables listener, is useful when device is unplugged and errors may occur when doing it the right way
           Does not unset flags - assumes that they're already unset."""
        if debug: print "forcefully disabling listener"
        self.stop_listen()
        #Exception possible at this stage if device does not exist anymore
        #Of course, nothing can be done about this =)
        try:
            self.device.ungrab() 
        except IOError:
            pass #Maybe log that device disappeared?
        self.enabled = False

    @to_be_enabled
    def disable(self):
        """Disables listener - makes it stop listening and ungrabs the device"""
        if debug: print "disabling listener"
        self.stop_listen()
        while self.listening:
            if debug: print "still listening"
            time.sleep(0.01)
        self.device.ungrab()
        self.enabled = False

    def set_callback(self, key_name, callback):
        """Sets a single callback of the listener"""
        self.keymap[key_name] = callback

    def remove_callback(self, key_name):
        """Sets a single callback of the listener"""
        self.keymap.remove(key_name)

    def set_keymap(self, keymap):
        """Sets all the callbacks supplied, removing previously set"""
        self.keymap = keymap

    def replace_keymap_entries(self, keymap):
        """Sets all the callbacks supplied, not removing previously set"""
        for key in keymap.keys:
            set_callback(key, keymap[key])

    def clear_keymap(self):
        """Removes all the callbacks set"""
        self.keymap.clear()

    @to_be_enabled
    def event_loop(self):
        """Blocking event loop which just calls supplied callbacks in the keymap."""
        #TODO: describe callback interpretation ways
        self.listening = True
        try:
            for event in self.device.read_loop():
                if self.stop_flag:
                    break
                if event.type == ecodes.EV_KEY:
                    key = ecodes.keys[event.code]
                    value = event.value
                    if value == 0:
                        if debug: print "processing an event: ",
                        if key in self.keymap:
                            if debug: print "event has callback, calling it"
                            self.keymap[key]()
                        else:
                            print ""
        except KeyError as e:
            self.force_disable()
        except IOError as e: 
            if e.errno == 11:
                #Okay, this error sometimes appears out of blue when I press buttons on a keyboard. Moreover, it's uncaught but due to some logic I don't understand yet the whole thing keeps running. I need to research it.
                print("That error again. Need to learn to ignore it somehow.")
        finally:
            self.listening = False

    @to_be_enabled
    def listen(self):
        """Starts event loop in a thread. Nonblocking."""
        if debug: print "started listening"
        self.stop_flag = False
        self.listener_thread = threading.Thread(target = self.event_loop) 
        self.listener_thread.daemon = True
        self.listener_thread.start()
        return True

    @to_be_enabled
    def stop_listen(self):
        self.stop_flag = True
        return True

def get_input_devices():
    """Returns list of all the available InputDevices"""
    return [InputDevice(fn) for fn in list_devices()]

def get_path_by_name(name):
    """Gets HID device path by name, returns None if not found."""
    path = None
    for dev in get_input_devices():
        if dev.name == name:
            path = dev.fn
    return path

def get_name_by_path(path):
    """Gets HID device path by name, returns None if not found."""
    name = None
    for dev in get_input_devices():
        if dev.fn == path:
            name = dev.name
    return name

if "__name__" != "__main__":
    config = read_config()
    try:
        driver_name = config["input"][0]["driver"]
    except:
        driver_name = None
    if driver_name:
        driver_module = importlib.import_module("input.drivers."+driver_name)
        try:
            driver_args = config["input"][0]["driver_args"]
        except KeyError:
            driver_args = []
        try:
            driver_kwargs = config["input"][0]["driver_kwargs"]
        except KeyError:
            driver_kwargs = {}
        driver = driver_module.InputDevice(*driver_args, **driver_kwargs)
        driver.activate()
    try:
        device_name = config["input"][0]["device_name"]
    except:
        device_name = driver.name
    listener = KeyListener(name=device_name)

