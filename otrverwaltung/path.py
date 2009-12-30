#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import join, isdir
import os

import os
from xdg import BaseDirectory

data_dir = "../data"

def getdatapath(*args):
    """Retrieve otrverwaltung data path

    This path is by default <mfm_lib_path>/../data/ in trunk
    and /usr/share/mfm in an installed version but this path
    is specified at installation time.
    """
    return os.path.join(os.path.dirname(__file__), data_dir, *args)
      
def get_storage_dir(filename=""):
    return os.path.join(BaseDirectory.xdg_data_home, "otrverwaltung", filename)

def get_config_path(filename):
    home = os.environ.get('HOME')
    config_dir = join(home, '.otr-verwaltung')
    if not isdir(config_dir):
        os.mkdir(config_dir)
    return join(config_dir, filename)
    # TODO: Change eventually:
    # return os.path.join(BaseDirectory.xdg_config_home, "mfm", filename)

def get_path(filename=""):
    return join(sys.path[0], "otrverwaltung", filename)

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
    
def get_image_path(filename=""):
    return join(getdatapath("media", filename))
