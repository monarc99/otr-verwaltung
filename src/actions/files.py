#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import mkdir
from os.path import dirname, join, isdir
import fileoperations

from baseaction import BaseAction

class Delete(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filenames, trash):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.__gui.question_box(message + "in den Müll verschoben werden?"):
            self.update_list = True
            for f in filenames:
                fileoperations.move_file(f, trash)

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

    def do(self, filenames, new_otrkeys_folder):
        for f in filenames:
            fileoperations.move_file(f, new_otrkeys_folder)
    
class Rename(BaseAction):
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui
        
    def do(self, filenames):
        response, new_names = self.__gui.dialog_rename.init_and_run("Umbenennen", filenames)  
                
        if response:
            for f in filenames:
                new_name = join(dirname(f), new_names[f])
                
                if f.endswith('.avi') and not new_name.endswith('.avi'):
                    new_name += '.avi'
                    
                fileoperations.rename_file(f, new_name)

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
