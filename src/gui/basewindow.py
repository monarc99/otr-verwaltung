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

import gtk

   
class BaseWindow:
    
    def __init__(self, builder_filename, name, parent=None): 
        """ Implements a gtk.Window/gtk.Dialog built by a gtk.Builder.
              builder_filename - 
              name - name of window, name of builder file
              parent (optional) - a parent window class """
               
        filename = os.path.join(sys.path[0], os.path.join("gui", builder_filename))
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
            raise Exception, "Cannot call run() on %s. \
You have to use a gtk.Dialog." % type(self.__window)
