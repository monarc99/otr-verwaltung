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

try:
    import gtk
    import pango
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

from basewindow import BaseWindow
import otrpath
from constants import Action, Section, On_Quit

class MainWindow(BaseWindow):
    
    def __init__(self, app, gui):
        self.app = app
        self.gui = gui
    
        widgets = [            
            'toolbar',
            'toolbuttonDecode',
            'toolbuttonDecodeAll',
            'toolbuttonCut',
            'toolbuttonCutAll',
            'toolbuttonDecodeAndCut',
            'toolbuttonDecodeAndCutAll',    

            # sidebar
            'entry_search',
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

            'labelMessage',
            'treeviewFiles',
            ]
                
        builder = self.create_builder("main_window.ui")
                
        BaseWindow.__init__(self, 
                            builder,
                            "main_window",
                            widgets)
       
        self.__setup_widgets(builder)

    def __setup_widgets(self, builder):
        
        # delete-search button image
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        builder.get_object('buttonClear').set_image(image)
    
        # toolbar buttons        
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
            ('real_delete', 'delete.png', "Löschen", Action.REAL_DELETE)
            ]
        
        self.toolbar_buttons = {}
        for key, image_name, text, action in toolbar_buttons:

            image = gtk.image_new_from_file(otrpath.get_image_path(image_name))
            image.show()
            self.toolbar_buttons[key] = gtk.ToolButton(image, text)
            self.toolbar_buttons[key].connect("clicked", self.on_toolbutton_clicked, action)
            self.toolbar_buttons[key].show()
                                
          
        # create sets of toolbuttons
        self.sets_of_toolbars = {
            Section.OTRKEY :    [ self.toolbar_buttons['decode'], self.toolbar_buttons['decodeandcut'], self.toolbar_buttons['delete'] ],
            Section.AVI_UNCUT:  [ self.toolbar_buttons['cut'], self.toolbar_buttons['delete'], self.toolbar_buttons['archive'], self.toolbar_buttons['play'], self.toolbar_buttons['cut_play'] ],
            Section.AVI_CUT:    [ self.toolbar_buttons['archive'], self.toolbar_buttons['delete'], self.toolbar_buttons['cut'], self.toolbar_buttons['play'], self.toolbar_buttons['rename'] ],
            Section.ARCHIVE:    [ self.toolbar_buttons['cut'], self.toolbar_buttons['delete'], self.toolbar_buttons['play'], self.toolbar_buttons['rename'], self.toolbar_buttons['new_folder'] ],
            Section.TRASH:      [ self.toolbar_buttons['real_delete'], self.toolbar_buttons['restore'] ]
        }

                      
        # connect other signals
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
        
        # change font of sidebar
        builder.get_object('labelFilter').modify_font(pango.FontDescription("bold 12"))
        
        for label in ['labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount', 'labelSearch',   'labelOtrkey', 'labelAvi']:
            builder.get_object(label).modify_font(pango.FontDescription("bold"))
        
        # setup the file treeview
        treeview = self.get_widget('treeviewFiles') 
        store = gtk.TreeStore(object, long, float)
        treeview.set_model(store)
            
        # constants for 
        self.FILENAME = 0
        self.SIZE =     1
        self.DATE =     2
                         
        # create the TreeViewColumns to display the data
        column_names = ['Dateiname', 'Größe', 'Geändert']
        tvcolumns = [None] * len(column_names)
                       
        # first column: pixbuf and filename
        cell_renderer_pixbuf = gtk.CellRendererPixbuf()
        tvcolumns[0] = gtk.TreeViewColumn(column_names[0], cell_renderer_pixbuf)
        cell_renderer_text_name = gtk.CellRendererText()
        tvcolumns[0].pack_start(cell_renderer_text_name, False)
        tvcolumns[0].set_cell_data_func(cell_renderer_pixbuf, self.file_pixbuf)
        tvcolumns[0].set_cell_data_func(cell_renderer_text_name, self.file_name)

        # second column: size
        cell_renderer_text_size = gtk.CellRendererText()
        cell_renderer_text_size.set_property('xalign', 1.0) 
        tvcolumns[1] = gtk.TreeViewColumn(column_names[1], cell_renderer_text_size, text=1)
        tvcolumns[1].set_cell_data_func(cell_renderer_text_size, self.file_size)        
        
        # third column: date
        cell_renderer_text_date = gtk.CellRendererText()
        tvcolumns[2] = gtk.TreeViewColumn(column_names[2], cell_renderer_text_date, text=2)
        tvcolumns[2].set_cell_data_func(cell_renderer_text_date, self.file_date)        
                
        # append the columns
        for col in tvcolumns:
            col.set_resizable(True)
            treeview.append_column(col)
        
        # allow multiple selection
        treeselection = treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)
               
        # sorting
        treeview.get_model().set_sort_func(0, self.sort, None)
        treeview.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)
        
        # load pixbufs for treeview
        self.pix_avi = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('avi.png'))      
        self.pix_otrkey = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('decode.png'))
        self.pix_folder = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('folder.png'))
      
    #
    # Convenience methods
    #
    
    def clear_files(self):
        self.get_widget('treeviewFiles').get_model().clear()
    
    def set_toolbar(self, section):
        for toolbutton in self.get_widget('toolbar').get_children():
           self.get_widget('toolbar').remove(toolbutton)
        
        for toolbutton in self.sets_of_toolbars[section]:        
            self.get_widget('toolbar').insert(toolbutton, -1)
     
    def get_selected_filenames(self):
        """ Return the selected filenames """
        selection = self.get_widget('treeviewFiles').get_selection()
            
        def selected_row(model, path, iter, filenames):
            filenames += [self.get_filename(iter)]
        
        filenames = []        
        selection.selected_foreach(selected_row, filenames)      

        return filenames
        
    def append_row_files(self, parent, filename, size, date):               
        data = [filename, size, date]
    
        iter = self.get_widget('treeviewFiles').get_model().append(parent, data)
        return iter
      
    def get_filename(self, iter):
        return self.get_widget('treeviewFiles').get_model().get_value(iter, self.FILENAME)
      
    #
    #  Signal handlers
    #
                  
    def on_menuHelpAbout_activate(self, widget, data=None):
        about_dialog = gtk.AboutDialog()        
        about_dialog.set_transient_for(self.gui.main_window.get_window())
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("OTR-Verwaltung")
        about_dialog.set_version("0.1")
        about_dialog.set_comments("Zum Verwalten von Dateien von onlinetvrecorder.com.")
        about_dialog.set_copyright("Copyright \xc2\xa9 2008 Benjamin Elbers")
        about_dialog.set_authors(["Benjamin Elbers <elbersb@googlemail.com>"])
        about_dialog.set_logo_icon_name(gtk.STOCK_EDIT)            
        about_dialog.run()
        about_dialog.destroy()
    
    def on_menuEditPreferences_activate(self, widget, data=None):
        self.gui.preferences_window.show()
    
    def on_main_window_destroy(self, widget, data=None):        
        gtk.main_quit()
        
    def on_menuFileQuit_activate(self, widget, data=None):        
        gtk.main_quit()
        
    def on_main_window_delete_event(self, widget, data=None):
        # dialog
        if self.app.config.get('common', 'on_quit') == On_Quit.ASK:
            self.gui.dialog_close_minimize.get_widget('checkbutton_keep').set_active(False)
            response = self.gui.dialog_close_minimize.run()
            self.gui.dialog_close_minimize.hide()
            
            if response==On_Quit.MINIMIZE:
                if self.gui.dialog_close_minimize.get_widget('checkbutton_keep').get_active()==True:
                    self.gui.preferences_window.get_widget('radio_minimize').set_active(True)
                    
                self.hide()    
                return True
            
            elif response==On_Quit.QUIT:
                if self.gui.dialog_close_minimize.get_widget('checkbutton_keep').get_active()==True:
                    self.gui.preferences_window.get_widget('radio_quit').set_active(True)
                    
                return False
            
            else: # canceled
                return True
                
        elif self.app.config.get('common', 'on_quit') == On_Quit.MINIMIZE:
            self.hide()
            return True # don't destroy window
        else: # quit
            return False # destroy window
    
    def on_menuEditSearch_activate(self, widget, data=None):
        self.get_widget('entry_search').grab_focus()
    
    # toolbar actions
    def on_toolbutton_clicked(self, button, action):                
        filenames = self.get_selected_filenames() 
        self.app.perform_action(action, filenames)             
                  
    # sidebar
    def on_sidebar_toggled(self, widget, section):
        if widget.get_active() == True:
            self.app.show_section(section)            
    
    def on_buttonClear_clicked(self, widget, data=None):
        self.get_widget('entry_search').set_text("")
    
    def on_entry_search_changed(self, widget, data=None):
        search = widget.get_text()

        if search == "":
            self.app.stop_search()
            
            for label in ['labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount']:
                self.get_widget(label).set_text("")
        else:
            counts_of_section = self.app.start_search(search)
                  
            self.get_widget('labelOtrkeysCount').set_text(counts_of_section[Section.OTRKEY])
            self.get_widget('labelUncutCount').set_text(counts_of_section[Section.AVI_UNCUT])
            self.get_widget('labelCutCount').set_text(counts_of_section[Section.AVI_CUT])                            
            self.get_widget('labelArchiveCount').set_text(counts_of_section[Section.ARCHIVE])    
            self.get_widget('labelTrashCount').set_text(counts_of_section[Section.TRASH])
                      
    def sort(self, model, iter1, iter2, data):
        # sort_func should return: -1 if the iter1 row should precede the iter2 row; 0, if the rows are equal; and, 1 if the iter2 row should precede the iter1 row
        filename_iter1 = self.get_filename(iter1)    
        filename_iter2 = self.get_filename(iter2)
        # why???
        if filename_iter2 == None:
            return -1
        
        iter1_isdir = isdir(filename_iter1)
        iter2_isdir = isdir(filename_iter2)
        
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
            
    # displaying methods for treeviewFiles
    def file_pixbuf(self, column, cell, model, iter):
        filename = model.get_value(iter, self.FILENAME)
        
        if isdir(filename):
            cell.set_property('pixbuf', self.pix_folder)
        else:
            if filename.endswith('.otrkey'):
                cell.set_property('pixbuf', self.pix_otrkey)
            else:
                cell.set_property('pixbuf', self.pix_avi)

    def file_name(self, column, cell, model, iter):            
        cell.set_property('text', basename(model.get_value(iter, self.FILENAME)))

    def file_size(self, column, cell, model, iter):
        filename = model.get_value(iter, self.FILENAME)
        if isdir(filename):
            cell.set_property('text', '')
        else:
            cell.set_property('text', self.humanize_size(model.get_value(iter, self.SIZE)))

    def file_date(self, column, cell, model, iter):
        cell.set_property('text', time.strftime("%a, %d.%m.%Y, %H:%M", time.localtime(model.get_value(iter, self.DATE))))
    
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
    
    def on_header_checkbox_clicked(self, tvcolumn):
        tvcolumn.get_widget().set_active(not tvcolumn.get_widget().get_active())

        self.get_widget('treeviewFiles').get_model().foreach(self.foreach_toggle_checkbox, tvcolumn.get_widget().get_active())

    def foreach_toggle_checkbox(self, model, path, iter, user_data):
        # set boolean value in first column
        model.set_value(iter, self.CHECK, user_data)

    def on_tv_checkbox_clicked(self, cell, path, model):
        model[path][self.CHECK] = not model[path][self.CHECK]
        self.set_checkbox_children(model[path], model[path][self.CHECK])

    # set value recursively
    def set_checkbox_children(self, treemodelrow, value):
        for row in treemodelrow.iterchildren():
            row[self.CHECK] = value
            self.set_checkbox_children(row, value)
