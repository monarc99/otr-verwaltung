# -*- coding: utf-8 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gtk

from otrverwaltung.constants import DownloadTypes
from otrverwaltung import path

class DownloadPropertiesDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "DownloadPropertiesDialog"

    def __init__(self):
        self.changed = False

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)

        self.combobox_type = self.builder.get_object('combobox_downloadtype')
        self.liststore_type = self.builder.get_object('combobox_downloadtype').get_model()
        cell = gtk.CellRendererText()
        self.combobox_type.pack_start(cell, True)
        self.combobox_type.add_attribute(cell, 'text', 0)

    def run(self, download):
        self.download = download
        self.original_download_type = download.information['download_type']

        # setup
        if download.filename:
            self.builder.get_object('label_filename').set_markup('<b>%s</b>' % download.filename)
        else:
            self.builder.get_object('label_filename').set_markup('Dateiname nicht bekannt.')
            self.builder.get_object('button_clipboard_filename').hide()

        if download.information['download_type'] == DownloadTypes.TORRENT:
            self.builder.get_object('label_downloadtype').hide()
            self.builder.get_object('box_downloadtype').hide()

            self.builder.get_object('button_clipboard_link').hide()
            self.builder.get_object('label_link_torrent_label').set_text("Torrent-Info:")
            torrent_info = []

            if download.information['ratio']:
                torrent_info.append('Ratio: %s' % download.information['ratio'])
            if download.information['upspeed']:
                torrent_info.append('Uploadgeschwindigkeit: %s' % download.information['upspeed'])
            if download.information['uploaded']:
                torrent_info.append('Upload: %s' % download.information['uploaded'])

            if torrent_info:
                self.builder.get_object('label_link_torrentinfo').set_text(', '.join(torrent_info))
            else:
                self.builder.get_object('label_link_torrentinfo').set_markup('<i>N/A</i>')
        else:
            self.builder.get_object('label_link_torrentinfo').set_text(download.link)

            # add types
            self.liststore_type.append(['Torrent-Download', 0])
            self.liststore_type.append(['Normaler Download über Aria2c', 1])
            self.liststore_type.append(['Normaler Download über Wget', 2])

            if download.information['download_type'] == DownloadTypes.OTR_DECODE:
                self.liststore_type.append(['OTR-Download mit Dekodieren', 3])
                self.combobox_type.set_active(3)

            elif download.information['download_type'] == DownloadTypes.OTR_CUT:
                self.liststore_type.append(['OTR-Download mit Dekodieren', 3])
                self.liststore_type.append(['OTR-Download mit Schneiden', 4])
                self.combobox_type.set_active(4)

            else:
                self.original_preferred = download.information['preferred_downloader']
                if download.information['preferred_downloader'] == 'wget':
                    self.combobox_type.set_active(2)
                else:
                    self.combobox_type.set_active(1)

        self.builder.get_object('textbuffer_log').set_text(download.log)
        textbuffer = self.builder.get_object('textbuffer_log')
        tag = textbuffer.create_tag(None, family='Monospace')
        textbuffer.apply_tag(tag, textbuffer.get_start_iter(), textbuffer.get_end_iter())

        gtk.Dialog.run(self)

    def clipboard(self, text):
        clipboard = gtk.clipboard_get()
        clipboard.set_text(text)
        clipboard.store()

    # signals #
    def on_combobox_downloadtype_changed(self, widget, data=None):
        index = widget.get_active()
        pref = { 1: '', 2: 'wget' }

        if self.original_download_type == DownloadTypes.BASIC and index in [1, 2]:
            # a change from wget to aria2c or vv.

            self.download.information['download_type'] = DownloadTypes.BASIC
            self.download.information['preferred_downloader'] = pref[index]
            if self.original_preferred == self.download.information['preferred_downloader']:
                self.changed = False
            else:
                self.changed = True

        else:
            if index == 0:
                self.download.information['download_type'] = DownloadTypes.TORRENT
            elif index == 1 or index == 2:
                self.download.information['download_type'] = DownloadTypes.BASIC
                self.download.information['preferred_downloader'] = pref[index]
            elif index == 3:
                self.download.information['download_type'] = DownloadTypes.OTR_DECODE
            elif index == 4:
                self.download.information['download_type'] = DownloadTypes.OTR_CUT

            if self.original_download_type == self.download.information['download_type']:
                self.changed = False
            else:
                self.changed = True

    def on_button_clipboard_filename_clicked(self, widget, data=None):
        self.clipboard(self.builder.get_object('label_filename').get_text())

    def on_button_clipboard_link_clicked(self, widget, data=None):
        self.clipboard(self.builder.get_object('label_link_torrentinfo').get_text())

def NewDownloadPropertiesDialog():
    glade_filename = path.getdatapath('ui', 'DownloadPropertiesDialog.glade')

    builder = gtk.Builder()
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("download_properties_dialog")
    return dialog
