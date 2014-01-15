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

import gtk, pango
import os
import sys

class FolderChooserComboBox(gtk.ComboBox):

    def __init__(self, add_empty_entry=False):
        gtk.ComboBox.__init__(self)
        
        self.add_empty_entry = add_empty_entry
        
        # setup combobox_archive       name    pixbuf     indent path
        self.liststore = gtk.ListStore(str, gtk.gdk.Pixbuf, str, str)        
        self.COL_NAME = 0
        self.COL_PIXBUF = 1
        self.COL_PATH = 3
        self.set_model(self.liststore)

        cell = gtk.CellRendererText()
        self.pack_start(cell, False)
        self.add_attribute(cell, 'text', 2)
        
        cell = gtk.CellRendererPixbuf()
        cell.set_property('xpad', 5)
        self.pack_start(cell, False)
        self.add_attribute(cell, 'pixbuf', self.COL_PIXBUF)               
        
        cell = gtk.CellRendererText()
        cell.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', self.COL_NAME)

     
    def __separator(self, model, iter, data=None):
        return (model.get_value(iter, self.COL_NAME) == '-')
    
    def get_active_path(self):
        iter = self.get_active_iter()
        if iter:
            return self.liststore.get_value(iter, self.COL_PATH)
        else:
            return ""
        
    def fill(self, path):
        ENCODING = sys.stdout.encoding or sys.getfilesystemencoding()
        image = gtk.icon_theme_get_default().load_icon('folder', 16, gtk.ICON_LOOKUP_USE_BUILTIN)

        self.liststore.clear()
        
        if self.add_empty_entry:
            self.liststore.append(["Nicht archivieren", None, "", ""])
            self.liststore.append(["-", None, "", ""])
            self.set_row_separator_func(self.__separator)
        
        # root folder
        self.liststore.append([path.split('/')[-1], image, "", path.encode(ENCODING)])
        
        fill_up = "—"
        for root, dirs, files in os.walk(path.encode(ENCODING)):
            directory = root[len(path)+1:].split('/')

            if not directory[0]: continue
                            
            self.liststore.append([directory[-1], image, fill_up * len(directory), root])
