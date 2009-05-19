#!/usr/bin/env python
# -*- coding: utf-8 -*-

import decodeorcut
import planning
import archive
import files

from constants import Action
    
# TODO: ein bisschen sinnlos; actions können auch direkt aufgerufen werden, oder?    
    
actions = {
    # planning
    Action.PLAN_ADD     : planning.Add,
    Action.PLAN_REMOVE  : planning.Remove,
    Action.PLAN_EDIT    : planning.Edit,
    Action.PLAN_SEARCH  : planning.Search,
    Action.PLAN_RSS     : planning.RSS,
    
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
