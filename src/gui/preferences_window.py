#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os

import gtk
import pango

from basewindow import BaseWindow
from constants import Save_Email_Password, Cut_action

class PreferencesWindow(BaseWindow):
    
    def __init__(self, app, gui, parent):
        self.app = app
        self.gui = gui
                      
        BaseWindow.__init__(self, "preferences_window.ui", "preferences_window", parent)
        
        self.__setup_widgets()
        
    def __setup_widgets(self):
        self.example_filename = 'James_Bond_007_09.01.06_20-15_ard_120_TVOON_DE.mpg.HQ.avi'
        
        # preferences fonts (little explanations)
        labels = [  'labelDescNewOtrkeys',
                    'labelDescUncutAvis',
                    'labelDescCutAvis',
                    'labelDescTrash',
                    'labelBestCutlist',
                    'labelChooseCutlist',
                    'labelManually',                    
                    'labelLocalCutlist']
        for label in labels:
            self.get_widget(label).modify_font(pango.FontDescription("9"))            
                         
        # fill combobox of player
        if os.name == "posix":
            players = ["vlc", "totem", "mplayer"]
        else:
            players = [r"X:\Pfad\zu\vlc.exe", r"X:\Pfad\zu\wmp.exe"]
        
        self.__set_model_from_list(self.get_widget('comboboxPlayer'), players)
        self.get_widget('comboboxentry-player').set_text(self.app.config.get('play', 'player'))
        
        # fill combobox of mplayer
        if os.name == "posix":
            mplayers = ["mplayer"]
        else:
            mplayers = [r"X:\Pfad\zu\mplayer.exe"]

        self.__set_model_from_list(self.get_widget('comboboxMPlayer'), mplayers)
        self.get_widget('comboboxentry-mplayer').set_text(self.app.config.get('play', 'mplayer'))

        # fill combobox of avi, hq, mp4
        if os.name == "posix":
            avidemux = ["avidemux", "avidemux2_cli"]
            avidemux_man = ["avidemux"]
            virtualdub = [r"/pfad/zu/vdub.exe"]
            virtualdub_man = [r"/pfad/zu/VirtualDub.exe"]
        else:
            avidemux = [r"C:\Programme\Avidemux\avidemux.exe"]
            avidemux_man = [r"C:\Programme\Avidemux\avidemux.exe"]
            virtualdub = [r"C:\Programme\VirtualDub\vdub.exe"]
            virtualdub_man = [r"C:\Programme\VirtualDub\VirtualDub.exe"]

        # avi + hq        
        self.__set_model_from_list(self.get_widget('combobox_avi'), avidemux + virtualdub)
        self.get_widget('comboboxentry-avi').set_text(self.app.config.get('cut', 'avi'))
        self.__set_model_from_list(self.get_widget('combobox_hq'), virtualdub)
        self.get_widget('comboboxentry-hq').set_text(self.app.config.get('cut', 'hq'))
    
        # man_avi + man_avidemux
        self.__set_model_from_list(self.get_widget('combobox_man_avi'), avidemux_man + virtualdub_man)
        self.get_widget('comboboxentry-man_avi').set_text(self.app.config.get('cut', 'man_avi'))
        self.__set_model_from_list(self.get_widget('combobox_man_hq'), virtualdub_man)
        self.get_widget('comboboxentry-man_hq').set_text(self.app.config.get('cut', 'man_hq'))
                
        # fill combobox servers
        self.__set_model_from_list(self.get_widget('comboboxServer'), ["http://cutlist.mbod.net/", "http://cutlist.at/"])
        self.get_widget('comboboxentry-server').set_text(self.app.config.get('cut', 'server'))
        
        # fill values from config_dic
        # folder choosers on folders tab           
        self.get_widget('folderNewOtrkeys').set_current_folder(self.app.config.get('folders', 'new_otrkeys'))
        self.get_widget('folderTrash').set_current_folder(self.app.config.get('folders', 'trash'))
        self.get_widget('folderUncutAvis').set_current_folder(self.app.config.get('folders', 'uncut_avis'))
        self.get_widget('folderCutAvis').set_current_folder(self.app.config.get('folders', 'cut_avis'))
        self.get_widget('checkArchive').set_active(self.app.config.get('common', 'use_archive'))    
        self.get_widget('folderArchive').set_current_folder(self.app.config.get('folders', 'archive'))     
        self.get_widget('check_smart').set_active(self.app.config.get('cut', 'smart'))
         
        # cutlists tab
        self.get_widget('check_delete_cutlists').set_active(self.app.config.get('cut', 'delete_cutlists'))
        self.get_widget('entry_username').set_text(self.app.config.get('cut', 'cutlist_username'))
        
        # choose cutlists by size or filename
        value = bool(self.app.config.get('cut', 'choose_cutlists_by')) # 0=size, 1=filename
        self.get_widget('radio_size').set_active(not value) 
        self.get_widget('radio_filename').set_active(value)
              
        # decode tab
        self.get_widget('entry_decoder').set_text(self.app.config.get('decode', 'path'))
        
        if self.app.config.get('decode', 'save_email_password') == Save_Email_Password.DONT_SAVE:
            self.get_widget('radioDontSave').set_active(True)
            self.on_radioDontSave_toggled(self.get_widget('radioDontSave'))
        else:
            self.get_widget('radioSave').set_active(True)
            self.get_widget('entryEMail').set_text(self.app.config.get('decode', 'email'))
            self.get_widget('entryPassword').set_text(base64.b64decode(self.app.config.get('decode', 'password')))
        
                   
        self.get_widget('entryPassword').set_visibility(False)
            
        self.get_widget('checkCorrect').set_active(self.app.config.get('decode', 'correct'))
        self.get_widget('entry_hash').set_text(self.app.config.get('decode', 'hash'))
        
        # radio buttons on cut tab
        radiobuttons = [ 'radioAsk', 'radioBestCutlist', 'radioChooseCutlist', 'radioManually', 'radioLocalCutlist'] # order is important!
        self.get_widget(radiobuttons[self.app.config.get('cut', 'cut_action')]).set_active(True)
               
        # rename tab
        self.get_widget('check_rename_cut').set_active(self.app.config.get('rename', 'rename_cut'))
        self.get_widget('entry_schema').set_sensitive(self.app.config.get('rename', 'rename_cut'))
        self.get_widget('entry_schema').set_text(self.app.config.get('rename', 'schema'))
     
    #
    # Helper
    # 
        
    def __set_model_from_list(self, cb, items):
        """Setup a ComboBox or ComboBoxEntry based on a list of strings."""           
        model = gtk.ListStore(str)
        for i in items:
            model.append([i])
        cb.set_model(model)
        if type(cb) == gtk.ComboBoxEntry:
            cb.set_text_column(0)
        elif type(cb) == gtk.ComboBox:
            cell = gtk.CellRendererText()
            cb.pack_start(cell, True)
            cb.add_attribute(cell, 'text', 0)
        
        
    #
    #  Signal handlers
    #
    
    def on_button_set_file_clicked(self, entry, data=None):    
        chooser = gtk.FileChooserDialog(title="Datei auswählen",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
                                        
        if chooser.run() == gtk.RESPONSE_OK:
            entry.set_text(chooser.get_filename())
    
        chooser.destroy()
    
    def on_preferences_buttonClose_clicked(self, widget, data=None):    
        self.hide()    

    def on_preferences_window_delete_event(self, window, event):        
        window.hide()
        return True # don't destroy
     
                     
    # folders tab
    # folder changed, save to config dictionary
    def on_folderNewOtrkeys_current_folder_changed(self, widget, data=None):        
        self.app.config.set('folders', 'new_otrkeys', widget.get_filename())
        self.app.show_section(self.app.section)
    
    def on_folderTrash_current_folder_changed(self, widget, data=None):
        self.app.config.set('folders', 'trash', widget.get_filename())
        self.app.show_section(self.app.section)
        
    def on_folderUncutAvis_current_folder_changed(self, widget, data=None):
        self.app.config.set('folders', 'uncut_avis', widget.get_filename())
        self.app.show_section(self.app.section)

    def on_folderCutAvis_current_folder_changed(self, widget, data=None):
        self.app.config.set('folders', 'cut_avis', widget.get_filename())
        self.app.show_section(self.app.section)

    def on_preferences_checkArchive_toggled(self, widget, data=None):          
        status = widget.get_active()
        self.app.config.set('common', 'use_archive', int(status))

        self.get_widget('folderArchive').set_sensitive(status)
        
        self.gui.main_window.get_widget('radioArchive').props.visible = status
        self.gui.main_window.get_widget('labelArchiveCount').props.visible = status
                
        self.gui.main_window.toolbar_buttons['archive'].props.visible = status 
                          
    def on_folderArchive_current_folder_changed(self, widget, data=None):        
        self.app.config.set('folders', 'archive', widget.get_filename())
        self.app.show_section(self.app.section)
                
    # decode tab
    def on_entry_decoder_changed(self, widget, data=None):
        self.app.config.set('decode', 'path', widget.get_text())
    
    def on_radioDontSave_toggled(self, widget, data=None):
        if widget.get_active() == True:
            self.app.config.set('decode', 'save_email_password', Save_Email_Password.DONT_SAVE)
            self.get_widget('entryEMail').set_text("")
            self.get_widget('entryEMail').set_sensitive(False)
            self.get_widget('entryPassword').set_text("")
            self.get_widget('entryPassword').set_sensitive(False)
        
    def on_radioSave_toggled(self, widget, data=None):
        if widget.get_active() == True:
            self.app.config.set('decode', 'save_email_password', Save_Email_Password.SAVE)
            self.get_widget('entryEMail').set_sensitive(True)
            self.get_widget('entryPassword').set_sensitive(True)
            
    def on_entryEMail_changed(self, widget, data=None):
        self.app.config.set('decode', 'email', widget.get_text())
        
    def on_entryPassword_changed(self, widget, data=None):
        self.app.config.set('decode', 'password', base64.b64encode(widget.get_text()))
    
    def on_checkCorrect_toggled(self, widget, data=None):
        self.app.config.set('decode', 'correct', int(widget.get_active()))

    def on_entry_hash_changed(self, widget, data=None):
        self.app.config.set('decode', 'hash', widget.get_text())
  
    # cut tab
    def on_radioAsk_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('cut', 'cut_action', Cut_action.ASK)
            
    def on_radioBestCutlist_toggled(self, widget, data=None):
        if widget.get_active()==True:
           self.app.config.set('cut', 'cut_action', Cut_action.BEST_CUTLIST)
                
    def on_radioChooseCutlist_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('cut', 'cut_action', Cut_action.CHOOSE_CUTLIST)
            
    def on_radioLocalCutlist_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('cut', 'cut_action', Cut_action.LOCAL_CUTLIST)

    def on_radioManually_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('cut', 'cut_action', Cut_action.MANUALLY)

    def on_comboboxentry_avi_changed(self, widget, data=None):
        self.app.config.set('cut', 'avi', widget.get_text())

    def on_comboboxentry_hq_changed(self, widget, data=None):
        self.app.config.set('cut', 'hq', widget.get_text())
        
    def on_comboboxentry_man_avi_changed(self, widget, data=None):
        self.app.config.set('cut', 'man_avi', widget.get_text())

    def on_comboboxentry_man_hq_changed(self, widget, data=None):
        self.app.config.set('cut', 'man_hq', widget.get_text())

    def on_check_smart_toggled(self, widget, data=None):
        self.app.config.set('cut', 'smart', int(widget.get_active()))
    
    # cutlist tab    
    def on_comboboxentry_server_changed(self, widget, data=None):
        self.app.config.set('cut', 'server', widget.get_text())
        
    def on_check_delete_cutlists_toggled(self, widget, data=None):
        self.app.config.set('cut', 'delete_cutlists', int(widget.get_active()))
      
    def on_radio_size_toggled(self, widget, data=None):
        if widget.get_active():
            self.app.config.set('cut', 'choose_cutlists_by', 0)
            
    def on_radio_filename_toggled(self, widget, data=None):
        if widget.get_active():
            self.app.config.set('cut', 'choose_cutlists_by', 1)        
    
    def on_entry_username_changed(self, widget, data=None):
        self.app.config.set('cut', 'cutlist_username', widget.get_text())
            
    # play tab
    def on_comboboxentry_player_changed(self, widget, data=None):
        self.app.config.set('play', 'player', widget.get_text())
    
    def on_comboboxentry_mplayer_changed(self, widget, data=None):
        self.app.config.set('play', 'mplayer', widget.get_text())      
               
    # rename tab   
    def on_check_rename_cut_toggled(self, widget, data=None):
        self.get_widget('entry_schema').set_sensitive(widget.get_active())
        self.app.config.set('rename', 'rename_cut', int(widget.get_active()))
           
    def on_entry_schema_changed(self, widget, data=None):
        self.app.config.set('rename', 'schema', widget.get_text())
        new = self.app.rename_by_schema(self.example_filename, widget.get_text())
        self.get_widget('label_schema').set_label("<i>%s</i> wird zu <i>%s</i>" % (self.example_filename, new))       
