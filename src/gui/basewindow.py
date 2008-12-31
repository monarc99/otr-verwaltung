#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import re

try:
    import gtk
    import pygtk
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)
  
   
class BaseWindow:
    
    def __path(self, filename):
        return os.path.join(sys.path[0], os.path.join("gui", filename))
        
    def __init__(self, builder, name, widgets=None, parent=None): 
        """ Implements a gtk.Window/gtk.Dialog built by a gtk.Builder.
              builder - a gtk.Builder object. Can be created by create_builder()
              name - name of window, name of builder file
              widgets (optional) - list of widgets to be loaded
              parent (optional) - a parent window classs        
        """
                          
        # Get window from builder
        self.__window = builder.get_object(name)
        if parent != None:
            self.__window.set_transient_for(parent.get_window())
        
        # Get widgets from builder
        self.__widgets = {}
        if widgets != None:
            for widget_name in widgets:
                self.__widgets[widget_name] = builder.get_object(widget_name)
                    
        # connect signals for "parent" class
        builder.connect_signals(self)

    def create_builder(self, files):
        """ Initializes a new gtk.Builder.
            files - String of file/List of files. """
                
        builder = gtk.Builder()
        if type(files)==str:
            builder.add_from_file(self.__path(files))
        elif type(files)==list:
            for builder_file in files:
                builder.add_from_file(self.__path(builder_file))
        else:
            raise AttributeError, "Files has to be a string or a list."
        
        return builder    
                       
    # Convenience methods
    def get_widget(self, widget_name):
        """ Get a widget by name. """
        return self.__widgets[widget_name]
    
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
            raise Exception, "Cannot call run() on %s. \
You have to use a gtk.Dialog." % type(self.__window)
