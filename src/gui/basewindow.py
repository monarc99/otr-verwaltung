#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

import gtk
   
class BaseWindow:
    
    def __init__(self, name, parent=None): 
        """ Implements a gtk.Window/gtk.Dialog built by a gtk.Builder.
              builder_filename - 
              name - name of window, name of builder file
              parent (optional) - a parent window class """
               
        filename = os.path.join(sys.path[0], os.path.join("gui", name + ".glade"))
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(filename)
                          
        # Get window from builder
        self.__window = self.get_widget(name)
        if parent:
            self.__window.set_transient_for(parent.get_window())
                           
        # connect signals for "parent" class
        self.__builder.connect_signals(self)
                                
    # Convenience methods
    def get_widget(self, widget_name):
        """ Get a widget by name. """
        return self.__builder.get_object(widget_name)
    
    def create_widget(self, widget_name, widget):
        self.__widgets[widget_name] = widget
        return widget 
    
    def get_window(self):
        """ Get the gtk.Window/gtk.Dialog. """
        return self.__window  

    def show(self):
        """ Shows the gtk.Window/gtk.Dialog. """
        self.__window.show()
        
    def hide(self):
        """ Hides the gtk.Window/gtk.Dialog. """
        self.__window.hide()
        
    def run(self):
        """ Runs the gtk.Dialog and returns the response id. """
        if type(self.__window) == gtk.Dialog:
            return self.__window.run()
        else:
            raise Exception, "Cannot call run() on %s. You have to use a gtk.Dialog." % type(self.__window)
