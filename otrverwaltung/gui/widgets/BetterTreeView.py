# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import gtk

class BetterTreeView(gtk.TreeView):

    def __init__(self, columns):
        """ columns is a list of tuples: 
                (column_name, None or an attribute name of object, None or a method callback) """
        
        gtk.TreeView.__init__(self)
        
        self.liststore = gtk.ListStore(object)        
        self.set_model(self.liststore)
            
        # append the columns
        for text, attribute, callback in columns:                  
            renderer_left = gtk.CellRendererText()
            renderer_left.set_property('xalign', 0.0) 
            col = gtk.TreeViewColumn(text, renderer_left)

            if callback:
                col.set_cell_data_func(renderer_left, callback)            
            else:
                col.set_cell_data_func(renderer_left, self.__standard_callback, attribute)                   

            col.set_resizable(True)        
            self.append_column(col)
       
    def __standard_callback(self, column, cell, model, iter, attribute):
        obj = model.get_value(iter, 0)
        cell.set_property('text', getattr(obj, attribute))
    
    def add_objects(self, *args):
        for obj in args:
            obj.update_view = self.__update_view
            self.liststore.append([obj])
        
    def remove_objects(self, *args):
        for row in self.liststore:
            if row[0] in args:
                del self.liststore[row.iter]
