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

import gtk

from basewindow import BaseWindow

class DialogCutlist(BaseWindow):
    
    def __init__(self, parent):
        widgets = [
            'labelCutlistFile',
            'treeviewCutlists',
            'treeviewCutlists_store'
            ]
        
        builder = self.create_builder("dialog_cutlist.ui")
            
        BaseWindow.__init__(self, builder, "dialog_cutlist", widgets, parent)
     
        self.__setup_widgets()
        
    def __setup_widgets(self):   
       
        # setup the file treeview
        treeview = self.get_widget('treeviewCutlists')
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
            str # 11 duration
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
    
    ###
    ### Convenience methods
    ###
            
    def add_cutlist(self, data):
        self.get_widget('treeviewCutlists').get_model().append(data)    
