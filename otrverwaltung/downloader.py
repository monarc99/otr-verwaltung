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

import subprocess
import re
import time
import os.path
import base64
import hashlib
import urllib

from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung.cutlists import Cutlist
from otrverwaltung.constants import DownloadStatus, DownloadTypes
from otrverwaltung import fileoperations

class Download:
    
    def __init__(self, config, filename, link=None):
        """ Torrent: link=None """
    
        self._config = config
           
        self.filename = filename
        self.link = link
           
        self.information = {
            'output' : '',
            'status' : -1,
            'size' : None,
            'progress' : 0,
            'speed' : '',
            'est' : '',
            'message_short' : '',
            # Torrent
            'seeders': None,
            'upspeed': None,
            'uploaded': None
        }
                
        self.__task = None
        self.__process = None
    
    #
    # Init methods for action
    # 
    
    def download_torrent(self):
        self.information['download_type'] = DownloadTypes.TORRENT
           
    def download_basic(self, preferred_downloader):
        self.information['download_type'] = DownloadTypes.BASIC
        self.information['preferred_downloader'] = preferred_downloader
    
    def download_decode(self, cutlist_id=None):
        if cutlist_id:
            self.information['download_type'] = DownloadTypes.OTR_CUT  
            self.information['cutlist_id'] = cutlist_id
            self.information['cutlist'] = None
        else:
            self.information['download_type'] = DownloadTypes.OTR_DECODE
                
    #
    # Convenience methods used only by this class
    #
    
    def _clear(self):
        self.information['est'] = ""
        self.information['speed'] = ""    
      
    def _finished(self):
        self.information['status'] = DownloadStatus.FINISHED
        self.information['progress'] = 100
        self.information['est'] = ""

    # unused by now
    def _parse_time(time):
        """ Takes a string '5m' or '6h2m59s' and calculates seconds. """
        m = re.match('((?P<h>[0-9]*)h)?((?P<m>[0-9]{1,2})m)?((?P<s>[0-9]{1,2})s)?', time)
        if m:
            d = m.groupdict()
            time = 60 * 60 * int(m.group('h')) if m.group('h') else 0
            time = (time + 60 * int(m.group('m'))) if m.group('m') else time
            time = (time + int(m.group('s'))) if m.group('s') else time
            return time
        else:
            return 0
    
    def _check_for_errors(self, text):
        words = ['error', 'fehler']
        for word in words:
            if word in text.lower():
                self.information['status'] = DownloadStatus.ERROR
                return True
        return False
   
    #
    # Download
    #     
        
    def _download(self):   
        self.log = ''
        
        self.information['status'] = DownloadStatus.RUNNING
      
        if self.information['download_type'] == DownloadTypes.TORRENT:            
            # download torrent if necessary
            torrent_filename = os.path.join(self._config.get('general', 'folder_new_otrkeys'), self.filename + '.torrent')            
            if not os.path.exists(torrent_filename):
                password = base64.b64decode(self._config.get('general', 'password'))
                hash = hashlib.md5(password).hexdigest()
                email = self._config.get('general', 'email')            
                url = 'http://81.95.11.2/xbt/xbt_torrent_create.php?filename=%s&email=%s&mode=free&hash=%s' % (self.filename, email, hash)
                try:
                    urllib.urlretrieve(url, torrent_filename)
                    # read filename
                    f = open(torrent_filename, 'r')
                    line = f.readlines()[0]
                except IOError, error:
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'Torrentdatei konnte nicht geladen werden.'
                    yield "Torrentdatei konnte nicht heruntergeladen werden (%s)!" % error
                    return
                    
                if "Hash wrong" in line:
                    os.remove(torrent_filename)
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'OTR-Daten nicht korrekt!'
                    yield 'OTR-Daten nicht korrekt!'
                    return                    
            
            self.information['message_short'] = 'Torrent-Download'
            self.information['output'] = self._config.get('general', 'folder_new_otrkeys')
            command = self._config.get('downloader', 'aria2c_torrent') + ["-d", self.information['output'], "-T", torrent_filename]
            
            try:                
                self.__process = subprocess.Popen(command, stdout=subprocess.PIPE)
            except OSError, error:
                self.information['status'] = DownloadStatus.ERROR
                self.information['message_short'] = 'Aria2c ist nicht installiert.'
                yield "Ist aria2c installiert? Der Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(command['aria2c']), error)
                return
                
            while True:
                error_code = self.__process.poll()
                if error_code != None:
                    if not self.information['status'] in [DownloadStatus.STOPPED, DownloadStatus.ERROR]:
                        if error_code == 0:
                            self._finished()
                        else:
                            self.information['status'] = DownloadStatus.ERROR
                    break
                          
                line = self.__process.stdout.readline().strip()
                self._check_for_errors(line)
        
                if "%" in line:
                    # get size
                    if not self.information['size']:
                        try:
                            # aria2c gives size always in MiB (hopefully)
                            size = re.findall('SIZE:.*/(.*)MiB\(', line)[0]
                            size = size.replace(',', '')
                            size = int(round(float(size))) * 1024 * 1024
                            self.information['size'] = size
                            yield line
                        except:
                            pass

                    # get progress
                    result = re.findall('([0-9]{1,3})%', line) 
                    if result:                            
                        self.information['progress'] = int(result[0])   

                    # get speed, est                
                    if "UP" in line:
                        result = re.findall('SPD:(.*) UP:(.*)\((.*)\) ETA:(.*)]', line)
                        if result:                   
                            self.information['speed'] = result[0][0]
                            self.information['upspeed'] = result[0][1]
                            self.information['uploaded'] = result[0][2]
                            self.information['est'] = result[0][3]                        
                    else:
                        result = re.findall('SPD:(.*) .*ETA:(.*)]', line)
                        if result:                   
                            self.information['speed'] = result[0][0]
                            self.information['est'] = result[0][1]                                           
                        
                    # get seeder info
                    result = re.findall('SEED:([0-9]*) ', line)                   
                    if result:
                        self.information['seeders'] = result[0]
                    
                    self.update_view()
                else:        
                    yield line

                time.sleep(1)
            
            ### Process is terminated                
            stdout = self.__process.stdout.read().strip()
            self._check_for_errors(stdout)
            yield stdout
      
        elif self.information['download_type'] == DownloadTypes.BASIC:            
            self.information['output'] = self._config.get('general', 'folder_new_otrkeys')
            
            if self.information['preferred_downloader'] == 'wget':                
                command = self._config.get('downloader', 'wget') + ["-c", "-P", self.information['output'], self.link]
                
                try:                
                    self.__process = subprocess.Popen(command, stderr=subprocess.PIPE)
                except OSError, error:
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'Wget ist nicht installiert.'
                    yield "Ist Wget installiert? Der Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(command), error)
                    return
                    
                sleep = 0
                while self.__process.poll() == None:                    
                    line = self.__process.stderr.readline().strip()
                            
                    if line:
                        if not self.information['size']:
                            result = re.findall(': ([0-9]*) \(', line)
                            if result:
                                self.information['size'] = int(result[0])
                        
                        if "%" in line: 
                            sleep = 1                                               
                            result = re.findall('([0-9]{1,3})% (.*)[ =](.*)', line)

                            if result:
                                self.information['progress'] = int(result[0][0])
                                self.information['speed'] = result[0][1]
                                if self.information['progress'] == 100:
                                    self._finished()
                                else:
                                    self.information['est'] = result[0][2]
                       
                        else:        
                            yield line    
                                        
                        self.update_view()
                        
                    time.sleep(sleep)
                
                ### Process is terminated
                yield self.__process.stderr.read().strip()
            
            else:
                command = self._config.get('downloader', 'aria2c') + ["-d", self.information['output'], self.link]
                try:                
                    self.__process = subprocess.Popen(command, stdout=subprocess.PIPE)
                except OSError, error:
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'Aria2c ist nicht installiert.'
                    yield "Ist aria2c installiert? Der Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(command), error)
                    return
                    
                while True:
                    error_code = self.__process.poll()
                    if error_code != None:
                        if not self.information['status'] in [DownloadStatus.STOPPED, DownloadStatus.ERROR]:
                            if error_code == 0:
                                self._finished()
                            else:
                                self.information['status'] = DownloadStatus.ERROR
                        break
                    
                    line = self.__process.stdout.readline().strip()                    
                            
                    if "%" in line:
                        if not self.information['size']:
                            try:
                                # aria2c gives size always in MiB (hopefully)
                                size = re.findall('.*FileAlloc.*/(.*)\(', line)[0]
                                size = size.strip('MiB')
                                size = size.replace(',', '')
                                size = int(round(float(size))) * 1024 * 1024
                                self.information['size'] = size
                                self.update_view()
                                yield line
                            except:
                                pass
                    
                        result = re.findall('\(([0-9]{1,3})%\).*SPD:(.*) ETA:(.*)]', line)
       
                        if result:                            
                            self.information['progress'] = int(result[0][0])
                            self.information['speed'] = result[0][1]
                            self.information['est'] = result[0][2]                       
                            self.update_view()
                    else:        
                        yield line

                    time.sleep(1)
                
                ### Process is terminated                
                stdout = self.__process.stdout.read().strip()
                self._check_for_errors(stdout)
                yield stdout
                
            self.update_view()
            
        elif self.information['download_type'] in [DownloadTypes.OTR_DECODE, DownloadTypes.OTR_CUT]:
            decoder = self._config.get('general', 'decoder')
            email = self._config.get('general', 'email')
            password = base64.b64decode(self._config.get('general', 'password'))        
            cache_dir = self._config.get('general', 'folder_trash_otrkeys')
            command = [decoder, "-b", "0", "-n", "-i", self.link, "-e", email, "-p", password, "-c", cache_dir]
            
            if self.information['download_type'] == DownloadTypes.OTR_CUT:
                self.information['output'] = self._config.get('general', 'folder_cut_avis')
                if not self.information['cutlist']:
                    cutlist = Cutlist()
                    cutlist.id = self.information['cutlist_id']
                    error = cutlist.download(self._config.get('general', 'server'), os.path.join(self.information['output'], self.filename))
                    if error:
                        self.information['status'] = DownloadStatus.ERROR
                        self.information['message_short'] = 'Cutlist konnte nicht geladen werden.'
                        yield error
                        return                        
                        
                    self.information['cutlist'] = cutlist
                    
                command += ["-o", self.information['output'], "-C", self.information['cutlist'].local_filename]
            else:
                self.information['output'] = self._config.get('general', 'folder_uncut_avis')                  
                command += ["-o", self.information['output']]
            
            try:
                self.__process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError, error:
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'Dekoder nicht gefunden.'
                    yield "Der Pfad zum Dekoder scheint nicht korrekt zu sein. Der folgende Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(command), error)
                    return

            line = ''
            while self.__process.poll()==None:
                char = self.__process.stdout.read(1)
                
                if char=='\r' or char=='\n':
                    line = line.strip()
                    if not line:
                        continue
                        
                    if not "%" in line:
                        yield line
                    
                    result = re.findall("([0-9]{1,3})%", line)
                    if result:
                        self.information['progress'] = int(result[0])
                        
                    result = re.findall("[0-9]{1,3}%.*: (.*)", line)
                    if result:
                        self.information['speed'] = result[0]
                    
                    self.update_view()
                    
                    line = ''
                else:
                    line += char
            
            ### Process is terminated
                    
            stderr = self.__process.stderr.read()
            if "invalid option" in stderr:
                self.information['status'] = DownloadStatus.ERROR
                self.information['message_short'] = 'Der Dekoder ist veraltet.'
                yield "Es ist ein veralteter Dekoder angegeben!\n"
                
            yield stderr.strip()
            self._check_for_errors(stderr)
            
            if not self.information['status'] in [DownloadStatus.ERROR, DownloadStatus.STOPPED]:
                self._finished()
                # remove otrkey and .segments file
                fileoperations.remove_file(os.path.join(cache_dir, self.filename))
                fileoperations.remove_file(os.path.join(cache_dir, self.filename + '.segments'))

                if self.information['download_type'] == DownloadTypes.OTR_CUT:
                    # rename file to "cut" filename
                    filename = os.path.join(self.output, self.filename.rstrip(".otrkey"))
                    new_filename, extension = os.path.splitext(filename)
                    new_filename += ".cut" + extension
                    fileoperations.rename_file(filename, new_filename)
                                       
                    #TODO: Zusammenfassungsdialoganzeigemöglichkeit einblenden
                    
                self.update_view()
                
    def start(self):    
        def loop(*args):
            self.log += "%s\n" % args[0]
        
        if not self.information['status'] == DownloadStatus.RUNNING:
            self.__task = GeneratorTask(self._download, loop)
            self.__task.start()
        
    def stop(self):    
        if self.information['status'] == DownloadStatus.RUNNING:
            self._clear()
            self.update_view()        
            self.information['status'] = DownloadStatus.STOPPED    
                
            if self.__process:
                try:
                    self.__process.kill()
                except OSError:
                    pass
        
            if self.__task:
                self.__task.stop()
