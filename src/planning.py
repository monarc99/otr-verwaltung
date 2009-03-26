#!/usr/bin/env python
# -*- coding: utf-8 -*-

class PlanningException(Exception):
    pass

class Planning(list):

    def __init__(self):
        self = []
        self.fields = ()
        
    def append(self, *data):
        if len(data) != 3:
            raise PlanningException, "Wrong data length while calling append"
        else:
            self.append(*data)
                
    def read_config(self, config_data):
        pass
        
    def write_config(self):
        
        
