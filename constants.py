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

class Section:
    OTRKEY      = 0
    AVI_UNCUT   = 1
    AVI_CUT     = 2
    ARCHIVE     = 3
    TRASH       = 4
    SEARCH      = 5
    
class Action:
    DECODE          = 0
    DECODEANDCUT    = 1
    CUT             = 2
    DELETE          = 3
    ARCHIVE         = 4
    PLAY            = 5
    RESTORE         = 6
    RENAME          = 7
    NEW_FOLDER      = 8
    CUT_PLAY        = 9

class Cut_action:
    ASK             = 0
    BEST_CUTLIST    = 1
    CHOOSE_CUTLIST  = 2
    MANUALLY        = 3

class Save_Email_Password:
    DONT_SAVE   = 0
    SAVE        = 1

class Status:
    OK          = 0
    ERROR       = 1
    NOT_DONE    = 2
