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

from otrverwaltung import path

class CutlistsTreeView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        
        self.pixbuf_warning = gtk.gdk.pixbuf_new_from_file(path.get_image_path('error.png'))      
           
        self.errors = {
           "100000" : "Fehlender Beginn", 
           "010000" : "Fehlendes Ende",
           "001000" : "Kein Video",
           "000100" : "Kein Audio",
           "000010" : "Anderer Fehler",
           "000001" : "Falscher Inhalt/EPG-Error"
        }           
               
        # setup combobox_archive       
        self.liststore = gtk.ListStore(object)        
        self.set_model(self.liststore)

        # create the TreeViewColumns to display the data
        column_names = [
            ("Autor", 'author'),
            ("Autorwertung", 'ratingbyauthor'),
            ("Benutzerwertung", self._treeview_rating),
            ("Kommentar", 'usercomment'),
            ("Fehler", self._treeview_errors),
            ("Eigentlicher Inhalt", self._treeview_actualcontent),
            ("Anzahl d. Schnitte", "countcuts"),
            ("Dateiname", "filename"),
            ("Dauer in s", "duration"),
            ("Anzahl Heruntergeladen", "downloadcount") ]
            
        # add a pixbuf renderer in case of errors in cutlists              
        cell_renderer_pixbuf = gtk.CellRendererPixbuf()
        col = gtk.TreeViewColumn('', cell_renderer_pixbuf)
        col.set_cell_data_func(cell_renderer_pixbuf, self._treeview_warning)
        self.append_column(col)      
              
        # append the columns
        for count, (text, data_func) in enumerate(column_names):                         
            renderer_left = gtk.CellRendererText()
            renderer_left.set_property('xalign', 0.0) 
            col = gtk.TreeViewColumn(text, renderer_left)

            if type(data_func) == str:
                col.set_cell_data_func(renderer_left, self._treeview_standard, data_func)
            else:                
                col.set_cell_data_func(renderer_left, data_func)

            col.set_resizable(True)        
            self.append_column(col)
       
    def get_selected_id(self):
        model, selected_row = self.get_selection().get_selected()
        if selected_row:
            return model.get_value(selected_row, 0).id
        else:
            return None
               
    def _treeview_standard(self, column, cell, model, iter, attribute_name):
        cutlist = model.get_value(iter, 0)
        cell.set_property('text', getattr(cutlist, attribute_name))
    
    def _treeview_warning(self, column, cell, model, iter):
        cutlist = model.get_value(iter, 0)
        
        if cutlist.errors or cutlist.actualcontent or cutlist.othererrordescription:
            cell.set_property('pixbuf', self.pixbuf_warning)
        else:
            cell.set_property('pixbuf', None)    
    
    def _treeview_rating(self, column, cell, model, iter):
        cutlist = model.get_value(iter, 0)
        if cutlist.rating:
            if cutlist.ratingcount == 1:
                cell.set_property('text', "%s (1 Bewertung)" % cutlist.rating)
            else:
                cell.set_property('text', "%s (%s Bewertungen)" % (cutlist.rating, cutlist.ratingcount))
        else:
            cell.set_property('text', "Keine")
            
    def _treeview_actualcontent(self, column, cell, model, iter):
        cutlist = model.get_value(iter, 0)
        cell.set_property('markup', "<span foreground='red'>%s</span>" % cutlist.actualcontent)

    def _treeview_errors(self, column, cell, model, iter):
        cutlist = model.get_value(iter, 0)
        text = "<span foreground='red'>%s" % cutlist.errors
        if cutlist.othererrordescription:
            text += " (%s)" % cutlist.othererrordescription
        text += "</span>"
        
        cell.set_property('markup', text)
    
    def _treeview_error_desc(self, column, cell, model, iter):
        cutlist = model.get_value(iter, 0)
        cell.set_property('markup', "<span foreground='red'>%s</span>" % cutlist.othererrordescription)
     
    def add_cutlist(self, c):     
        if c.errors in self.errors:
            c.errors = self.errors[c.errors]
        else:
            c.errors = ''
        
        self.liststore.append([c])
