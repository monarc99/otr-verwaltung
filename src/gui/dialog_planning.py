#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import basename
import datetime
import time

import gtk

from basewindow import BaseWindow

class DialogPlanning(BaseWindow):
    
    def __init__(self, gui, parent):
        self.gui = gui
            
        BaseWindow.__init__(self, "dialog_planning.ui", "dialog_planning", parent)
        
        # fill combobox
        store = gtk.ListStore(str)
        
        stations = "ARD ZDF Sat.1 Pro7 RTL kabel1 VOX RTL2 SWR WDR NDR MDR RBB HR BR BR alpha SuperRTL Tele5 DMAX 3sat ARTE PHOENIX EinsExtra EinsPlus EinsFestival ZDFdokukanal ZDFinfokanal ZDFtheaterkanal ComedyCentral 9live DASVIERTE Nickelodeon KIKA Eurosport DSF GIGA VIVA MTV N24 n-tv BBC World CNN TRT" 
        for station in stations.split(" "):
            store.append([station])        

        self.get_widget('combobox_station').set_model(store)
        self.get_widget('combobox_station').set_text_column(0)
            
    def run_new(self):       
        self.get_widget('label_headline').set_markup('<b>Neue Sendung hinzufügen:</b>')
     
        dt = datetime.datetime.today()
        self.get_widget('calendar').select_month(dt.month - 1, dt.year)
        self.get_widget('calendar').select_day(dt.day)
     
        self.get_widget('entry_broadcast').set_text('')
        self.get_widget('comboboxentry_station').set_text('')
     
        return self.run()
        
    def run_edit(self, broadcast):
        self.get_widget('label_headline').set_markup('<b>Sendung bearbeiten:</b>')
           
        self.get_widget('entry_broadcast').set_text(broadcast.title)

        dt = datetime.datetime.fromtimestamp(broadcast.datetime)
        self.get_widget('calendar').select_month(dt.month - 1, dt.year)
        self.get_widget('calendar').select_day(dt.day)
        self.get_widget('entry_time').set_text(dt.strftime('%H:%M'))

        self.get_widget('comboboxentry_station').set_text(broadcast.station)
           
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
