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

import gtk
import gobject

from otrverwaltung.constants import DownloadStatus
from otrverwaltung import path

class DownloadsTreeView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        
        self.liststore = gtk.ListStore(object)        
        self.set_model(self.liststore)
        
        self.set_headers_visible(False)
        
        rend = CellRendererDownload()        
        column = gtk.TreeViewColumn('col', rend, download=0)       
        self.append_column(column)
        
        self.set_rules_hint(True)
    
    def __update_view(self):
        self.queue_draw()
    
    def add_objects(self, *args):
        for obj in args:
            obj.update_view = self.__update_view
            self.liststore.append([obj])
        
    def remove_objects(self, *args):
        for row in self.liststore:
            if row[0] in args:
                del self.liststore[row.iter]
                
class CellRendererDownload(gtk.GenericCellRenderer):
    __gtype_name__ = "CellRendererDownload"

    __gproperties__ = {
        'download': (gobject.TYPE_PYOBJECT, 'Download', 'Download', gobject.PARAM_READWRITE)
    }
    
    def __init__(self):
        self.__gobject_init__()

        self.set_property('mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)

        self.statuses = {
            DownloadStatus.RUNNING : ("Laufend", gtk.gdk.pixbuf_new_from_file(path.getdatapath('media', 'download_start.png'))),
            DownloadStatus.STOPPED : ("Gestoppt", gtk.gdk.pixbuf_new_from_file(path.getdatapath('media', 'download_stop.png'))),
            DownloadStatus.ERROR : ("Fehler", gtk.gdk.pixbuf_new_from_file(path.getdatapath('media', 'error.png'))),
            DownloadStatus.FINISHED : ("Fertig!", gtk.gdk.pixbuf_new_from_file(path.getdatapath('media', 'finished.png')))
        }

        self.cellrenderer_pixbuf = gtk.CellRendererPixbuf()        
        self.cellrenderer_filename = gtk.CellRendererText()
        self.cellrenderer_info = gtk.CellRendererText()
        self.cellrenderer_progress = gtk.CellRendererProgress()
        
    def on_get_size(self, widget, cell_area=None):
        complete_width, complete_height = 0, 0
    
        xoffset, yoffset, width, height = self.cellrenderer_filename.get_size(widget)      
        complete_height += height  
        xoffset, yoffset, width, height = self.cellrenderer_info.get_size(widget)
        complete_height += height
        xoffset, yoffset, width, height = self.cellrenderer_progress.get_size(widget)
        complete_height += height
        
        return 0, 0, complete_width, complete_height + 10

    def on_render(self, window, widget, background_area, cell_area, expose_area, flags):               
        x, y, w, h = cell_area.x, cell_area.y, cell_area.width, cell_area.height
        
        area = gtk.gdk.Rectangle(x + 2, y, 16, 20)
        self.cellrenderer_pixbuf.render(window, widget, background_area, area, expose_area, flags)
    
        area = gtk.gdk.Rectangle(x + 20, y, w - 25, 16)
        self.cellrenderer_filename.render(window, widget, background_area, area, expose_area, flags)
        
        area = gtk.gdk.Rectangle(x + 20, y + 22, w - 25, 16)
        self.cellrenderer_info.render(window, widget, background_area, area, expose_area, flags)
                    
        area = gtk.gdk.Rectangle(x + 20, y + 45, w - 25, 18)
        self.cellrenderer_progress.render(window, widget, background_area, area, expose_area, flags)                
        
    def on_activate(self, event, widget, path, background_area, cell_area, flags):
        pass
        
    def do_set_property(self, pspec, value):
        if pspec.name == 'download':
            self.cellrenderer_filename.set_property('markup', value.filename)            
            self.cellrenderer_progress.set_property('value', value.progress)
            info_text, text = "", ""
            if value.status != -1:
                text, pixbuf = self.statuses[value.status]            
                self.cellrenderer_pixbuf.set_property('pixbuf', pixbuf)
            
            infos = []
            if value.size:
                infos.append("Größe: %s" % self.humanize_size(value.size))
            if value.speed:
                infos.append("Geschwindigkeit: %s" % value.speed)
            if value.est:
                infos.append("Verbleibende Zeit: %s" % value.est)
            
            if infos:
                info_text += "<i>%s</i> - " % text + ", ".join(infos)
            else:
                info_text += "<i>%s</i>" % text

            self.cellrenderer_info.set_property('markup', info_text)

    def humanize_size(self, bytes):
        bytes = float(bytes)
        if bytes >= 1099511627776:
            terabytes = bytes / 1099511627776
            size = '%.1f T' % terabytes
        elif bytes >= 1073741824:
            gigabytes = bytes / 1073741824
            size = '%.1f GB' % gigabytes
        elif bytes >= 1048576:
            megabytes = bytes / 1048576
            size = '%.1f MB' % megabytes
        elif bytes >= 1024:
            kilobytes = bytes / 1024
            size = '%.1f K' % kilobytes
        else:
            size = '%.1f b' % bytes
        return size

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)               
