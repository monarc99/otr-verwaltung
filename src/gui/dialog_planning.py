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

from os.path import basename
import datetime
import time

import gtk

from basewindow import BaseWindow

class DialogPlanning(BaseWindow):
    
    def __init__(self, gui, parent):
        self.gui = gui
    
        widgets = [
            'label_headline',
            'entry_broadcast',
            'calendar',
            'entry_time',
            'comboboxentry_station'
            ]
        
        builder = self.create_builder("dialog_planning.ui")
            
        BaseWindow.__init__(self, builder, "dialog_planning", widgets, parent)
        
        # fill combobox
        store = gtk.ListStore(str)
        
        stations = "ARD ZDF Sat.1 Pro7 RTL kabel1 VOX RTL2 SWR WDR NDR MDR RBB HR BR BR alpha SuperRTL Tele5 DMAX 3sat ARTE PHOENIX EinsExtra EinsPlus EinsFestival ZDFdokukanal ZDFinfokanal ZDFtheaterkanal ComedyCentral 9live DASVIERTE Nickelodeon KIKA Eurosport DSF GIGA VIVA MTV N24 n-tv BBC World CNN TRT" 
        for station in stations.split(" "):
            store.append([station])        

        builder.get_object('combobox_station').set_model(store)
        builder.get_object('combobox_station').set_text_column(0)
            
    def run_new(self):       
        self.get_widget('label_headline').set_markup('<b>Neue Sendung hinzufügen:</b>')
     
        dt = datetime.datetime.today()
        self.get_widget('calendar').select_month(dt.month - 1, dt.year)
        self.get_widget('calendar').select_day(dt.day)
     
        self.get_widget('entry_broadcast').set_text('')
        self.get_widget('comboboxentry_station').set_text('')
     
        return self.run()
        
    def run_edit(self, broadcast, stamp, station):
        self.get_widget('label_headline').set_markup('<b>Sendung bearbeiten:</b>')
           
        self.get_widget('entry_broadcast').set_text(broadcast)

        dt = datetime.datetime.fromtimestamp(stamp)
        self.get_widget('calendar').select_month(dt.month - 1, dt.year)
        self.get_widget('calendar').select_day(dt.day)
        self.get_widget('entry_time').set_text(dt.strftime('%H:%M'))

        self.get_widget('comboboxentry_station').set_text(station)
           
        return self.run()
    
    def on_button_ok_clicked(self, dialog, data=None):
        # validate time
        if self.get_widget('entry_broadcast').get_text()=="":
            self.gui.message_error_box('Der Titel der Sendung ist nicht angegeben!')
            return
        
        try:
            hour, minute = self.get_widget('entry_time').get_text().split(':')               
            assert int(hour) in range(24)
            assert int(minute) in range(59)
        except:
            self.gui.message_error_box('Die Uhrzeit ist nicht korrekt formatiert!')
            return
  
        self.get_window().response(-5)
    
    def get_values(self):
        # do not allow: ',' and ';'
        broadcast = self.get_widget('entry_broadcast').get_text().replace(',','_').replace(';','_')
             
        # Note that month is zero-based (i.e it allowed values are 0-11) while selected_day is one-based (i.e. allowed values are 1-31).
        year, month, day = self.get_widget('calendar').get_date()
        hour, minute = self.get_widget('entry_time').get_text().split(':')
        dt = datetime.datetime(year, month + 1, day, int(hour), int(minute))
        stamp = time.mktime(dt.timetuple())
        
        station = self.get_widget('comboboxentry_station').get_text().replace(',','_').replace(';','_')
        
        return broadcast, int(stamp), station
