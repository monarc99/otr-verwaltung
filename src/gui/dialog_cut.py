#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
from os.path import join

from basewindow import BaseWindow

from constants import Cut_action
import cutlists as cutlists_management

class DialogCut(BaseWindow):
    
    def __init__(self, app, gui, parent):
        self.gui = gui
        self.app = app
    
        widgets = [
            'label_file',
            
            'radio_best_cutlist',
            'radio_choose_cutlist',
            'radio_local_cutlist',
            'label_cutlist',
            'radio_manually',            
            'label_warning',
            
            'button_show_cuts',
            'treeview_cutlists',
            'label_status'
            ]
        
        builder = self.create_builder("dialog_cut.ui")    
        
        BaseWindow.__init__(self, builder, "dialog_cut", widgets, parent)

        self.__setup_widgets()
        
        self.chosen_cutlist = None
        
    def __setup_widgets(self):   
       
        # setup the file treeview
        treeview = self.get_widget('treeview_cutlists')
        store = gtk.ListStore(
            str, # 0 id
            str, # 1 author
            str, # 2 ratingbyauthor
            str, # 3 rating
            str, # 4 ratingcount
            str, # 5 cuts
            str, # 6 actualcontent
            str, # 7 usercomment
            str, # 8 filename
            str, # 9 withframes
            str, # 10 withtime
            str  # 11 duration
            )             
        treeview.set_model(store)
            
        # create the TreeViewColumns to display the data
        column_names = ['Autor', 'Autorenwertung', 'Benutzerwertung', 'Benutzerkommentar' ]
        tvcolumns = [None] * len(column_names)
        
        renderer_left = gtk.CellRendererText()
        renderer_left.set_property('xalign', 0.0) 

        tvcolumns[0] = gtk.TreeViewColumn(column_names[0], renderer_left, text=1)
        tvcolumns[1] = gtk.TreeViewColumn(column_names[1], renderer_left, text=2)       
        tvcolumns[2] = gtk.TreeViewColumn(column_names[2], renderer_left, text=3)
        tvcolumns[3] = gtk.TreeViewColumn(column_names[3], renderer_left, text=7)        
              
        # append the columns
        for col in tvcolumns:
            col.set_resizable(True)        
            treeview.append_column(col)
            
        selection = treeview.get_selection()
        selection.connect('changed', self.on_selection_changed)
    
        self.filename = ""
    
    ###
    ### Convenience methods
    ###
            
    def add_cutlist(self, data):
        self.get_widget('treeview_cutlists').get_model().append(data)  
       
    ###
    ### Signal handlers
    ###
    
    def on_radio_manually_toggled(self, widget, data=None):
        self.get_widget('button_show_cuts').set_sensitive(not widget.get_active())
    
    def on_radio_best_cutlist_toggled(self, widget, data=None):
        self.get_widget('button_show_cuts').set_sensitive(not widget.get_active())
        
    def on_button_show_cuts_clicked(self, widget, data=None):
        if self.get_widget('radio_local_cutlist').get_active():
            local_filename = self.get_widget('label_cutlist').get_text()
            
        else:
            treeselection = self.get_widget('treeview_cutlists').get_selection()  

            if treeselection.count_selected_rows() == 0:                            
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return
            
            # retrieve id of chosen cutlist
            (model, iter) = treeselection.get_selected()                   
            cutlist_id = model.get_value(iter, 0)    
            
            local_filename = self.filename + ".cutlist"
            cutlists_management.download_cutlist(cutlist_id, self.app.config.get('cut', 'server'), local_filename)
            
        self.app.show_cuts(self.filename, local_filename)
    
    def on_selection_changed(self, selection, data=None):     
        model, paths = selection.get_selected_rows()
        if paths:
            self.get_widget('radio_choose_cutlist').set_active(True)
       
    def on_buttonCutOK_clicked(self, widget, data=None):
        if self.get_widget('radio_best_cutlist').get_active() == True:
            self.get_window().response(Cut_action.BEST_CUTLIST)

        elif self.get_widget('radio_choose_cutlist').get_active() == True:
            treeselection = self.get_widget('treeview_cutlists').get_selection()  
                
            if treeselection.count_selected_rows() == 0:                            
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return

            # retrieve id of chosen cutlist
            (model, iter) = treeselection.get_selected()                   
            self.chosen_cutlist = model.get_value(iter, 0)
        
            self.get_window().response(Cut_action.CHOOSE_CUTLIST)
            
        elif self.get_widget('radio_local_cutlist').get_active() == True:
            self.get_window().response(Cut_action.LOCAL_CUTLIST)
        else:                    
            self.get_window().response(Cut_action.MANUALLY)
