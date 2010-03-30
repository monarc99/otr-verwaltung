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

import os

import gtk
import pango

from otrverwaltung.constants import Cut_action
from otrverwaltung.gui.config_bindings import EntryBinding, FileChooserFolderBinding, CheckButtonBinding, ComboBoxEntryBinding, RadioButtonsBinding
from otrverwaltung import path

class PreferencesWindow(gtk.Window, gtk.Buildable):
    __gtype_name__ = "PreferencesWindow"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):  
        self.builder = builder
        self.builder.connect_signals(self)        
                                 
    def bind_config(self, config):
        self.example_filename = 'James_Bond_007_09.01.06_20-15_ard_120_TVOON_DE.mpg.HQ.avi'
        
        # preferences fonts (little explanations)
        labels = [  'labelDescNewOtrkeys',
                    'labelDescUncutAvis',
                    'labelDescCutAvis',
                    'labelDescTrashOtrkeys',
                    'labelDescTrashAvis']
        for label in labels:
            self.builder.get_object(label).modify_font(pango.FontDescription("9"))                                     
                    
        # avi + hq + mp4
        avidemux = ["avidemux", "avidemux2_cli"]
        virtualdub = [r"/pfad/zu/vdub.exe"]        
        self.gui.set_model_from_list(self.builder.get_object('combobox_avi'), avidemux + virtualdub)
        self.gui.set_model_from_list(self.builder.get_object('combobox_hq'), virtualdub)
        self.gui.set_model_from_list(self.builder.get_object('combobox_mp4'), avidemux)
        
        # manually
        avidemux_man = ["avidemux"]
        virtualdub_man = [r"/pfad/zu/VirtualDub.exe"]
        self.gui.set_model_from_list(self.builder.get_object('combobox_man_avi'), avidemux_man + virtualdub_man)
        self.gui.set_model_from_list(self.builder.get_object('combobox_man_hq'), virtualdub_man) 
        self.gui.set_model_from_list(self.builder.get_object('combobox_man_mp4'), avidemux_man)
       
        self.gui.set_model_from_list(self.builder.get_object('comboboxServer'), ["http://cutlist.at/"])
        
        # add bindings here.
               
        EntryBinding(self.builder.get_object('entry_username'), self.app.config, 'general', 'cutlist_username')
        EntryBinding(self.builder.get_object('entry_decoder'), self.app.config, 'general', 'decoder')
        EntryBinding(self.builder.get_object('entryEMail'), self.app.config, 'general', 'email')
        EntryBinding(self.builder.get_object('entryPassword'), self.app.config, 'general', 'password', encode=True)       
        EntryBinding(self.builder.get_object('entry_schema'), self.app.config, 'general', 'rename_schema')                
        
        def rename_schema_changed(value):
            new = self.app.rename_by_schema(self.example_filename, value)
            self.builder.get_object('label_schema').set_label("<i>%s</i> wird zu <i>%s</i>" % (self.example_filename, new))       
        self.app.config.connect('general', 'rename_schema', rename_schema_changed)
        # "initial rename"
        # TODO: remove?
        #rename_schema_changed(self.builder.get_object('entry_schema').get_text())        
        
        FileChooserFolderBinding(self.builder.get_object('folderNewOtrkeys'), self.app.config, 'general', 'folder_new_otrkeys')
        FileChooserFolderBinding(self.builder.get_object('folderTrashOtrkeys'), self.app.config, 'general', 'folder_trash_otrkeys')
        FileChooserFolderBinding(self.builder.get_object('folderTrashAvis'), self.app.config, 'general', 'folder_trash_avis')
        FileChooserFolderBinding(self.builder.get_object('folderUncutAvis'), self.app.config, 'general', 'folder_uncut_avis')
        FileChooserFolderBinding(self.builder.get_object('folderCutAvis'), self.app.config, 'general', 'folder_cut_avis')
        FileChooserFolderBinding(self.builder.get_object('folderArchive'), self.app.config, 'general', 'folder_archive')
        
        for option in ['folder_new_otrkeys', 'folder_trash_otrkeys', 'folder_trash_avis', 'folder_uncut_avis', 'folder_cut_avis', 'folder_archive']:
            self.app.config.connect('general', option, lambda value: self.app.show_section(self.app.section))

        CheckButtonBinding(self.builder.get_object('checkCorrect'), self.app.config, 'general', 'verify_decoded')
        CheckButtonBinding(self.builder.get_object('check_delete_cutlists'), self.app.config, 'general', 'delete_cutlists')
        CheckButtonBinding(self.builder.get_object('check_rename_cut'), self.app.config, 'general', 'rename_cut')
        
        self.app.config.connect('general', 'rename_cut', lambda value: self.builder.get_object('entry_schema').set_sensitive(value))
        
        ComboBoxEntryBinding(self.builder.get_object('combobox_avi'), self.app.config, 'general', 'cut_avis_by')
        ComboBoxEntryBinding(self.builder.get_object('combobox_hq'), self.app.config, 'general', 'cut_hqs_by')
        ComboBoxEntryBinding(self.builder.get_object('combobox_mp4'), self.app.config, 'general', 'cut_mp4s_by')
        ComboBoxEntryBinding(self.builder.get_object('combobox_man_avi'), self.app.config, 'general', 'cut_avis_man_by')
        ComboBoxEntryBinding(self.builder.get_object('combobox_man_hq'), self.app.config, 'general', 'cut_hqs_man_by')
        ComboBoxEntryBinding(self.builder.get_object('combobox_man_mp4'), self.app.config, 'general', 'cut_mp4s_man_by')
        ComboBoxEntryBinding(self.builder.get_object('comboboxServer'), self.app.config, 'general', 'server')

        RadioButtonsBinding([self.builder.get_object(widget) for widget in ['radio_size', 'radio_filename']], self.app.config, 'general', 'choose_cutlists_by') 
        
        self.builder.get_object('entryPassword').set_visibility(False)    
        self.builder.get_object('entry_schema').set_sensitive(self.app.config.get('general', 'rename_cut'))
             
    #  Signal handlers

    def _on_button_set_file_clicked(self, entry, data=None):    
        chooser = gtk.FileChooserDialog(title="Datei auswählen",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
                                        
        if chooser.run() == gtk.RESPONSE_OK:
            if type(entry) == gtk.ComboBoxEntry:
                entry.child.set_text(chooser.get_filename())
            else:
                entry.set_text(chooser.get_filename())
    
        chooser.destroy()
    
    def _on_preferences_buttonClose_clicked(self, widget, data=None):    
        self.hide()    

    def _on_preferences_window_delete_event(self, window, event):        
        self.hide()
        return True # don't destroy
        
def NewPreferencesWindow(app, gui):
    glade_filename = path.getdatapath('ui', 'PreferencesWindow.glade')

    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    window = builder.get_object("preferences_window")
    window.app = app
    window.gui = gui
    return window
