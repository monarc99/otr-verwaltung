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

from os.path import join, dirname, splitext
from os import listdir

from otrverwaltung import fileoperations
from otrverwaltung.actions.baseaction import BaseAction

class Archive(BaseAction):
   
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self, filenames):
        # widgets
        archive_directory = self.__app.config.get('general', 'folder_archive')
        dialog = self.__gui.dialog_archive

        result, renamed_filenames, archive_to = dialog.run(filenames, archive_directory)            
            
        if result:
            self.update_list = True
            
            for original, new_name in renamed_filenames.iteritems():
                # add extension to renamed file if needed
                extension = splitext(original)[1]                                                
                if not new_name.endswith(extension):
                    new_name += extension

                new_name = join(dirname(original), new_name.replace('/', '_'))
               
                if new_name != original:
                    fileoperations.rename_file(original, new_name)
    
                fileoperations.move_file(new_name, archive_to)
                    
        dialog.hide()
