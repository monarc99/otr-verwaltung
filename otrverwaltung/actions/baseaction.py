#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BaseAction:    
    """ Base class for actions."""    
     
    def __init__(self):
        self.update_list = True
    
    def do(self):
        raise Exception("Override this method!")
