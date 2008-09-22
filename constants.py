#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Author: Benjamin Elbers
#         elbersb@googlemail.com
#
#
# LICENSE: CREATIVE COMMONS
#          Attribution-Noncommercial-Share Alike 2.0 Generic
# http://creativecommons.org/licenses/by-nc-sa/2.0/
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
