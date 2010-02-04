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

from os.path import basename

import gtk

from otrverwaltung import path

class ArchiveDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "ArchiveDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)

        # create folder treestore
        treeview = self.builder.get_object('treeviewFolders')
        treeview.set_model(gtk.TreeStore(str))

        cell_renderer_folder_name = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn(None, cell_renderer_folder_name, text = 0)
        tvcolumn.set_cell_data_func(cell_renderer_folder_name, self.folder_name)        
        
        treeview.append_column(tvcolumn)

        # create files-rename liststore
        treeview = self.builder.get_object('treeviewFilesRename')
        treeview.set_model(gtk.ListStore(str))
        
        cell_renderer_new = gtk.CellRendererText()
        cell_renderer_new.set_property('editable', True)
        cell_renderer_new.connect('edited', self.new_name_cell_edited, treeview.get_model())
        tvcolumn_new = gtk.TreeViewColumn("Neuer Name (Doppelklick zum Bearbeiten):", cell_renderer_new, text=0)     
        
        treeview.append_column(tvcolumn_new)
        
        selection = treeview.get_selection()    
    
    ###
    ### Convenience methods
    ###    
  
    def append_row_treeviewFilesRename(self, filename):
        iter = self.builder.get_object('treeviewFilesRename').get_model().append([filename])    
        return iter
        
    def append_row_treeviewFolders(self, parent, filename):   
        iter = self.builder.get_object('treeviewFolders').get_model().append(parent, [filename])
        return iter
        
    ###
    ### Signal handlers
    ###    
    
    def folder_name(self, column, cell, model, iter):
        cell.set_property('text', basename(model.get_value(iter, 0)))
    
    def new_name_cell_edited(self, cell, path, new_text, model):
        # update new name of file in model
        model[path][0] = new_text
        
def NewArchiveDialog():
    glade_filename = path.getdatapath('ui', 'ArchiveDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("archive_dialog")
        
    return dialog
