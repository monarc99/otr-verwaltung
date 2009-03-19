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

from os.path import join, isdir, basename
import sys
import time
import urllib
import webbrowser

import gtk
import pango

from basewindow import BaseWindow
import otrpath
from constants import Action, Section

class MainWindow(BaseWindow):
    
    def __init__(self, app, gui):
        self.app = app
        self.gui = gui
    
        widgets = [            
            'toolbar',

            'eventbox_tasks',
            'progressbar_tasks',
            'label_tasks',

            # sidebar
            'entry_search',
            'eventboxPlanningCurrentCount',
            'labelPlanningCurrentCount',
            'labelPlanningCount',
            'radioPlanning',
            'radioUndecoded',            
            'separator1',
            'labelAvi',
            'radioUncut',
            'radioCut',
            'separator2',
            'radioArchive',
            'separator3',
            'radioTrash',
            'labelOtrkeysCount',
            'labelUncutCount',
            'labelCutCount',
            'labelArchiveCount',
            'labelTrashCount',

            'label_search',
            'eventbox_search',
            'labelMessage',
            'scrolledwindow_planning',
            'treeview_planning',
            'scrolledwindow_files',
            'treeview_files'
            ]
                
        builder = self.create_builder("main_window.ui")
                
        BaseWindow.__init__(self, 
                            builder,
                            "main_window",
                            widgets)
       
        self.__setup_toolbar(builder)
        self.__setup_treeview_planning(builder)
        self.__setup_treeview_files(builder)
        self.__setup_widgets(builder)
        
    def __setup_toolbar(self, builder):       
        toolbar_buttons = [
            ('decode', 'decode.png', 'Dekodieren', Action.DECODE),
            ('decodeandcut', 'decodeandcut.png', "Dekodieren und Schneiden", Action.DECODEANDCUT),
            ('delete', 'delete.png', "In den Müll verschieben", Action.DELETE),
            ('archive', 'archive.png', "Archivieren", Action.ARCHIVE),
            ('cut', 'cut.png', "Schneiden", Action.CUT),
            ('play', 'play.png', "Abspielen", Action.PLAY),
            ('restore', 'restore.png', "Wiederherstellen", Action.RESTORE),
            ('rename', 'rename.png', "Umbenennen", Action.RENAME),
            ('new_folder', 'new_folder.png', "Neuer Ordner", Action.NEW_FOLDER),
            ('cut_play', 'play.png', "Geschnitten Abspielen", Action.CUT_PLAY),
            ('real_delete', 'delete.png', "Löschen", Action.REAL_DELETE),
            ('plan_add', 'film_add.png', "Hinzufügen", Action.PLAN_ADD),
            ('plan_remove', 'film_delete.png', "Löschen", Action.PLAN_REMOVE),
            ('plan_edit', 'film_edit.png', "Bearbeiten", Action.PLAN_EDIT),
            ('plan_search', 'film_search.png', "Auf Mirror suchen", Action.PLAN_SEARCH)
            ]
        
        self.toolbar_buttons = {}
        for key, image_name, text, action in toolbar_buttons:

            image = gtk.image_new_from_file(otrpath.get_image_path(image_name))
            image.show()
            self.toolbar_buttons[key] = gtk.ToolButton(image, text)
            self.toolbar_buttons[key].connect("clicked", self.on_toolbutton_clicked, action)
            self.toolbar_buttons[key].show()
             
             
        self.sets_of_toolbars = {
            Section.PLANNING :  [ 'plan_add', 'plan_edit', 'plan_remove', 'plan_search' ],
            Section.OTRKEY :    [ 'decodeandcut', 'decode', 'delete' ],
            Section.AVI_UNCUT:  [ 'cut', 'delete', 'archive', 'play', 'cut_play' ],
            Section.AVI_CUT:    [ 'archive', 'delete', 'cut', 'play', 'rename' ],
            Section.ARCHIVE:    [ 'delete', 'play', 'rename', 'new_folder' ],
            Section.TRASH:      [ 'real_delete', 'restore' ]
        }                       

        # create sets of toolbuttons          
        for section, button_names in self.sets_of_toolbars.iteritems():
            toolbar_buttons = []
            for button_name in button_names:
                toolbar_buttons.append(self.toolbar_buttons[button_name])
                
            self.sets_of_toolbars[section] = toolbar_buttons
    
    def __setup_treeview_planning(self, builder):
        treeview = self.get_widget('treeview_planning') 
        store = gtk.TreeStore(int, str, str, str)                        
        treeview.set_model(store)
        
        # create the TreeViewColumns to display the data
        column_names = [ 'Sendung', 'Datum/Zeit', 'Sender' ]
        tvcolumns = [None] * len(column_names)
                             
        tvcolumns[0] = gtk.TreeViewColumn(column_names[0], gtk.CellRendererText(), markup=1)
        tvcolumns[1] = gtk.TreeViewColumn(column_names[1], gtk.CellRendererText(), markup=2)        
        tvcolumns[2] = gtk.TreeViewColumn(column_names[2], gtk.CellRendererText(), markup=3)
       
        # append the columns
        for col in tvcolumns:
            col.set_resizable(True)
            treeview.append_column(col)
        
        # allow multiple selection
        treeselection = treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)
               
        # sorting
        treeview.get_model().set_sort_func(0, self.tv_planning_sort, None)
        treeview.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)    
    
    def __setup_treeview_files(self, builder):
        treeview = self.get_widget('treeview_files') 
        store = gtk.TreeStore(str, str, str, bool) # filename, size, date, locked
        treeview.set_model(store)
            
        # constants for model and columns
        self.FILENAME = 0
        self.SIZE =     1
        self.DATE =     2
        
        # create the TreeViewColumns to display the data
        column_names = ['Dateiname', 'Größe', 'Geändert' ]                       
        tvcolumns = [None] * len(column_names)
                       
        # pixbuf and filename
        cell_renderer_pixbuf = gtk.CellRendererPixbuf()
        tvcolumns[self.FILENAME] = gtk.TreeViewColumn(column_names[self.FILENAME], cell_renderer_pixbuf)
        cell_renderer_text_name = gtk.CellRendererText()
        tvcolumns[self.FILENAME].pack_start(cell_renderer_text_name, False)
        tvcolumns[self.FILENAME].set_cell_data_func(cell_renderer_pixbuf, self.tv_files_pixbuf)
        tvcolumns[self.FILENAME].set_cell_data_func(cell_renderer_text_name, self.tv_files_name)

        # size
        cell_renderer_text_size = gtk.CellRendererText()
        cell_renderer_text_size.set_property('xalign', 1.0) 
        tvcolumns[self.SIZE] = gtk.TreeViewColumn(column_names[self.SIZE], cell_renderer_text_size, text=self.SIZE)        
        
        # date
        tvcolumns[self.DATE] = gtk.TreeViewColumn(column_names[self.DATE], gtk.CellRendererText(), text=self.DATE)        

        # append the columns
        for col in tvcolumns:
            col.set_resizable(True)
            treeview.append_column(col)
        
        # allow multiple selection
        treeselection = treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)
               
        # sorting
        treeview.get_model().set_sort_func(0, self.tv_files_sort, None)
        treeview.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)
        
        # load pixbufs for treeview
        self.pix_avi = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('avi.png'))      
        self.pix_otrkey = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('decode.png'))
        self.pix_folder = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('folder.png'))

    def __setup_widgets(self, builder):
        
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
        
        # delete-search button image
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        builder.get_object('buttonClear').set_image(image)
                      
        # connect other signals
        self.get_widget('radioPlanning').connect('clicked', self.on_sidebar_toggled, Section.PLANNING)
        self.get_widget('radioUndecoded').connect('clicked', self.on_sidebar_toggled, Section.OTRKEY)
        self.get_widget('radioUncut').connect('clicked', self.on_sidebar_toggled, Section.AVI_UNCUT)
        self.get_widget('radioCut').connect('clicked', self.on_sidebar_toggled, Section.AVI_CUT)
        self.get_widget('radioArchive').connect('clicked', self.on_sidebar_toggled, Section.ARCHIVE)  
        self.get_widget('radioTrash').connect('clicked', self.on_sidebar_toggled, Section.TRASH)
        
        # change background of sidebar
        eventbox = builder.get_object('eventboxSidebar')
        cmap = eventbox.get_colormap()
        colour = cmap.alloc_color("gray")
        style = eventbox.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = colour
        eventbox.set_style(style)

        style = builder.get_object('eventboxPlanningCurrentCount').get_style().copy()
        pixmap, mask = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('badge.png')).render_pixmap_and_mask()
        style.bg_pixmap[gtk.STATE_NORMAL] = pixmap        
        builder.get_object('eventboxPlanningCurrentCount').shape_combine_mask(mask, 0, 0)        
        builder.get_object('eventboxPlanningCurrentCount').set_style(style)

        # change font of sidebar     
        for label in ['labelPlanningCount', 'labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount', 'labelOtrkey', 'labelAvi', 'labelPlanningCurrentCount']:
            builder.get_object(label).modify_font(pango.FontDescription("bold"))

        # change background of tasks and searchbar
        for eventbox in ['eventbox_tasks', 'eventbox_search']:
            eventbox = builder.get_object(eventbox)
            cmap = eventbox.get_colormap()
            colour = cmap.alloc_color("#FFF288")
            style = eventbox.get_style().copy()
            style.bg[gtk.STATE_NORMAL] = colour
            eventbox.set_style(style)

        # image cancel
        builder.get_object('image_cancel').set_from_file(otrpath.get_image_path('cancel.png'))
        
      
    #
    # treeview_files
    #
    
    def clear_files(self):
        self.get_widget('treeview_files').get_model().clear()
        self.get_widget('treeview_planning').get_model().clear()
    
    def get_selected_filenames(self):
        """ Return the selected filenames """
        selection = self.get_widget('treeview_files').get_selection()
            
        def selected_row(model, path, iter, filenames):
            filenames += [self.get_widget('treeview_files').get_model().get_value(iter, self.FILENAME)]
        
        filenames = []        
        selection.selected_foreach(selected_row, filenames)      

        return filenames
        
    def append_row_files(self, parent, filename, size, date, locked=False):               

        if isdir(filename):
            size = ''
        else:
            size = self.humanize_size(size)

        date = time.strftime("%a, %d.%m.%Y, %H:%M", time.localtime(date))
    
        data = [filename, size, date, locked]
    
        iter = self.get_widget('treeview_files').get_model().append(parent, data)
        return iter
   
    def humanize_size(self, size):
        abbrevs = [
            (1<<30L, 'GB'), 
            (1<<20L, 'MB'), 
            (1<<10L, 'k'),
            (1, '')
        ]

        for factor, suffix in abbrevs:
            if size > factor:
                break
        return `int(size/factor)` + ' ' + suffix
       
    def tv_files_sort(self, model, iter1, iter2, data):
        # -1 if the iter1 row should precede the iter2 row; 0, if the rows are equal; and, 1 if the iter2 row should precede the iter1 row
         
        filename_iter1 = model.get_value(iter1, self.FILENAME)    
        filename_iter2 = model.get_value(iter2, self.FILENAME)
        
        # why???
        if filename_iter2 == None:
            return -1
        
        iter1_isdir, iter2_isdir = isdir(filename_iter1), isdir(filename_iter2)
        
        if iter1_isdir and iter2_isdir: # both are folders
            # put names into array
            folders = [ filename_iter1, filename_iter2 ]
            # sort them
            folders.sort()
            # check if the first element is still iter1
            if folders[0] == filename_iter1:
                return -1
            else:
                return 1
                
        elif iter1_isdir: # only iter1 is a folder
            return -1
        elif iter2_isdir: # only iter2 is a folder
            return 1
        else: # none of them is a folder
            return 0
            
    # displaying methods for treeview_files
    def tv_files_name(self, column, cell, model, iter):            
        cell.set_property('text', basename(model.get_value(iter, self.FILENAME)))

    def tv_files_pixbuf(self, column, cell, model, iter):
        filename = model.get_value(iter, self.FILENAME)
    
        if isdir(filename):
            cell.set_property('pixbuf', self.pix_folder)
        else:
            if filename.endswith('.otrkey'):
                cell.set_property('pixbuf', self.pix_otrkey)
            else:
                cell.set_property('pixbuf', self.pix_avi)

    #
    # treeview_planning
    #
            
    def get_selected_broadcasts(self):
        """ Return the selected filenames """
        selection = self.get_widget('treeview_planning').get_selection()
            
        def selected_row(model, path, iter, broadcasts):
            broadcasts += [iter]
        
        broadcasts = []        
        selection.selected_foreach(selected_row, broadcasts)      

        return broadcasts
               
    def append_row_planning(self, index):
        broadcast, stamp, station = self.app.planned_broadcasts[index]
        datetime = time.strftime("%a, %d.%m.%Y, %H:%M", time.localtime(stamp))
    
        now = time.time()

        if stamp < now: 
            # everything bold
            data = [index, "<b>%s</b>" % broadcast, "<b>%s</b>" % datetime, "<b>%s</b>" % station]
        else:
            data = [index, broadcast, datetime, station]
              
        iter = self.get_widget('treeview_planning').get_model().append(None, data)
        return iter

    def tv_planning_sort(self, model, iter1, iter2, data):
        # -1 if the iter1 row should precede the iter2 row; 0, if the rows are equal; and, 1 if the iter2 row should precede the iter1 row              
        time1 = self.app.planned_broadcasts[model.get_value(iter1, 0)][1]
        time2 = self.app.planned_broadcasts[model.get_value(iter2, 0)][1]

        if time1 > time2:
            return 1
        elif time1 < time2:
            return -1
        else:
            return 0
        
    #
    # Convenience
    #       
    
    def set_toolbar(self, section):
        for toolbutton in self.get_widget('toolbar').get_children():
           self.get_widget('toolbar').remove(toolbutton)
        
        for toolbutton in self.sets_of_toolbars[section]:        
            self.get_widget('toolbar').insert(toolbutton, -1)
                
    def show_planning(self, planning):
        self.get_widget('scrolledwindow_files').props.visible = not planning
        self.get_widget('scrolledwindow_planning').props.visible = planning
     
    def block_gui(self, state):
        for button in ["decode", "cut", "decodeandcut"]:
            self.toolbar_buttons[button].set_sensitive(not state)
     
    def broadcasts_badge(self):
        count = 0
        now = time.time()
        for broadcast in self.app.planned_broadcasts:
            stamp = broadcast[1]
            if stamp < now:
                count += 1
    
        if count == 0:
            self.get_widget('eventboxPlanningCurrentCount').hide()
        else:
            self.get_widget('eventboxPlanningCurrentCount').show()
            self.get_widget('labelPlanningCurrentCount').set_text(str(count))
      
    #
    #  Signal handlers
    #
    
    def on_menu_check_update_activate(self, widget, data=None):
        current_version = open(otrpath.get_path("VERSION"), 'r').read().strip()
    
        try:
            svn_version = urllib.urlopen('http://otr-verwaltung.googlecode.com/svn/trunk/src/STABLEVERSION').read().strip()
        except IOError, AssertionError:
            self.gui.message_error_box("Konnte keine Verbindung mit dem Internet herstellen!")
            return
        
        print svn_version
        
        current_version = current_version.split(".")   # 0.5.4
        svn_version = svn_version(".")                 # 1.0.0, 0.5.7
        
        if svn_version[0] > current_version[0] or svn_version[1] > current_version[1] or svn_version[2] > current_version[2]:
            self.gui.message_info_box("Es steht eine neue Version bereit: %s\n\n(Ihre Version ist %s.)" % (svn_version, current_version))            

                      
    def on_menuHelpAbout_activate(self, widget, data=None):

        def open_website(dialog, url, data=None):
            webbrowser.open(url)

        gtk.about_dialog_set_url_hook(open_website)

        about_dialog = gtk.AboutDialog()        
        about_dialog.set_transient_for(self.gui.main_window.get_window())
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("OTR-Verwaltung")
        about_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('icon3.png')))
        
        version = open(otrpath.get_path("VERSION"), 'r')        
        about_dialog.set_version(version.read().strip())
        about_dialog.set_website("http://code.google.com/p/otr-verwaltung/")
        about_dialog.set_comments("Zum Verwalten von Dateien von onlinetvrecorder.com.")
        about_dialog.set_copyright("Copyright \xc2\xa9 2008 Benjamin Elbers")
        about_dialog.set_authors(["Benjamin Elbers <elbersb@googlemail.com>"])
        about_dialog.run()
        about_dialog.destroy()
    
    def on_menuEditPreferences_activate(self, widget, data=None):
        self.gui.preferences_window.show()
    
    def on_main_window_destroy(self, widget, data=None):        
        gtk.main_quit()
        
    def on_menuFileQuit_activate(self, widget, data=None):        
        gtk.main_quit()
           
    def on_menuEditSearch_activate(self, widget, data=None):
        entry_search = self.get_widget('entry_search')
        
        if entry_search.get_text() == "Durchsuchen":
            entry_search.set_text('')
        
        entry_search.grab_focus()
    
    # toolbar actions
    def on_toolbutton_clicked(self, button, action):                
        filenames = self.get_selected_filenames()
        broadcasts = self.get_selected_broadcasts()
        self.app.perform_action(action, filenames, broadcasts)             
                  
    # sidebar
    def on_sidebar_toggled(self, widget, section):
        if widget.get_active() == True:
            self.app.show_section(section)            
    
    def on_buttonClear_clicked(self, widget, data=None):
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
        self.get_widget('entry_search').set_text("Durchsuchen")
   
    def on_entry_search_button_press_event(self, widget, data=None):
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        if self.get_widget('entry_search').get_text() == "Durchsuchen":
            self.get_widget('entry_search').set_text("")
    
    def on_entry_search_focus_out_event(self, widget, data=None):
        if self.get_widget('entry_search').get_text() == "":
            self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
            self.get_widget('entry_search').set_text("Durchsuchen")
            
    def on_entry_search_changed(self, widget, data=None):
        search = widget.get_text()

        self.do_search(search)
    
    def do_search(self, search):
        if search == "Durchsuchen" or search == "":
            self.app.stop_search()
            
            self.get_widget('eventbox_search').hide()
            
            for label in ['labelPlanningCount', 'labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount']:
                self.get_widget(label).set_text("")
        else:
            self.get_widget('eventbox_search').show()
            self.get_widget('label_search').set_markup("<b>Suchergebnisse für '%s'</b>" % search)
        
            counts_of_section = self.app.start_search(search)
                  
            self.get_widget('labelPlanningCount').set_text(counts_of_section[Section.PLANNING])                  
            self.get_widget('labelOtrkeysCount').set_text(counts_of_section[Section.OTRKEY])
            self.get_widget('labelUncutCount').set_text(counts_of_section[Section.AVI_UNCUT])
            self.get_widget('labelCutCount').set_text(counts_of_section[Section.AVI_CUT])     
            self.get_widget('labelArchiveCount').set_text(counts_of_section[Section.ARCHIVE])    
            self.get_widget('labelTrashCount').set_text(counts_of_section[Section.TRASH])
       
    def on_eventbox_cancel_button_press_event(self, widget, data=None):
        # TODO: Cancel of cut and decode
        pass
        
    def on_eventboxPlanningCurrentCount_button_release_event(self, widget, data=None):
        # show section
        self.get_widget('radioPlanning').set_active(True)
        
        # select already broadcasted
        selection = self.get_widget('treeview_planning').get_selection()
        selection.unselect_all()
        now = time.time()
                
        def foreach(model, path, iter, data=None):
            index = model.get_value(iter, 0)
            stamp = self.app.planned_broadcasts[index][1]

            if stamp < now:
                selection.select_iter(iter)

        self.get_widget('treeview_planning').get_model().foreach(foreach)
