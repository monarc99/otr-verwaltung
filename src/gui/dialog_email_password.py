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

import gtk

from basewindow import BaseWindow

class DialogEmailPassword(BaseWindow):
    
    def __init__(self, parent):
        widgets = [           
            'entryDialogEMail',
            'entryDialogPassword'
            ]
            
        builder = self.create_builder("dialog_email_password.ui")
        
        BaseWindow.__init__(self, builder, "dialog_email_password", widgets, parent)
        
        self.get_widget('entryDialogPassword').set_visibility(False)
