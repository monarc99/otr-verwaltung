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

from otrverwaltung.actions import decodeorcut
from otrverwaltung.actions import planning
from otrverwaltung.actions import archive
from otrverwaltung.actions import files

from otrverwaltung.constants import Action
    
# TODO: ein bisschen sinnlos; actions können auch direkt aufgerufen werden, oder?    
    
actions = {
    # planning
    Action.PLAN_ADD     : planning.Add,
    Action.PLAN_REMOVE  : planning.Remove,
    Action.PLAN_EDIT    : planning.Edit,
    Action.PLAN_SEARCH  : planning.Search,
    
    # decode and cut
    Action.DECODEANDCUT : decodeorcut.DecodeOrCut,
    Action.DECODE       : decodeorcut.DecodeOrCut,
    Action.CUT          : decodeorcut.DecodeOrCut,
    
    # file movement
    # TODO: archive in "files"
    Action.ARCHIVE      : archive.Archive,
    Action.DELETE       : files.Delete,
    Action.RESTORE      : files.Restore,
    Action.RENAME       : files.Rename,
    Action.NEW_FOLDER   : files.NewFolder,
    Action.REAL_DELETE  : files.RealDelete
        }
        
def get_action(action, gui):
    action = actions[action](gui)
    
    return action
