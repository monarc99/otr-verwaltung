#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import join, isdir
import os

def get_config_path(filename):
    home = os.environ.get('HOME')
    config_dir = join(home, '.otr-verwaltung')
    if not isdir(config_dir):
        os.mkdir(config_dir)
    return join(config_dir, filename)

def get_path(filename=None):
    if filename == None:
        return sys.path[0]
    else:
        return join(sys.path[0], filename)

def get_plugin_paths():
    plugins_home = get_config_path('plugins')
    if not isdir(plugins_home):
        os.mkdir(plugins_home)
    plugins_usr = get_path('plugins')
    return plugins_home, plugins_usr
    
def get_gui_path(filename=None):
    if filename == None:
        return join(get_path(), "gui")
    else:
        return join(get_path(), join("gui", filename))
    
def get_image_path(filename=None):
    if filename == None:
        return join(get_path(), "images")
    else:
        return join(get_path(), join("images", filename))
    
    
