#!/usr/bin/env python
# -*- coding: utf-8 -*-

import decodeorcut
import cutplay
import play
import planning
import archive
import files

from constants import Action
    
actions = {
    Action.PLAN_ADD     : planning.Add,
    Action.PLAN_REMOVE  : planning.Remove,
    Action.PLAN_EDIT    : planning.Edit,
    Action.PLAN_SEARCH  : planning.Search,
    Action.DECODEANDCUT : decodeorcut.DecodeOrCut,
    Action.DECODE       : decodeorcut.DecodeOrCut,
    Action.CUT          : decodeorcut.DecodeOrCut,
    Action.DELETE       : files.Delete,
    Action.ARCHIVE      : archive.Archive,
    Action.PLAY         : play.Play,
    Action.RESTORE      : files.Restore,
    Action.RENAME       : files.Rename,
    Action.NEW_FOLDER   : files.NewFolder,
    Action.CUT_PLAY     : cutplay.CutPlay,
    Action.REAL_DELETE  : files.RealDelete
        }
        
def get_action(action, gui):
    action = actions[action](gui)
    
    return action
