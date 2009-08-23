#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join, isdir, basename, splitext
import sys
import time
import urllib
import webbrowser
import subprocess


import gtk
import pango

from basewindow import BaseWindow
import otrpath
from constants import Action, Section, Cut_action
from GeneratorTask import GeneratorTask

class MainWindow(BaseWindow):
    
    def __init__(self, app, gui):
        self.__app = app
        self.__gui = gui      
                
        BaseWindow.__init__(self, "main_window")
       
        self.__setup_toolbar()
        self.__setup_treeview_planning()
        self.__setup_treeview_files()
        self.__setup_widgets()
    
    def __get_cut_menu(self, action):
        # menu for cut/decodeandcut
        cut_menu = gtk.Menu()
        items = [
            ("Nachfragen", Cut_action.ASK),
            ("Beste Cutlist", Cut_action.BEST_CUTLIST),
            ("Cutlist wählen", Cut_action.CHOOSE_CUTLIST),
            ("Lokale Cutlist", Cut_action.LOCAL_CUTLIST),
            ("Manuell (und Cutlist erstellen)", Cut_action.MANUALLY)
        ]
       
        for label, cut_action in items:
            item = gtk.MenuItem(label)
            item.show()
            item.connect("activate", self._on_toolbutton_clicked, action, cut_action)
            cut_menu.add(item)
        
        return cut_menu
    
    def __setup_toolbar(self):
    
        toolbar_buttons = [
            ('decodeandcut', 'decodeandcut.png', "Dekodieren und Schneiden", Action.DECODEANDCUT),
            ('decode', 'decode.png', 'Dekodieren', Action.DECODE),
            ('delete', 'delete.png', "In den Müll verschieben", Action.DELETE),
            ('archive', 'archive.png', "Archivieren", Action.ARCHIVE),
            ('cut', 'cut.png', "Schneiden", Action.CUT),          
            ('restore', 'restore.png', "Wiederherstellen", Action.RESTORE),
            ('rename', 'rename.png', "Umbenennen", Action.RENAME),
            ('new_folder', 'new_folder.png', "Neuer Ordner", Action.NEW_FOLDER),            
            ('real_delete', 'delete.png', "Löschen", Action.REAL_DELETE),
            ('plan_add', 'film_add.png', "Hinzufügen", Action.PLAN_ADD),
            ('plan_remove', 'film_delete.png', "Löschen", Action.PLAN_REMOVE),
            ('plan_edit', 'film_edit.png', "Bearbeiten", Action.PLAN_EDIT),
            ('plan_search', 'film_search.png', "Auf Mirror suchen", Action.PLAN_SEARCH),
            ('plan_rss', 'rss_go.png', "Von OTR aktualisieren", Action.PLAN_RSS)
            ]
        
        self.__toolbar_buttons = {}
        for key, image_name, text, action in toolbar_buttons:
            image = gtk.image_new_from_file(otrpath.get_image_path(image_name))
            image.show()
            
            if key == "cut" or key == "decodeandcut":
                self.__toolbar_buttons[key] = gtk.MenuToolButton(image, text)
                self.__toolbar_buttons[key].set_menu(self.__get_cut_menu(action))
            else:
                self.__toolbar_buttons[key] = gtk.ToolButton(image, text)

            self.__toolbar_buttons[key].connect("clicked", self._on_toolbutton_clicked, action)              
            self.__toolbar_buttons[key].show()
             
        self.__sets_of_toolbars = {
            Section.PLANNING :   [ 'plan_add', 'plan_edit', 'plan_remove', 'plan_search'],# 'plan_rss' ],
            Section.OTRKEY :     [ 'decodeandcut', 'decode', 'delete' ],
            Section.VIDEO_UNCUT: [ 'cut', 'delete', 'archive', ],
            Section.VIDEO_CUT:   [ 'archive', 'delete', 'cut', 'rename' ],
            Section.ARCHIVE:     [ 'delete', 'rename', 'new_folder' ],
            Section.TRASH:       [ 'real_delete', 'restore' ]
        }           

        # create sets of toolbuttons          
        for section, button_names in self.__sets_of_toolbars.iteritems():
            toolbar_buttons = []
            for button_name in button_names:
                toolbar_buttons.append(self.__toolbar_buttons[button_name])
                
            self.__sets_of_toolbars[section] = toolbar_buttons
   
    def add_toolbutton(self, image, text, sections):
        """ Fügt einen neuen Toolbutton hinzu. 
              image ein gtk.Image() 
              text Text des Toolbuttons 
              sections Liste von Sections, in denen der Toolbutton angezeigt wird. """
        
        image.show()
        toolbutton = gtk.ToolButton(image, text)
        toolbutton.show()
        
        for section in sections:            
            self.__sets_of_toolbars[section].append(toolbutton)

        self.set_toolbar(self.__app.section)
        return toolbutton
        
    def remove_toolbutton(self, toolbutton):
        """ Entfernt den angegebenen toolbutton.
              toolbutton"""
    
        for section in self.__sets_of_toolbars.keys():
            if toolbutton in self.__sets_of_toolbars[section]:
                self.__sets_of_toolbars[section].remove(toolbutton)

        self.set_toolbar(self.__app.section)    
    
    def __setup_treeview_planning(self):
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
        treeview.get_model().set_sort_func(0, self.__tv_planning_sort, None)
        treeview.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)    
    
    def __setup_treeview_files(self):
        treeview = self.get_widget('treeview_files') 
        store = gtk.TreeStore(str, str, str, bool) # filename, size, date, locked
        treeview.set_model(store)
            
        # constants for model and columns
        self.__FILENAME = 0
        self.__SIZE =     1
        self.__DATE =     2
        
        # create the TreeViewColumns to display the data
        column_names = ['Dateiname', 'Größe', 'Geändert' ]                       
        tvcolumns = [None] * len(column_names)
                       
        # pixbuf and filename
        cell_renderer_pixbuf = gtk.CellRendererPixbuf()
        tvcolumns[self.__FILENAME] = gtk.TreeViewColumn(column_names[self.__FILENAME], cell_renderer_pixbuf)
        cell_renderer_text_name = gtk.CellRendererText()
        tvcolumns[self.__FILENAME].pack_start(cell_renderer_text_name, False)
        tvcolumns[self.__FILENAME].set_cell_data_func(cell_renderer_pixbuf, self.__tv_files_pixbuf)
        tvcolumns[self.__FILENAME].set_cell_data_func(cell_renderer_text_name, self.__tv_files_name)

        # size
        cell_renderer_text_size = gtk.CellRendererText()
        cell_renderer_text_size.set_property('xalign', 1.0) 
        tvcolumns[self.__SIZE] = gtk.TreeViewColumn(column_names[self.__SIZE], cell_renderer_text_size, text=self.__SIZE)        
        
        # date
        tvcolumns[self.__DATE] = gtk.TreeViewColumn(column_names[self.__DATE], gtk.CellRendererText(), text=self.__DATE)        

        # append the columns
        for col in tvcolumns:
            col.set_resizable(True)
            treeview.append_column(col)
        
        # allow multiple selection
        treeselection = treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)        
               
        # sorting
        treeview.get_model().set_sort_func(0, self.__tv_files_sort, None)
        treeview.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)
        
        # load pixbufs for treeview
        self.__pix_avi = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('avi.png'))      
        self.__pix_otrkey = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('decode.png'))
        self.__pix_folder = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('folder.png'))

    def __setup_widgets(self):        
        self.get_widget('menu_bottom').set_active(self.__app.config.get('show_bottom'))
        
        self.get_widget('image_status').clear()
        
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
        
        # delete-search button image
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        self.get_widget('buttonClear').set_image(image)
                      
        # connect other signals
        self.get_widget('radioPlanning').connect('clicked', self._on_sidebar_toggled, Section.PLANNING)
        self.get_widget('radioUndecoded').connect('clicked', self._on_sidebar_toggled, Section.OTRKEY)
        self.get_widget('radioUncut').connect('clicked', self._on_sidebar_toggled, Section.VIDEO_UNCUT)
        self.get_widget('radioCut').connect('clicked', self._on_sidebar_toggled, Section.VIDEO_CUT)
        self.get_widget('radioArchive').connect('clicked', self._on_sidebar_toggled, Section.ARCHIVE)  
        self.get_widget('radioTrash').connect('clicked', self._on_sidebar_toggled, Section.TRASH)
        
        # change background of sidebar
        eventbox = self.get_widget('eventboxSidebar')
        cmap = eventbox.get_colormap()
        colour = cmap.alloc_color("lightgray")
        style = eventbox.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = colour
        eventbox.set_style(style)

        style = self.get_widget('eventboxPlanningCurrentCount').get_style().copy()
        pixmap, mask = gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('badge.png')).render_pixmap_and_mask()
        style.bg_pixmap[gtk.STATE_NORMAL] = pixmap        
        self.get_widget('eventboxPlanningCurrentCount').shape_combine_mask(mask, 0, 0)        
        self.get_widget('eventboxPlanningCurrentCount').set_style(style)

        # change font of sidebar     
        for label in ['labelPlanningCount', 'labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount', 'labelOtrkey', 'labelAvi', 'labelPlanningCurrentCount']:
            self.get_widget(label).modify_font(pango.FontDescription("bold"))

        # change background of tasks and searchbar
        for eventbox in ['eventbox_search']:
            eventbox = self.get_widget(eventbox)
            cmap = eventbox.get_colormap()
            colour = cmap.alloc_color("#FFF288")
            style = eventbox.get_style().copy()
            style.bg[gtk.STATE_NORMAL] = colour
            eventbox.set_style(style)
        
      
    #
    # treeview_files
    #
    
    def clear_files(self):
        """ Entfernt alle Einträge aus den Treeviews treeview_files und treeview_planning."""        
        self.get_widget('treeview_files').get_model().clear()
        self.get_widget('treeview_planning').get_model().clear()
    
    def get_selected_filenames(self):
        """ Gibt die ausgewählten Dateinamen zurück. """
        selection = self.get_widget('treeview_files').get_selection()
            
        def selected_row(model, path, iter, filenames):
            filenames += [self.get_widget('treeview_files').get_model().get_value(iter, self.__FILENAME)]
        
        filenames = []        
        selection.selected_foreach(selected_row, filenames)      

        return filenames
        
    def append_row_files(self, parent, filename, size, date, locked=False):               
        """ Fügt eine neue Datei zu treeview_files hinzu.
              parent Für Archiv, ansonsten None: der übergeordnete iter des Ordners
              filename Dateiname
              size Dateigröße in Bytes
              date Änderungsdatum der Datei
              locked locked"""

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
       
    def __tv_files_sort(self, model, iter1, iter2, data):
        # -1 if the iter1 row should precede the iter2 row; 0, if the rows are equal; and, 1 if the iter2 row should precede the iter1 row
         
        filename_iter1 = model.get_value(iter1, self.__FILENAME)    
        filename_iter2 = model.get_value(iter2, self.__FILENAME)
        
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
    def __tv_files_name(self, column, cell, model, iter):            
        cell.set_property('text', basename(model.get_value(iter, self.__FILENAME)))

    def __tv_files_pixbuf(self, column, cell, model, iter):        
        filename = model.get_value(iter, self.__FILENAME)
    
        if isdir(filename):
            cell.set_property('pixbuf', self.__pix_folder)
        else:
            if filename.endswith('.otrkey'):
                cell.set_property('pixbuf', self.__pix_otrkey)
            else:
                cell.set_property('pixbuf', self.__pix_avi)

    #
    # treeview_planning
    #
            
    def get_selected_broadcasts(self):
        """ Gibt die ausgewählten geplanten Sendungen zurück. """
        selection = self.get_widget('treeview_planning').get_selection()
            
        def selected_row(model, path, iter, broadcasts):
            broadcasts += [iter]
        
        broadcasts = []        
        selection.selected_foreach(selected_row, broadcasts)      

        return broadcasts
               
    def append_row_planning(self, broadcast):
        """ Fügt eine geplante Sendung zu treeview_planning hinzu.
             broadcast Instanz von planning.PlanningItem """
        
        datetime = time.strftime("%a, %d.%m.%Y, %H:%M", time.localtime(broadcast.datetime))
    
        now = time.time()

        index = self.__app.planned_broadcasts.index(broadcast)

        if broadcast.datetime < now: 
            # everything bold
            data = [index, "<b>%s</b>" % broadcast.title, "<b>%s</b>" % datetime, "<b>%s</b>" % broadcast.station]
        else:
            data = [index, broadcast.title, datetime, broadcast.station]
              
        iter = self.get_widget('treeview_planning').get_model().append(None, data)
        return iter

    def __tv_planning_sort(self, model, iter1, iter2, data):
        # -1 if the iter1 row should precede the iter2 row; 0, if the rows are equal; and, 1 if the iter2 row should precede the iter1 row              
        time1 = self.__app.planned_broadcasts[model.get_value(iter1, 0)].datetime
        time2 = self.__app.planned_broadcasts[model.get_value(iter2, 0)].datetime

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
        """ Fügt die entsprechenden Toolbuttons in die Toolbar ein.
              section """
        
        for toolbutton in self.get_widget('toolbar').get_children():
           self.get_widget('toolbar').remove(toolbutton)
        
        for toolbutton in self.__sets_of_toolbars[section]:        
            self.get_widget('toolbar').insert(toolbutton, -1)
                
    def show_planning(self, planning):
        self.get_widget('scrolledwindow_files').props.visible = not planning
        self.get_widget('scrolledwindow_planning').props.visible = planning
     
    def block_gui(self, state):
        for button in ["decode", "cut", "decodeandcut"]:
            self.__toolbar_buttons[button].set_sensitive(not state)
     
    def broadcasts_badge(self):
        count = 0
        now = time.time()
        for broadcast in self.__app.planned_broadcasts:           
            if broadcast.datetime < now:
                count += 1
    
        if count == 0:
            self.get_widget('eventboxPlanningCurrentCount').hide()
        else:
            self.get_widget('eventboxPlanningCurrentCount').show()
            self.get_widget('labelPlanningCurrentCount').set_text(str(count))
      
    def change_status(self, message_type, message, permanent=False):
        """ Zeigt ein Bild und einen Text in der Statusleiste an.
              message_type 0 = Information-Icon, -1  = kein Icon
              message Anzuzeigender Text
              permanent: wenn \e False, verschwindet die Nachricht nach 10s wieder."""
            
        self.get_widget('label_statusbar').set_text(message)           
            
        if message_type == 0:            
            self.get_widget('image_status').set_from_file(otrpath.get_image_path("information.png"))
        
        if not permanent:                
            def wait():
                yield 0 # fake generator
                time.sleep(10)
                   
            def completed():
                self.get_widget('label_statusbar').set_text("")     
                self.get_widget('image_status').clear()
                   
            GeneratorTask(wait, None, completed).start()         
   
    def set_tasks_visible(self, visible):
        """ Zeigt/Versteckt einen Text und einen Fortschrittsbalken, um Aufgaben auszuführen. """      
        self.get_widget('box_tasks').props.visible = visible
        self.get_widget('label_tasks').set_markup("")
        self.get_widget('progressbar_tasks').set_fraction(0)

    def set_tasks_text(self, text):
        """ Zeigt den angegebenen Text im Aufgabenfenster an. """
        self.get_widget('label_tasks').set_markup("<b>%s</b>" % text)

    def set_tasks_progress(self, progress):
        """ Setzt den Fortschrittsbalken auf die angegebene %-Zahl. """
        self.get_widget('progressbar_tasks').set_fraction(progress / 100.)
        
          
    #
    #  Signal handlers
    #
               
    def _on_menu_check_update_activate(self, widget, data=None):
        current_version = open(otrpath.get_path("VERSION"), 'r').read().strip()
    
        try:
           svn_version = urllib.urlopen('http://github.com/elbersb/otr-verwaltung/raw/master/src/VERSION').read().strip()
        except IOError:
            self.__gui.message_error_box("Konnte keine Verbindung mit dem Internet herstellen!")
            return
        
        self.__gui.message_info_box("Ihre Version ist:\n%s\n\nAktuelle Version ist:\n%s" % (current_version, svn_version))            

    
    def _on_menuHelpHelp_activate(self, widget, data=None):
        webbrowser.open("http://otrverwaltung.host56.com/")
                      
    def _on_menuHelpAbout_activate(self, widget, data=None):

        def open_website(dialog, url, data=None):
            webbrowser.open(url)

        gtk.about_dialog_set_url_hook(open_website)

        about_dialog = gtk.AboutDialog()        
        about_dialog.set_transient_for(self.__gui.main_window.get_window())
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("OTR-Verwaltung")
        about_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('icon3.png')))
        
        version = open(otrpath.get_path("VERSION"), 'r')        
        about_dialog.set_version(version.read().strip())
        about_dialog.set_website("http://otrverwaltung.host56.com/")
        about_dialog.set_comments("Zum Verwalten von Dateien von onlinetvrecorder.com.")
        about_dialog.set_copyright("Copyright \xc2\xa9 2009 Benjamin Elbers")
        about_dialog.set_authors(["Benjamin Elbers <elbersb@gmail.com>"])
        about_dialog.run()
        about_dialog.destroy()
    
    def _on_menuEditPlugins_activate(self, widget, data=None):
        self.__gui.dialog_plugins.run()

    def _on_menuEditPreferences_activate(self, widget, data=None):
        self.__gui.preferences_window.show()
    
    def _on_main_window_configure_event(self, widget, event, data=None):
        self.size = self.get_window().get_size()       
   
    def _on_main_window_window_state_event(self, widget, event, data=None):
        state = event.new_window_state
        if (state & gtk.gdk.WINDOW_STATE_MAXIMIZED):
            self.maximized = True
        else:
            self.maximized = False
    
    def _on_main_window_destroy(self, widget, data=None):                
        gtk.main_quit()
   
    def _on_main_window_delete_event(self, widget, data=None):
        if self.__app.locked:
            if not self.__gui.question_box("Das Programm arbeitet noch. Soll wirklich abgebrochen werden?"):        
                return True # won't be destroyed
        
    def _on_menuFileQuit_activate(self, widget, data=None):        
        gtk.main_quit()
           
    def _on_menuEditSearch_activate(self, widget, data=None):
        entry_search = self.get_widget('entry_search')
        
        if entry_search.get_text() == "Durchsuchen":
            entry_search.set_text('')
        
        entry_search.grab_focus()
    
    def _on_menu_bottom_toggled(self, widget, data=None):
        self.__app.config.set('show_bottom', widget.get_active())
        self.get_widget('box_bottom').props.visible = widget.get_active()
    
    # toolbar actions
    def _on_toolbutton_clicked(self, button, action, cut_action=None):        
        filenames = self.get_selected_filenames()
        broadcasts = self.get_selected_broadcasts()    
        self.__app.perform_action(action, filenames, broadcasts, cut_action)
                  
    # sidebar
    def _on_sidebar_toggled(self, widget, section):
        if widget.get_active() == True:
            self.__app.show_section(section)            
    
    def _on_buttonClear_clicked(self, widget, data=None):
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
        self.get_widget('entry_search').set_text("Durchsuchen")
   
    def _on_entry_search_button_press_event(self, widget, data=None):
        self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        if self.get_widget('entry_search').get_text() == "Durchsuchen":
            self.get_widget('entry_search').set_text("")
    
    def _on_entry_search_focus_out_event(self, widget, data=None):
        if self.get_widget('entry_search').get_text() == "":
            self.get_widget('entry_search').modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
            self.get_widget('entry_search').set_text("Durchsuchen")
            
    def _on_entry_search_changed(self, widget, data=None):
        search = widget.get_text()

        self.do_search(search)
    
    def do_search(self, search):
        if search == "Durchsuchen" or search == "":
            self.__app.stop_search()
            
            self.get_widget('eventbox_search').hide()
            
            for label in ['labelPlanningCount', 'labelOtrkeysCount', 'labelUncutCount', 'labelCutCount', 'labelArchiveCount', 'labelTrashCount']:
                self.get_widget(label).set_text("")
        else:
            self.get_widget('eventbox_search').show()
            self.get_widget('label_search').set_markup("<b>Suchergebnisse für '%s'</b>" % search)
        
            counts_of_section = self.__app.start_search(search)
                  
            self.get_widget('labelPlanningCount').set_text(counts_of_section[Section.PLANNING])                  
            self.get_widget('labelOtrkeysCount').set_text(counts_of_section[Section.OTRKEY])
            self.get_widget('labelUncutCount').set_text(counts_of_section[Section.VIDEO_UNCUT])
            self.get_widget('labelCutCount').set_text(counts_of_section[Section.VIDEO_CUT])     
            self.get_widget('labelArchiveCount').set_text(counts_of_section[Section.ARCHIVE])    
            self.get_widget('labelTrashCount').set_text(counts_of_section[Section.TRASH])
               
    def _on_eventboxPlanningCurrentCount_button_release_event(self, widget, data=None):
        # show section
        self.get_widget('radioPlanning').set_active(True)
        
        # select already broadcasted
        selection = self.get_widget('treeview_planning').get_selection()
        selection.unselect_all()
        now = time.time()
                
        def foreach(model, path, iter, data=None):
            index = model.get_value(iter, 0)
            stamp = self.__app.planned_broadcasts[index].datetime

            if stamp < now:
                selection.select_iter(iter)

        self.get_widget('treeview_planning').get_model().foreach(foreach)
        
    # bottom
    def on_notebook_bottom_page_added(self, notebook, child, page_num, data=None):
        self.get_widget('menu_bottom').set_sensitive(True)
    
    def on_notebook_bottom_page_removed(self, notebook, child, page_num, data=None):        
        self.get_widget('menu_bottom').set_sensitive(False)
        self.get_widget('menu_bottom').set_active(False)
