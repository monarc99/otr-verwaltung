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
from gtk import RESPONSE_OK
import time
import webbrowser
import urllib2
import xml.dom.minidom
import hashlib

from otrverwaltung.actions.baseaction import BaseAction

class Add(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, planned_broadcasts):
        if self.__gui.dialog_planning.run_new() == RESPONSE_OK:           
            broadcast, datetime, station = self.__gui.dialog_planning.get_values()
            item = planned_broadcasts.append(broadcast, datetime, station)

            self.__gui.main_window.append_row_planning(item)
            self.__gui.main_window.broadcasts_badge()
            
        self.__gui.dialog_planning.hide()
        
class Edit(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, broadcast_iter, planned_broadcasts):        
        model = self.__gui.main_window.builder.get_object('treeview_planning').get_model()
        broadcast = model.get_value(broadcast_iter, 0)
            
        if self.__gui.dialog_planning.run_edit(broadcast) == RESPONSE_OK:
            title, datetime, station = self.__gui.dialog_planning.get_values()
            broadcast.title = title
            broadcast.datetime = datetime
            broadcast.station = station
                        
            self.__gui.main_window.broadcasts_badge()            
            
        self.__gui.dialog_planning.hide()

class Remove(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, broadcast_iters, planned_broadcasts):
        if len(broadcast_iters) == 1:
            message = "Es ist eine Sendung ausgewählt. Soll diese Sendung "
        else:
            message = "Es sind %s Sendungen ausgewählt. Sollen diese Sendungen " % len(broadcast_iters)
        
        if self.__gui.question_box(message + "gelöscht werden?"):
            model = self.__gui.main_window.builder.get_object('treeview_planning').get_model()
            planning_items = [model.get_value(iter, 0) for iter in broadcast_iters]

            # remove rows            
            row_references = [gtk.TreeRowReference(model, model.get_path(iter)) for iter in broadcast_iters]
            for row_reference in row_references:
                iter = model.get_iter(row_reference.get_path())
                # remove from list
                planned_broadcasts.remove(model.get_value(iter, 0))
                # remove treeview row
                del model[iter]
            
            self.__gui.main_window.broadcasts_badge()            
            
class Search(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui
        
    def do(self, broadcast_iters, planned_broadcasts):
        model = self.__gui.main_window.builder.get_object('treeview_planning').get_model()
        for broadcast_iter in broadcast_iters:
            broadcast = model.get_value(broadcast_iter, 0)
                        
            # build string: Titanic_08.12.24_20-15_pro7_
            string = broadcast.title.replace(' ', '_') + ' '
            string += time.strftime("%y.%m.%d_%H-%M", time.localtime(broadcast.datetime)) + "_"
            string += broadcast.station + "_"
            
            webbrowser.open("http://www.otr-search.com/?q=%s" % string)
