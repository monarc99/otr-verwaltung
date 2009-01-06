#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import base64

try:
    import gtk
    import pango
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

from basewindow import BaseWindow

from constants import Save_Email_Password, On_Quit, Cut_action

class PreferencesWindow(BaseWindow):
    
    def __init__(self, app, gui, parent):
        self.app = app
        self.gui = gui
    
        widgets = [
            'notebook',
 
            # Allgemein
            'radio_ask',
            'radio_quit',
            'radio_minimize',
 
            # Speicherorte
            'folderArchive',
            # Dekodieren
            'filechooserDecoder',
            'entryEMail',
            'entryPassword',      
            'checkCorrect',
            # Schneiden
            'comboboxMPlayer',
            # Umbenennen
            'entry_schema',
            'label_schema'   
            ]
        
        builder = self.create_builder("preferences_window.ui")
            
        BaseWindow.__init__(self, builder, "preferences_window", widgets, parent)
        
        self.__setup_widgets(builder)
        
    def __setup_widgets(self, builder):
        self.example_filename = 'James_Bond_007_09.01.06_20-15_ard_120_TVOON_DE.mpg.HQ.avi'
        
        # preferences fonts (little explanations)
        labels = [  'labelDescNewOtrkeys',
                    'labelDescTrash',
                    'labelBestCutlist',
                    'labelChooseCutlist',
                    'labelManually',
                    'labelDescAvidemux']
        for label in labels:
            builder.get_object(label).modify_font(pango.FontDescription("8"))            
        
        builder.get_object('labelHeadline').modify_font(pango.FontDescription("bold"))
          
        # TODO: Do filling of comboboxes by glade
          
        # fill combobox of player
        player_store = gtk.ListStore(str)
        player_store.append(["vlc"])
        player_store.append(["totem"])
        player_store.append(["mplayer"])
        builder.get_object('comboboxPlayer').set_model(player_store)
        builder.get_object('comboboxPlayer').set_text_column(0)
        builder.get_object('comboboxentry-player').set_text(self.app.config.get('play', 'player'))
        
        # fill combobox of mplayer
        mplayer_store = gtk.ListStore(str)
        mplayer_store.append(["mplayer"])
        builder.get_object('comboboxMPlayer').set_model(mplayer_store)
        builder.get_object('comboboxMPlayer').set_text_column(0)
        builder.get_object('comboboxentry-mplayer').set_text(self.app.config.get('play', 'mplayer'))
        
        # fill combobox avidemux
        avidemux_store = gtk.ListStore(str)
        avidemux_store.append(["avidemux"])
        avidemux_store.append(["avidemux2"])        
        builder.get_object('comboboxAvidemux').set_model(avidemux_store)
        builder.get_object('comboboxAvidemux').set_text_column(0)
        builder.get_object('comboboxentry-avidemux').set_text(self.app.config.get('cut', 'avidemux'))
        
        # fill combobox servers
        server_store = gtk.ListStore(str)
        server_store.append(["http://cutlist.de/"])
        server_store.append(["http://cutlist.mbod.net/"])
        server_store.append(["http://cutlist.at/"])
        builder.get_object('comboboxServer').set_model(server_store)
        builder.get_object('comboboxServer').set_text_column(0)
        builder.get_object('comboboxentry-server').set_text(self.app.config.get('cut', 'server'))
        
        # fill values from config_dic
        # folder choosers on folders tab           
        builder.get_object('folderNewOtrkeys').set_current_folder(self.app.config.get('folders', 'new_otrkeys'))
        builder.get_object('folderTrash').set_current_folder(self.app.config.get('folders', 'trash'))
        builder.get_object('checkArchive').set_active(self.app.config.get('common', 'use_archive'))    
        builder.get_object('checkUseCutPlay').set_active(self.app.config.get('play', 'use_cut_play'))
        builder.get_object('folderArchive').set_current_folder(self.app.config.get('folders', 'archive'))     
              
        # decode tab
        self.get_widget('filechooserDecoder').set_filename(self.app.config.get('decode', 'path'))  
        if self.app.config.get('decode', 'save_email_password') == Save_Email_Password.DONT_SAVE:
            builder.get_object('radioDontSave').set_active(True)
            self.on_radioDontSave_toggled(builder.get_object('radioDontSave'))
        else:
            builder.get_object('radioSave').set_active(True)
            self.get_widget('entryEMail').set_text(self.app.config.get('decode', 'email'))
            self.get_widget('entryPassword').set_text(base64.b64decode(self.app.config.get('decode', 'password')))
           
        self.get_widget('entryPassword').set_visibility(False)
            
        self.get_widget('checkCorrect').set_active(self.app.config.get('decode', 'correct'))
            
        # radio buttons on cut tab
        radiobuttons = [ 'radioAsk', 'radioBestCutlist', 'radioChooseCutlist', 'radioManually' ] # order is important!
        builder.get_object(radiobuttons[self.app.config.get('cut', 'cut_action')]).set_active(True)
       
        # radio buttons common tab
        radiobuttons = [ 'radio_ask', 'radio_minimize', 'radio_quit' ] # order is important!
        builder.get_object(radiobuttons[self.app.config.get('common', 'on_quit')]).set_active(True)
        
        # rename tab
        builder.get_object('check_rename_cut').set_active(self.app.config.get('rename', 'rename_cut'))
        self.get_widget('entry_schema').set_sensitive(self.app.config.get('rename', 'rename_cut'))
        self.get_widget('entry_schema').set_text(self.app.config.get('rename', 'schema'))
        
    #
    #  Signal handlers
    #
    
    
    def on_preferences_buttonClose_clicked(self, widget, data=None):    
        self.hide()    

    def on_preferences_window_delete_event(self, window, event):        
        window.hide()
        return True # don't destroy
     
    # common tab
    def on_radio_ask_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('common', 'on_quit', On_Quit.ASK)
            
    def on_radio_quit_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('common', 'on_quit', On_Quit.QUIT)
    
    def on_radio_minimize_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('common', 'on_quit', On_Quit.MINIMIZE)
                      
    # folders tab
    # folder changed, save to config dictionary
    def on_folderNewOtrkeys_current_folder_changed(self, widget, data=None):        
        self.app.config.set('folders', 'new_otrkeys', widget.get_filename())
        self.app.show_section(self.app.section)
    
    def on_folderTrash_current_folder_changed(self, widget, data=None):
        self.app.config.set('folders', 'trash', widget.get_filename())
        self.app.show_section(self.app.section)

    def on_preferences_checkArchive_toggled(self, widget, data=None):          
        status = widget.get_active()
        self.app.config.set('common', 'use_archive', int(status))

        self.get_widget('folderArchive').set_sensitive(status)
        
        self.gui.main_window.get_widget('radioArchive').props.visible = status
        self.gui.main_window.get_widget('labelArchiveCount').props.visible = status
        self.gui.main_window.get_widget('separator3').props.visible = status
                
        self.gui.main_window.toolbar_buttons['archive'].props.visible = status 
                          
    def on_folderArchive_current_folder_changed(self, widget, data=None):        
        self.app.config.set('folders', 'archive', widget.get_filename())
        self.app.show_section(self.app.section)
                
    # decode tab
    def on_filechooserDecoder_file_set(self, widget, data=None):
        self.app.config.set('decode', 'path', widget.get_filename())
    
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
                
    def on_radioManually_toggled(self, widget, data=None):
        if widget.get_active()==True:
            self.app.config.set('cut', 'cut_action', Cut_action.MANUALLY)

    def on_comboboxentry_avidemux_changed(self, widget, data=None):
        self.app.config.set('cut', 'avidemux', widget.get_text())
    
    def on_comboboxentry_server_changed(self, widget, data=None):
        self.app.config.set('cut', 'server', widget.get_text())
        
    # play tab
    def on_comboboxentry_player_changed(self, widget, data=None):
        self.app.config.set('play', 'player', widget.get_text())
    
    def on_comboboxentry_mplayer_changed(self, widget, data=None):
        self.app.config.set('play', 'mplayer', widget.get_text())      
       
    def on_checkUseCutPlay_toggled(self, widget, data=None):       
        self.app.config.set('play', 'use_cut_play', int(widget.get_active()))
        
        self.get_widget('comboboxMPlayer').set_sensitive(widget.get_active())
                    
        self.gui.main_window.toolbar_buttons['cut_play'].props.visible = widget.get_active()
        
    # rename tab   
    def on_check_rename_cut_toggled(self, widget, data=None):
        self.get_widget('entry_schema').set_sensitive(widget.get_active())
        self.app.config.set('rename', 'rename_cut', int(widget.get_active()))
           
    def on_entry_schema_changed(self, widget, data=None):
        self.app.config.set('rename', 'schema', widget.get_text())
        new = self.app.rename_by_schema(self.example_filename, widget.get_text())
        self.get_widget('label_schema').set_label("<i>%s</i> wird zu <i>%s</i>" % (self.example_filename, new))       
