#!/usr/bin/env python
# -*- coding: utf-8 -*-

class PlanningItem():
    def __init__(self, status, title, datetime, station, rss_otrkey=""):
        self.status = status        
        self.title = title
        self.datetime = datetime
        self.station = station
        self.rss_otrkey = rss_otrkey        

class Planning(list):

    def __init__(self):
        pass         
        
    def append(self, *data):       
        self += [PlanningItem(*data)]
        
    def get_from_rss(self):
        return [broadcast for broadcast in self if broadcast.status == 1]            
                
    def read_config(self, config_data):
        for item in config_data.split(';'):                        
            try:
                values = item.split(',')
                
                if len(values) == 3: # compability
                    values = [0, values[0], values[1], values[2], ""]
                
                assert len(values) == 5               
                
                self.append(int(values[0]), values[1], int(values[2]), values[3], values[4])
            except AssertionError:
                print "Assertion failed: ", values
                continue
        
    def get_config(self):
        string = ''
        for broadcast in self:
            string += str(broadcast.status) + ',' + broadcast.title + ',' + str(broadcast.datetime) + ',' + broadcast.station + ',' + broadcast.rss_otrkey + ';'
            
        return string
