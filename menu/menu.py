from time import sleep
debug = True

import logging

def to_be_foreground(func):
    def wrapper(self, *args, **kwargs):
        if self.in_foreground:
            return func(self, *args, **kwargs)
        else:
            return False
    return wrapper

#def menu_name(func):
#    def wrapper(self, *args, **kwargs):
#        print self.name+":",
#        return func(self, *args, **kwargs)
#    return wrapper

class Menu():
    contents = []
    pointer = 0
    display_callback = None
    in_background = True
    in_foreground = False
    exit_flag = False
    name = ""


    def __init__(self, contents, screen, listener, name):
        self.generate_keymap()
        self.name = name
        self.listener = listener
        self.contents = contents
        self.process_contents()
        self.screen = screen
        self.display_callback = screen.display_data
        self.set_display_callback(self.display_callback)

    def to_foreground(self):
        logging.info("menu {0} enabled".format(self.name))    
        self.in_background = True
        self.in_foreground = True
        self.refresh()
        self.set_keymap()

    @to_be_foreground
    def to_background(self):
        self.in_foreground = False
        logging.info("menu {0} disabled".format(self.name))    

    def activate(self):
        logging.info("menu {0} activated".format(self.name))    
        self.to_foreground()
        while self.in_background:
            sleep(1)
        logging.debug(self.name+" exited")
        return True

    def deactivate(self):
        logging.info("menu {0} deactivated".format(self.name))    
        self.to_background()
        self.in_background = False

    def print_contents(self):
        logging.info(self.contents)

    def print_name(self):
        logging.info("Active menu is {0}".format(self.name))    

    @to_be_foreground
    def move_down(self):
        if self.pointer < (len(self.contents)-1):
            logging.debug("moved down")
            self.pointer += 1  
            self.refresh()    
            return True
        else: 
            return False

    @to_be_foreground
    def move_up(self):
        if self.pointer != 0:
            logging.debug("moved up")
            self.pointer -= 1
            self.refresh()
            return True
        else: 
            return False

    @to_be_foreground
    def select_element(self):
        logging.debug("element selected")
        self.to_background()
        if len(self.contents) == 0:
            self.deactivate()
        else:
            self.contents[self.pointer][1]()
        self.set_keymap()        
        if self.in_background:
            self.to_foreground()

    def generate_keymap(self):
        keymap = {
            "KEY_LEFT":lambda: self.deactivate(),
            "KEY_RIGHT":lambda: self.print_name(),
            "KEY_UP":lambda: self.move_up(),
            "KEY_DOWN":lambda: self.move_down(),
            "KEY_KPENTER":lambda: self.select_element(),
            "KEY_ENTER":lambda: self.select_element()
            }
        self.keymap = keymap

    def process_contents(self):
        for entry in self.contents:
            if entry[1] == "exit":
                entry[1] = self.deactivate
        logging.debug("{0}: menu contents processed".format(self.name))

    @to_be_foreground
    def set_keymap(self):
        self.generate_keymap()
        self.listener.stop_listen()
        self.listener.keymap.clear()
        self.listener.keymap = self.keymap
        self.listener.listen_direct()

    @to_be_foreground
    def get_displayed_data(self):
        if len(self.contents) == 0:
            return ("No menu entries", " ")
        elif len(self.contents) == 1:
            return ("*"+self.contents[0][0], " ")
        elif self.pointer < (len(self.contents)-1):
            return ("*"+self.contents[self.pointer][0], " "+self.contents[self.pointer+1][0])
        else:
            return (" "+self.contents[self.pointer-1][0], "*"+self.contents[self.pointer][0])

    @to_be_foreground
    def refresh(self):
        logging.debug("{0}: refreshed data on display".format(self.name))
        self.display_callback(*self.get_displayed_data())

    def set_display_callback(self, callback):
        logging.debug("{0}: display callback set".format(self.name))
        self.display_callback = callback

