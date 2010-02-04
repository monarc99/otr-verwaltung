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
