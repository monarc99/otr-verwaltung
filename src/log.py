#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

class Log:
    def __init__(self, screen=True, filename=""):
        self.screen = screen
        
        self.file = None        
        if filename:
            self.file = open(filename, 'w')
    
    def l(self, *messages):
        text = "%s: %s" % (time.strftime("%X"), " ".join(messages))
        
        if self.screen:
            print text
            
        if not self.file == None:
            self.file.write("%s\n\n" % text)
