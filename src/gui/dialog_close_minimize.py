#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from basewindow import BaseWindow

class DialogCloseMinimize(BaseWindow):
    
    def __init__(self, parent):                   
        BaseWindow.__init__(self, "dialog_close_minimize.ui", "dialog_close_minimize", parent)
