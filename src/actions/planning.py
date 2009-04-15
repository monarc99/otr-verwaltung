#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gtk import RESPONSE_OK
import time
import webbrowser
import urllib2
import xml.dom.minidom
import hashlib

from baseaction import BaseAction

class Add(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, planned_broadcasts):
        if self.__gui.dialog_planning.run_new() == RESPONSE_OK:           
            broadcast, datetime, station = self.__gui.dialog_planning.get_values()
            planned_broadcasts.append(0, broadcast, datetime, station)
            
            self.__gui.main_window.broadcasts_badge()
            
        self.__gui.dialog_planning.hide()
        

class Edit(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, broadcast, planned_broadcasts):
        index = self.__gui.main_window.get_widget('treeview_planning').get_model().get_value(broadcast, 0)
        
        if self.__gui.dialog_planning.run_edit(planned_broadcasts[index]) == RESPONSE_OK:
            title, datetime, station = self.__gui.dialog_planning.get_values()
            planned_broadcasts[index].title = title
            planned_broadcasts[index].datetime = datetime
            planned_broadcasts[index].station = station
            
            self.__gui.main_window.broadcasts_badge()            
            
        self.__gui.dialog_planning.hide()

class Remove(BaseAction):    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, broadcasts, planned_broadcasts):
        if len(broadcasts) == 1:
            message = "Es ist eine Sendung ausgewählt. Soll diese Sendung "
        else:
            message = "Es sind %s Sendungen ausgewählt. Sollen diese Sendungen " % len(broadcasts)
        
        if self.__gui.question_box(message + "gelöscht werden?"):
            # convert indices to references in the list
            items = []
            for iter in broadcasts:
                index = self.__gui.main_window.get_widget('treeview_planning').get_model().get_value(iter, 0)
                items.append(planned_broadcasts[index])
            for item in items:
                planned_broadcasts.remove(item)
            
            self.__gui.main_window.broadcasts_badge()            
            
class Search(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui
        
    def do(self, broadcasts, planned_broadcasts):
        for broadcast in broadcasts:
            index = self.__gui.main_window.get_widget('treeview_planning').get_model().get_value(broadcast, 0)
            broadcast = planned_broadcasts[index]
                        
            # build string: Titanic_08.12.24_20-15_pro7_
            string = broadcast.title.replace(' ', '_') + ' '
            string += time.strftime("%y.%m.%d_%H-%M", time.localtime(broadcast.datetime)) + "_"
            string += broadcast.station + "_"
            
            webbrowser.open("http://www.otr-search.com/?q=%s" % string)
            
class RSS(BaseAction):
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui
    
    def do(self, planned_broadcasts, email, password):
        if not email or not rss_hash:
            self.__gui.message_error_box("E-Mail oder Hash sind nicht richtig eingetragen!")
        
        url = "http://www.onlinetvrecorder.com/rss/my.php?email=%s&hash=%s" % (email, hashlib.md5(password).hexdigest())    
        print url        
        
        rss_file = urllib2.urlopen(url)
        print rss_file.read()
                 
        # rss_otrkeys = []                  
                 
        # dom = xml.dom.minidom.parse(rss_file)
        # handle.close()
        # dom_x = dom_cutlists.getElementsByTagName('x')

        # elements = cutlist_element.getElementsByTagName(node_name)
        # for node in elements[0].childNodes:
        #    return node.nodeValue                    
        
        from_rss = planned_broadcasts.get_from_rss()
        
        for rss_otrkey in rss_otrkeys:
            # search for this otrkey in existing broadcasts
            for local_rss_otrkey in from_rss:
                if rss_otrkey == local_rss_otrkey:
                    continue # already local
                
                # get: title, datetime, station from rss_otrkey
                title = None               
                datetime = None
                station = None
                planned_broadcasts.append(1, title, datetime, station, rss_otrkey)
