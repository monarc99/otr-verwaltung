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
from os.path import join, basename, exists

from otrverwaltung.constants import Cut_action
import otrverwaltung.cutlists as cutlists_management
from otrverwaltung import fileoperations
from otrverwaltung import path

class CutDialog(gtk.Dialog, gtk.Buildable):
    """ Dialog, um den Schnittmodus constants.Cut_action und ggf die Cutlist auszuwählen """ 
    
    __gtype_name__ = "CutDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)
       
        self.cutlists = []        
        self.chosen_cutlist = None
 
        # warning sign
        self.pixbuf_warning = gtk.gdk.pixbuf_new_from_file(path.get_image_path('error.png'))      
               
        # setup the file treeview
        treeview = self.builder.get_object('treeview_cutlists')
        store = gtk.ListStore(
            str, # 0 id
            str, # 1 author
            str, # 2 ratingbyauthor
            str, # 3 rating
            str, # 4 ratingcount
            str, # 5 countcuts
            str, # 6 actualcontent
            str, # 7 usercomment
            str, # 8 filename
            str, # 9 withframes
            str, # 10 withtime
            str, # 11 duration
            str, # 12 errors
            str, # 13 othererrordescription
            str, # 14 downloadcount
            str, # 15 autoname
            str, # 16 filename_original            
            bool # 17 errors?
            )             
        
        treeview.set_model(store)
            
        # create the TreeViewColumns to display the data
        column_names = [
            (0, "ID"),
            (1, "Autor"),
            (2, "Autorwertung"),
            (3, "Benutzerwertung"),
            (4, "Anzahl d. Wertungen"),
            (7, "Kommentar"),
            (12, "Fehler"),
            (13, "Fehlerbeschr."),
            (6, "Eigentlicher Inhalt"),
            (5, "Anzahl d. Schnitte"),            
            (8, "Dateiname"),
            (11, "Dauer in s"),
            (14, "Anzahl Heruntergeladen") ]
        
        renderer_left = gtk.CellRendererText()
        renderer_left.set_property('xalign', 0.0) 
              
        cell_renderer_pixbuf = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('', cell_renderer_pixbuf)
        col.set_cell_data_func(cell_renderer_pixbuf, self.warning_pixbuf)
        treeview.append_column(col)      
              
        # append the columns
        for count, (index, text) in enumerate(column_names):                         
            col = gtk.TreeViewColumn(text, renderer_left, markup=index)

            col.set_resizable(True)        
            treeview.append_column(col)
            
        selection = treeview.get_selection()
        selection.connect('changed', self._on_selection_changed)
    
        self.filename = ""
    
    def warning_pixbuf(self, column, cell, model, iter):
        errors = model.get_value(iter, 17)
        
        if errors:
            cell.set_property('pixbuf', self.pixbuf_warning)
        else:
            cell.set_property('pixbuf', None)
    
    ###
    ### Convenience methods
    ###
            
    def setup(self, video_file, folder_cut_avis, cut_action_ask):
        self.filename = video_file
        self.builder.get_object('label_file').set_markup("<b>%s</b>" % basename(video_file))
        self.builder.get_object('label_warning').set_markup('<span size="small">Wichtig! Um eine Cutlist zu erstellen muss das Projekt im Ordner %s gespeichert werden (siehe Website->Einstieg->Funktionen). OTR-Verwaltung schneidet die Datei dann automatisch.</span>' % folder_cut_avis)

        if cut_action_ask:
            self.builder.get_object('radio_best_cutlist').set_active(True)
        else:
            self.builder.get_object('radio_choose_cutlist').set_active(True)

        # looking for a local cutlist
        filename_cutlist = video_file + ".cutlist"
        if exists(filename_cutlist):
            self.builder.get_object('label_cutlist').set_markup("<b>%s</b>" % filename_cutlist)
            self.builder.get_object('radio_local_cutlist').set_sensitive(True)
        else:
            self.builder.get_object('label_cutlist').set_markup("Keine lokale Cutlist gefunden.")
            self.builder.get_object('radio_local_cutlist').set_sensitive(False)

        # start looking for cutlists                
        self.builder.get_object('treeview_cutlists').get_model().clear()                
        self.builder.get_object('label_status').set_markup("<b>Cutlisten werden heruntergeladen...</b>")
            
    def add_cutlist(self, c):                                           
        self.cutlists.append(c)      

        errors = {
           "100000" : "Fehlender Beginn", 
           "010000" : "Fehlendes Ende",
           "001000" : "Kein Video",
           "000100" : "Kein Audio",
           "000010" : "Anderer Fehler",
           "000001" : "Falscher Inhalt/EPG-Error"
        }
      
        if c.errors in errors.keys():
            c.errors = errors[c.errors]
        else:
            c.errors = ''
        
        errors = False
        if c.actualcontent or c.errors or c.othererrordescription:
            errors = True
        
        c.actualcontent = "<span foreground='red'>%s</span>" % c.actualcontent
        c.errors = "<span foreground='red'>%s</span>" % c.errors
        c.othererrordescription = "<span foreground='red'>%s</span>" % c.othererrordescription
        
        data = [ c.id, c.author, "<b>%s</b>" % c.ratingbyauthor, "<b>%s</b>" % c.rating, c.ratingcount, c.countcuts, c.actualcontent, c.usercomment, c.filename, c.withframes, c.withtime, c.duration, c.errors, c.othererrordescription, c.downloadcount, c.autoname, c.filename_original ]
        data.append(errors)
        
        self.builder.get_object('treeview_cutlists').get_model().append(data)  
       
    ###
    ### Signal handlers
    ###
    
    def _on_radio_manually_toggled(self, widget, data=None):
        self.builder.get_object('button_show_cuts').set_sensitive(not widget.get_active())
    
    def _on_radio_best_cutlist_toggled(self, widget, data=None):
        self.builder.get_object('button_show_cuts').set_sensitive(not widget.get_active())
        
    def _on_button_show_cuts_clicked(self, widget, data=None):
        cutlist = cutlists_management.Cutlist()

        if self.builder.get_object('radio_local_cutlist').get_active():
            
            cutlist.local_filename = self.builder.get_object('label_cutlist').get_text()
            
        else:
            treeselection = self.builder.get_object('treeview_cutlists').get_selection()  

            if treeselection.count_selected_rows() == 0:                            
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return
            
            # retrieve id of chosen cutlist
            (model, iter) = treeselection.get_selected()                   
            cutlist_id = model.get_value(iter, 0)    
                        
            cutlist.id = cutlist_id
                                    
            error = cutlist.download(self.app.config.get('server'), self.filename)

            if error:
                self.gui.message_error_box(error)
                return
            
        self.app.show_cuts(self.filename, cutlist)
        
        # delete cutlist
        fileoperations.remove_file(cutlist.local_filename)
    
    def _on_selection_changed(self, selection, data=None):     
        model, paths = selection.get_selected_rows()
        if paths:
            self.builder.get_object('radio_choose_cutlist').set_active(True)
       
    def _on_buttonCutOK_clicked(self, widget, data=None):
        if self.builder.get_object('radio_best_cutlist').get_active() == True:
            self.response(Cut_action.BEST_CUTLIST)

        elif self.builder.get_object('radio_choose_cutlist').get_active() == True:
            treeselection = self.builder.get_object('treeview_cutlists').get_selection()  
                
            if treeselection.count_selected_rows() == 0:                            
                self.gui.message_error_box("Es wurde keine Cutlist ausgewählt!")
                return

            # retrieve id of chosen cutlist
            (model, iter) = treeselection.get_selected()                   
            cutlist_id = model.get_value(iter, 0)
        
            for cutlist in self.cutlists:
                if cutlist.id == cutlist_id:
                    self.chosen_cutlist = cutlist
                    self.response(Cut_action.CHOOSE_CUTLIST)
                    return
            
        elif self.builder.get_object('radio_local_cutlist').get_active() == True:
            self.response(Cut_action.LOCAL_CUTLIST)
        else:                    
            self.response(Cut_action.MANUALLY)

def NewCutDialog(app, gui):
    glade_filename = path.getdatapath('ui', 'CutDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("cut_dialog")
    dialog.app = app
    dialog.gui = gui
        
    return dialog
