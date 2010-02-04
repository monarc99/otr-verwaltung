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

from gtk import RESPONSE_OK
from os.path import basename, join, isdir, dirname, splitext
from os import listdir

from otrverwaltung import fileoperations
from otrverwaltung.actions.baseaction import BaseAction

class Archive(BaseAction):
   
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filenames, folder):       
        # widgets
        dialog = self.__gui.dialog_archive
       
        treeview_files = self.__gui.dialog_archive.builder.get_object('treeviewFilesRename')
        treestore_files = treeview_files.get_model()
        treeview_folders = self.__gui.dialog_archive.builder.get_object('treeviewFolders')
        treestore_folders = treeview_folders.get_model()
                
        self.__gui.dialog_archive.builder.get_object('labelFiles').set_text("%s Datei(en) zum Archivieren ausgewählt." % len(filenames))
        
        # fill rename tree
        dict_files_iter = {}        
        for f in filenames:
            iter = self.__gui.dialog_archive.append_row_treeviewFilesRename(basename(f))
            # keep relation between filename and iter
            dict_files_iter[f] = iter
            
        # fill tree of folders
        root = self.__gui.dialog_archive.append_row_treeviewFolders(None, folder)    
        self.tree_folders(root)        
        # select first node
        selection = treeview_folders.get_selection()
        selection.select_path(0)
        
        # expand
        treeview_folders.expand_all()
        
        result = dialog.run()

        if result == RESPONSE_OK:            
            self.update_list = True

            # get selection
            selection = treeview_folders.get_selection()
            (model, iter) = selection.get_selected()
            
            # get target path
            target_folder = model.get_value(iter, 0)
            
            for f in filenames:
                extension = splitext(f)[1]
                
                # get new filename
                new_name = treestore_files.get_value(dict_files_iter[f], 0)
                                
                if not new_name.endswith(extension):
                    new_name += extension

                new_name = join(dirname(f), new_name.replace('/', '_'))
                
                if new_name != f:
                    fileoperations.rename_file(f, new_name)
    
                fileoperations.move_file(new_name, target_folder)                   
                    
        dialog.hide()
                
        # clear treeview and listview
        treestore_folders.clear()
        treestore_files.clear()

    # recursive
    def tree_folders(self, parent):              
        dir = self.__gui.dialog_archive.builder.get_object('treeviewFolders').get_model().get_value(parent, 0)
            
        files = listdir(dir)            

        for file in files:
            full_path = join(dir, file)
            
            if isdir(full_path):                
                iter = self.__gui.dialog_archive.append_row_treeviewFolders(parent, full_path)
                self.tree_folders(iter)
