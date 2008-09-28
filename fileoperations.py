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

import os

def remove_file(filename):
    os.remove(filename)
    
def rename_file(old_filename, new_filename):
    os.rename(old_filename, new_filename)

def move_file(filename, target):
    os.rename(filename, os.join(target, basename(filename)))

def get_size(filename):
    """ Returns a file's size."""
    filestat = os.stat(filename)
    size = filestat.st_size
    
    return size

def get_date(filename):
    """ Returns a file's last changed date."""
    filestat = os.stat(filename)
    date = filestat.st_mtime
    
    return date
