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

from os import mkdir
from os.path import dirname, join, isdir, splitext
import re

from otrverwaltung import fileoperations
from otrverwaltung.actions.baseaction import BaseAction

class Delete(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filenames, trash_otrkeys, trash_avis):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.__gui.question_box(message + "in den Müll verschoben werden?"):
            self.update_list = True
            for f in filenames:
                if f.endswith("otrkey"):
                    fileoperations.move_file(f, trash_otrkeys)
                else:
                    fileoperations.move_file(f, trash_avis)

class RealDelete(BaseAction):
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui            

    def do(self, filenames):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.__gui.question_box(message + "endgültig gelöscht werden?"):
            for f in filenames:           
                fileoperations.remove_file(f)

class Restore(BaseAction):
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, filenames, new_otrkeys_folder, uncut_videos_folder, cut_videos_folder, uncut_video):
        for f in filenames:
            if f.endswith("otrkey"):
                fileoperations.move_file(f, new_otrkeys_folder)
            elif uncut_video.match(f):
                fileoperations.move_file(f, uncut_videos_folder)
            else:
                fileoperations.move_file(f, cut_videos_folder)
    
class Rename(BaseAction):
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui
        
    def do(self, filenames):
        response, new_names = self.__gui.dialog_rename.init_and_run("Umbenennen", filenames)  
                
        if response:
            for f in filenames:
                extension = splitext(f)[1]

                new_name = new_names[f]
                new_name = join(dirname(f), new_name.replace('/', '_'))
                
                if f.endswith(extension) and not new_name.endswith(extension):
                    new_name += extension
                
                fileoperations.rename_file(f, new_name)
        else:
            self.update_list = False

class NewFolder(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui
        
    def do(self, filename):
        if isdir(filename):
            dirname = filename
        else:
            dirname = dirname(filename)

        response, new_names = self.__gui.dialog_rename.init_and_run("Neuer Ordner", ["Neuer Ordner"])

        if response and new_names["Neuer Ordner"] != "":            
            self.update_list = True
            mkdir(join(dirname, new_names["Neuer Ordner"]))
