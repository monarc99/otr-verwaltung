#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import basename

import gtk

from basewindow import BaseWindow

class DialogArchive(BaseWindow):
    
    def __init__(self, parent):                    
        BaseWindow.__init__(self, "dialog_archive", parent)
        
        self.__setup_widgets()
        
    def __setup_widgets(self):
        # create folder treestore
        treeview = self.get_widget('treeviewFolders')
        treeview.set_model(gtk.TreeStore(str))

        cell_renderer_folder_name = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn(None, cell_renderer_folder_name, text = 0)
        tvcolumn.set_cell_data_func(cell_renderer_folder_name, self.folder_name)        
        
        treeview.append_column(tvcolumn)

        # create files-rename liststore
        treeview = self.get_widget('treeviewFilesRename')
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
        iter = self.get_widget('treeviewFilesRename').get_model().append([filename])    
        return iter
        
    def append_row_treeviewFolders(self, parent, filename):   
        iter = self.get_widget('treeviewFolders').get_model().append(parent, [filename])
        return iter
        
    ###
    ### Signal handlers
    ###    
    
    def folder_name(self, column, cell, model, iter):
        cell.set_property('text', basename(model.get_value(iter, 0)))
    
    def new_name_cell_edited(self, cell, path, new_text, model):
        # update new name of file in model
        model[path][0] = new_text
