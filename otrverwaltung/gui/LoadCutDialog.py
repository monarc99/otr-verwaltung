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

import gtk
import os
import re

from otrverwaltung.constants import Cut_action
import otrverwaltung.cutlists as cutlists_management
from otrverwaltung import fileoperations
from otrverwaltung import path
from otrverwaltung.gui.widgets.CutlistsTreeView import CutlistsTreeView
from otrverwaltung.GeneratorTask import GeneratorTask

class LoadCutDialog(gtk.Dialog, gtk.Buildable):
    """ Dialog, um Cutlists lokal oder von cutlist.at zu laden """ 
    
    __gtype_name__ = "LoadCutDialog"

    def __init__(self):
        self.download_error = False

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)
       
        self.chosen_cutlist = None
 
        self.treeview_local_cutlists = CutlistsTreeView()
        self.treeview_local_cutlists.show()
        self.treeview_local_cutlists.get_selection().connect('changed', self._on_local_selection_changed)
        self.builder.get_object('scrolledwindow_local').add(self.treeview_local_cutlists)
        self.treeview_download_cutlists = CutlistsTreeView()
        self.treeview_download_cutlists.show()
        self.treeview_download_cutlists.get_selection().connect('changed', self._on_download_selection_changed)
        self.builder.get_object('scrolledwindow_download').add(self.treeview_download_cutlists)
     
        self.filename = ""
        
    ###
    ### Convenience methods
    ###
            
    def setup(self, video_file):
        self.filename = video_file
        self.builder.get_object('label_file').set_markup("<b>%s</b>" % os.path.basename(video_file))

        # looking for local cutlists
        p, filename = os.path.split(video_file)
        cutregex = re.compile("^" + filename + "\.?(.*).cutlist$")
        files = os.listdir(p)
        local_cutlists = []
        for f in files:
            match = cutregex.match(f)
            if match:
                # print "Found local cutlist"
                local_cutlists.append(p + '/' + match.group())
            else:
                # print f + " is no cutlist"
                pass
        
        # print "%d cutlists found" % len(local_cutlists)
        if len(local_cutlists) > 0:
            self.treeview_local_cutlists.get_model().clear()
            self.builder.get_object('scrolledwindow_local').set_sensitive(True)
            self.builder.get_object('button_local').set_sensitive(True)
            for c in local_cutlists:
                cutlist = cutlists_management.Cutlist()
                cutlist.local_filename = c
                cutlist.read_from_file()
                self.treeview_local_cutlists.add_cutlist(cutlist)
            
        else:
            self.builder.get_object('scrolledwindow_local').set_sensitive(False)
            self.builder.get_object('button_local').set_active(False)
            self.builder.get_object('button_local').set_sensitive(False)
        
        # start looking for downloadable cutlists
        self.treeview_download_cutlists.get_model().clear()                
        self.builder.get_object('label_status').set_markup("<b>Cutlisten werden heruntergeladen...</b>")
        self.download_error = False

        GeneratorTask(cutlists_management.download_cutlists, None, self._completed).start(video_file, self.app.config.get('general', 'server'), self.app.config.get('general', 'choose_cutlists_by'), self.app.config.get('general', 'cutlist_mp4_as_hq'), self._error_cb, self._cutlist_found_cb)

            
    def _error_cb(self, error):
        print "Error: %s" % error
        self.builder.get_object('label_status').set_markup("<b>%s</b>" % error)
        self.download_error = True
    
    def _cutlist_found_cb(self, cutlist):
        # print "Found cutlist"
        self.add_cutlist(cutlist)
    
    def _completed(self):
        # print "Downloading cutlists completed. download_error = %r" % self.download_error
        if not self.download_error:
            self.builder.get_object('label_status').set_markup("")
    
    def add_cutlist(self, c):                                           
        self.treeview_download_cutlists.add_cutlist(c)
       
    ###
    ### Signal handlers
    ###
    
    def _on_local_selection_changed(self, selection, data=None):     
        model, paths = selection.get_selected_rows()
        if paths:
            self.builder.get_object('button_local').set_active(True)
            self.treeview_download_cutlists.get_selection().unselect_all()
       
    def _on_download_selection_changed(self, selection, data=None):     
        model, paths = selection.get_selected_rows()
        if paths:
            self.builder.get_object('button_download').set_active(True)
            self.treeview_local_cutlists.get_selection().unselect_all()
       
    def on_button_ok_clicked(self, widget, data=None):
        if self.builder.get_object('button_local').get_active() == True:
            cutlist = self.treeview_local_cutlists.get_selected()
                
            if not cutlist:
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return
            
            self.result = cutlist
            self.response(1)
            
        elif self.builder.get_object('button_download').get_active() == True:
            cutlist = self.treeview_download_cutlists.get_selected()
                
            if not cutlist:
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return
            
            cutlist.download(self.app.config.get('general', 'server'), self.filename)
            self.result = cutlist
            self.response(1)

def NewLoadCutDialog(app, gui):
    glade_filename = path.getdatapath('ui', 'LoadCutDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("load_cut_dialog")
    dialog.app = app
    dialog.gui = gui
        
    return dialog
