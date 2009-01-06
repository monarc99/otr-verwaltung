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

from os import remove, rename, stat
from os.path import join, basename

# TODO: Achten auf :/\* etc. in Dateiname!
# TODO: Fehler abfangen, fehlerwert zurückgeben, damit das Programm weitermachen kann

def remove_file(filename):
    remove(filename)
    
def rename_file(old_filename, new_filename):
    rename(old_filename, new_filename)

def move_file(filename, target):
    rename(filename, join(target, basename(filename)))

def get_size(filename):
    """ Returns a file's size."""
    filestat = stat(filename)
    size = filestat.st_size
    
    return size

def get_date(filename):
    """ Returns a file's last changed date."""
    filestat = stat(filename)
    date = filestat.st_mtime
    
    return date
