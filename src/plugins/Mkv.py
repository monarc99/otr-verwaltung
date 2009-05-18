#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pluginsystem import Plugin

class Mkv(Plugin):
    Name = "MKV"
    Desc = "Wandelt avi-Dateien mit Hilfe von mkvmerge in mkv-Dateien um."
    Author = "Benjamin Elbers"
    Configurable = True
    Config = { 'mkvmerge': 'mkvmerge' }
        
    def enable(self):
        print "[Plugin: Play] Enable"        
        
    def disable(self):
        print "[Plugin: Play] Disable"
    
    def configurate(self):
        print "config"
