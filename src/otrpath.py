#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

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
    
    
