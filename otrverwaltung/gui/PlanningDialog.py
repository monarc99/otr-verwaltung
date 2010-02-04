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

from os.path import basename
import datetime
import time

import gtk

from otrverwaltung import path

class PlanningDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "PlanningDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)

        # fill combobox
        store = gtk.ListStore(str)
        
        stations = "ARD ZDF Sat.1 Pro7 RTL kabel1 VOX RTL2 SWR WDR NDR MDR RBB HR BR BR alpha SuperRTL Tele5 DMAX 3sat ARTE PHOENIX EinsExtra EinsPlus EinsFestival ZDFdokukanal ZDFinfokanal ZDFtheaterkanal ComedyCentral 9live DASVIERTE Nickelodeon KIKA Eurosport DSF GIGA VIVA MTV N24 n-tv BBC World CNN TRT" 
        for station in stations.split(" "):
            store.append([station])        

        self.builder.get_object('combobox_station').set_model(store)
        self.builder.get_object('combobox_station').set_text_column(0)
            
    def run_new(self):       
        self.builder.get_object('label_headline').set_markup('<b>Neue Sendung hinzufügen:</b>')
     
        dt = datetime.datetime.today()
        self.builder.get_object('calendar').select_month(dt.month - 1, dt.year)
        self.builder.get_object('calendar').select_day(dt.day)
     
        self.builder.get_object('entry_broadcast').set_text('')
        self.builder.get_object('combobox_station').child.set_text('')
     
        return self.run()
        
    def run_edit(self, broadcast):
        self.builder.get_object('label_headline').set_markup('<b>Sendung bearbeiten:</b>')
           
        self.builder.get_object('entry_broadcast').set_text(broadcast.title)

        dt = datetime.datetime.fromtimestamp(broadcast.datetime)
        self.builder.get_object('calendar').select_month(dt.month - 1, dt.year)
        self.builder.get_object('calendar').select_day(dt.day)
        self.builder.get_object('entry_time').set_text(dt.strftime('%H:%M'))

        self.builder.get_object('combobox_station').child.set_text(broadcast.station)
           
        return self.run()
    
    def _on_button_ok_clicked(self, dialog, data=None):
        # validate time
        if self.builder.get_object('entry_broadcast').get_text()=="":
            self.gui.message_error_box('Der Titel der Sendung ist nicht angegeben!')
            return

        try:
            hour, minute = self.builder.get_object('entry_time').get_text().split(':')               
            assert int(hour) in range(24)
            assert int(minute) in range(59)
        except:
            self.gui.message_error_box('Die Uhrzeit ist nicht korrekt formatiert!')
            return
  
        self.response(-5)
    
    def get_values(self):
        # do not allow: ',' and ';'
        broadcast = self.builder.get_object('entry_broadcast').get_text().replace(',','_').replace(';','_')
             
        # Note that month is zero-based (i.e it allowed values are 0-11) while selected_day is one-based (i.e. allowed values are 1-31).
        year, month, day = self.builder.get_object('calendar').get_date()
        hour, minute = self.builder.get_object('entry_time').get_text().split(':')
        dt = datetime.datetime(year, month + 1, day, int(hour), int(minute))
        stamp = time.mktime(dt.timetuple())
        
        station = self.builder.get_object('combobox_station').child.get_text().replace(',','_').replace(';','_')
        
        return broadcast, int(stamp), station
        
def NewPlanningDialog(gui):
    glade_filename = path.getdatapath('ui', 'PlanningDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("planning_dialog")
    dialog.gui = gui
        
    return dialog
