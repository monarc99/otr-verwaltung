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
    def __init__(self, title, datetime, station):
        self.title = title
        self.datetime = datetime
        self.station = station  

class Planning(list):

    def __init__(self):
        pass         
        
    def append(self, *data):       
        item = PlanningItem(*data)
        self += [item]
        return item    
                
    def read_config(self, config_data):
        for item in config_data.split(';'):                        
            try:
                values = item.split(',')
                
                if len(values) == 5: # compability
                    values = [values[1], values[2], values[3]]
                
                assert len(values) == 3
                
                self.append(values[0], int(values[1]), values[2])
            except AssertionError:
                print "Assertion failed: ", values
                continue
        
    def get_config(self):
        string = ''
        for broadcast in self:
            string += "%s,%i,%s;" % (broadcast.title, broadcast.datetime, broadcast.station)
            
        return string
