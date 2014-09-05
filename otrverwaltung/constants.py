# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

class Section:
    """ Die verschiedenen Ansichten """    
    PLANNING    = 6
    DOWNLOAD    = 7
    """ Geplante Sendungen"""
    OTRKEY      = 0
    """ Nicht dekodiert """
    VIDEO_UNCUT = 1
    VIDEO_CUT   = 2
    ARCHIVE     = 3
    TRASH       = 4
        
class Action:
    # planning
    PLAN_ADD        = 11
    PLAN_REMOVE     = 12
    PLAN_EDIT       = 13
    PLAN_SEARCH     = 14
    # download
    DOWNLOAD_ADD      = 16
    DOWNLOAD_ADD_LINK = 17
    DOWNLOAD_START    = 18
    DOWNLOAD_STOP     = 19
    DOWNLOAD_REMOVE   = 20
    # decode and cut
    DECODE          = 0
    DECODEANDCUT    = 1
    CUT             = 2
    # file movement
    DELETE          = 3
    ARCHIVE         = 4
    RESTORE         = 6
    RENAME          = 7
    NEW_FOLDER      = 8
    REAL_DELETE     = 10

class Cut_action:
    ASK             = 0
    BEST_CUTLIST    = 1
    CHOOSE_CUTLIST  = 2
    MANUALLY        = 3
    LOCAL_CUTLIST   = 4

class Status:
    OK          = 0
    ERROR       = 1
    NOT_DONE    = 2
    
class Format:
    AVI = 0
    HQ  = 1
    MP4 = 2
    HD  = 3
    AC3 = 4
    
class Program:
    AVIDEMUX    = 0
    VIRTUALDUB  = 1
    CUT_INTERFACE = 2
    SMART_MKVMERGE = 3
    
class DownloadTypes:
    TORRENT     = 0
    BASIC       = 1
    OTR_DECODE  = 2
    OTR_CUT     = 3      
    
class DownloadStatus:
    RUNNING     = 0
    STOPPED     = 1
    ERROR       = 2
    FINISHED    = 3
    SEEDING     = 4
