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

import pynotify

try:
    import gtk
    import pygtk
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

from basewindow import BaseWindow

from otrpath import get_image_path

class Notify(BaseWindow):
    
    def __init__(self, app, parent):                     
        self.app = app
        self.main_window = parent
        
        widgets = [
            'status_menu'
            ]
        
        builder = self.create_builder("status_menu.ui")    
        BaseWindow.__init__(self, builder, "status_menu", widgets)
     
        # status icon
        status_icon = self.create_widget('status', gtk.StatusIcon())
        # TODO: path
        status_icon.set_from_file(get_image_path('icon3.png'))
        status_icon.set_tooltip("OTR-Verwaltung")
        status_icon.connect("activate", self.on_status_clicked)
        status_icon.connect("popup_menu", self.on_status_popup_menu)
        status_icon.set_visible(True)
        
        # popup
        pynotify.init("pynotify")
        
    ###
    ### Convenience methods
    ###

    def popup(self, title, text, seconds):
        notify = pynotify.Notification(title, text, "pynotify")
    	notify.set_urgency(pynotify.URGENCY_NORMAL)
    	notify.attach_to_status_icon(self.get_widget("status"))
    	notify.set_timeout(seconds * 1000)
    	notify.show()         

    ###
    ### Helpers
    ###
    
    def __show_main_window(self):
        if self.app.blocked == False:
            # show/hide main window
            if self.main_window.get_window().props.visible:
                self.main_window.hide()
            else:
                self.main_window.show()
        else:
            # when blocked, don't show main window but a notification
            self.popup("OTR-Verwaltung arbeitet gerade...", self.app.get_notify_text(), 3)
    
    def __show_context_menu(self, button=None, activate_time=None):
        if self.app.blocked == False:
            # show context menu
            self.get_widget('status_menu').popup(None, None, None, button, activate_time)        
        else:
            # when blocked, don't show context menu but a notification
            self.popup("OTR-Verwaltung arbeitet gerade...", self.app.get_notify_text(), 3)

    ###
    ### Signal handlers
    ###
    
    # status icons
    def on_status_clicked(self, widget, data=None):
        self.__show_main_window()

    def on_status_popup_menu(self, widget, button, activate_time, data=None):        
        self.__show_context_menu(button, activate_time)
        
    # menu items
    def on_status_menu_open_activate(self, widget, data=None):
        self.__show_main_window()
      
    def on_status_menu_quit_activate(self, widget, data=None):
        gtk.main_quit()
         
