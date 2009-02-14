#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

from baseaction import BaseAction

class Play(BaseAction):
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filename, player):                   
        if not player:
            self.__gui.message_error_box("Es ist kein Player angegeben!")
            return
        
        p = subprocess.Popen([player, filename])
