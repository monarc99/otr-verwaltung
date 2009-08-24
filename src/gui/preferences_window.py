#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import gtk
import pango

from basewindow import BaseWindow
from constants import Cut_action
from configparser import EntryBinding, FileChooserBinding, CheckButtonBinding, ComboBoxEntryBinding, RadioButtonsBinding

class PreferencesWindow(BaseWindow):
    
    def __init__(self, app, gui, parent):
        self.app = app
        self.gui = gui
                      
        BaseWindow.__init__(self, "preferences_window", parent)
        
        self.__setup_widgets()
        
    def __setup_widgets(self):
        self.example_filename = 'James_Bond_007_09.01.06_20-15_ard_120_TVOON_DE.mpg.HQ.avi'
        
        # preferences fonts (little explanations)
        labels = [  'labelDescNewOtrkeys',
                    'labelDescUncutAvis',
                    'labelDescCutAvis',
                    'labelDescTrashOtrkeys',
                    'labelDescTrashAvis',
                    'labelBestCutlist',
                    'labelChooseCutlist',
                    'labelManually',                    
                    'labelLocalCutlist']
        for label in labels:
            self.get_widget(label).modify_font(pango.FontDescription("9"))            
                         
                    
        # avi + hq + mp4
        avidemux = ["avidemux", "avidemux2_cli"]
        virtualdub = [r"/pfad/zu/vdub.exe"]        
        self.gui.set_model_from_list(self.get_widget('combobox_avi'), avidemux + virtualdub)
        self.gui.set_model_from_list(self.get_widget('combobox_hq'), virtualdub)
        self.gui.set_model_from_list(self.get_widget('combobox_mp4'), avidemux)
        
        # manually
        avidemux_man = ["avidemux"]
        virtualdub_man = [r"/pfad/zu/VirtualDub.exe"]
        self.gui.set_model_from_list(self.get_widget('combobox_man_avi'), avidemux_man + virtualdub_man)
        self.gui.set_model_from_list(self.get_widget('combobox_man_hq'), virtualdub_man) 
        self.gui.set_model_from_list(self.get_widget('combobox_man_mp4'), avidemux_man)
       
        # fill comboboxentries
        self.gui.set_model_from_list(self.get_widget('comboboxServer'), ["http://cutlist.at/"])
                         
    def update_config_values(self):
        EntryBinding(self.app.config, 'cutlist_username', self.get_widget('entry_username'))
        EntryBinding(self.app.config, 'decoder', self.get_widget('entry_decoder'))
        EntryBinding(self.app.config, 'email', self.get_widget('entryEMail'))
        EntryBinding(self.app.config, 'password', self.get_widget('entryPassword'), encode=True)       
        EntryBinding(self.app.config, 'rename_schema', self.get_widget('entry_schema'))                
        
        def rename_schema_changed(value):
            new = self.app.rename_by_schema(self.example_filename, value)
            self.get_widget('label_schema').set_label("<i>%s</i> wird zu <i>%s</i>" % (self.example_filename, new))       
        self.app.config.connect('rename_schema', rename_schema_changed)
        
        FileChooserBinding(self.app.config, 'folder_new_otrkeys', self.get_widget('folderNewOtrkeys')),
        FileChooserBinding(self.app.config, 'folder_trash_otrkeys', self.get_widget('folderTrashOtrkeys')),
        FileChooserBinding(self.app.config, 'folder_trash_avis', self.get_widget('folderTrashAvis')),
        FileChooserBinding(self.app.config, 'folder_uncut_avis', self.get_widget('folderUncutAvis')),
        FileChooserBinding(self.app.config, 'folder_cut_avis', self.get_widget('folderCutAvis')),
        FileChooserBinding(self.app.config, 'folder_archive', self.get_widget('folderArchive')) 
        
        for option in ['folder_new_otrkeys', 'folder_trash_otrkeys', 'folder_trash_avis', 'folder_uncut_avis', 'folder_cut_avis', 'folder_archive']:
            self.app.config.connect(option, lambda value: self.app.show_section(self.app.section))

        CheckButtonBinding(self.app.config, 'verify_decoded', self.get_widget('checkCorrect'))
        CheckButtonBinding(self.app.config, 'smart', self.get_widget('check_smart'))
        CheckButtonBinding(self.app.config, 'delete_cutlists', self.get_widget('check_delete_cutlists'))
        CheckButtonBinding(self.app.config, 'rename_cut', self.get_widget('check_rename_cut'))
        
        self.app.config.connect('rename_cut', lambda value: self.get_widget('entry_schema').set_sensitive(value))
        
        ComboBoxEntryBinding(self.app.config, 'cut_avis_by', self.get_widget('combobox_avi'))
        ComboBoxEntryBinding(self.app.config, 'cut_hqs_by', self.get_widget('combobox_hq'))
        ComboBoxEntryBinding(self.app.config, 'cut_mp4s_by', self.get_widget('combobox_mp4'))
        ComboBoxEntryBinding(self.app.config, 'cut_avis_man_by', self.get_widget('combobox_man_avi'))
        ComboBoxEntryBinding(self.app.config, 'cut_hqs_man_by', self.get_widget('combobox_man_hq'))
        ComboBoxEntryBinding(self.app.config, 'cut_mp4s_man_by', self.get_widget('combobox_man_mp4'))
        ComboBoxEntryBinding(self.app.config, 'server', self.get_widget('comboboxServer'))

        RadioButtonsBinding(self.app.config, 'cut_action', [ 
                self.get_widget('radioAsk'),
                self.get_widget('radioBestCutlist'),
                self.get_widget('radioChooseCutlist'),
                self.get_widget('radioManually'),
                self.get_widget('radioLocalCutlist')
            ])
            
        RadioButtonsBinding(self.app.config, 'choose_cutlists_by', [ 
                self.get_widget('radio_size'),
                self.get_widget('radio_filename')
            ])
        
        self.get_widget('entryPassword').set_visibility(False)
    
        self.get_widget('entry_schema').set_sensitive(self.app.config.get('rename_cut'))
             
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
