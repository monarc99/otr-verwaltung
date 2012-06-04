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
import urllib2

from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung.cutlists import Cutlist
from otrverwaltung.conclusions import FileConclusion
from otrverwaltung.constants import DownloadStatus, DownloadTypes, Action, Cut_action, Status
from otrverwaltung import fileoperations

class Download:
    
    def __init__(self, app, config, filename=None, link=None):
        """ Torrent: link=None """
    
        self._app = app
        self._config = config
           
        self.filename = filename
        self.link = link
        self.log = ""
           
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
            'uploaded': None,
            'ratio': None
        }
                
        self.__task = None
        self.__process = None

    #
    # Storage
    #

    def to_json(self):
        information = self.information.copy()
        if 'cutlist' in information.keys():
            information['cutlist'] = None
    
        return {
            'information' : information,
            'filename': self.filename,
            'link': self.link
        }

    def from_json(self, json):
        self.information = json['information']
        self.filename = json['filename']
        self.link = json['link']

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
            
    def _check_file_with_torrent(self):
        """ checks file with torrent """
        password = base64.b64decode(self._config.get('general', 'password'))
        hash = hashlib.md5(password).hexdigest()
        email = self._config.get('general', 'email')            
        url = 'http://81.95.11.2/xbt/xbt_torrent_create.php?filename=%s&email=%s&mode=free&hash=%s' % (self.filename, email, hash)      
        command = self._config.get('downloader', 'aria2c_torrent') + ["-d", self.information['output'], '--check-integrity=true', '--continue', '--bt-enable-lpd=false', '--bt-exclude-tracker="*"', '--enable-dht=false', '--enable-dht6=false', '--enable-peer-exchange=false', '--bt-hash-check-seed=false', '--bt-stop-timeout=1', '--seed-time=0', '--follow-torrent=mem', url]
        self.information['message_short'] = 'Torrent Datei zur Überprüfung holen ...'
        self.update_view()  
                
        # Checking
        try:                
            self.__process = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError, error:
            self.information['status'] = DownloadStatus.ERROR
            self.information['message_short'] = 'Aria2c ist nicht installiert oder Passwort falsch.'
            return

        while self.__process.poll() == None:                    
            line = self.__process.stdout.readline().strip()
            time.sleep(1)
            if "Checksum" in line:
                result = re.findall('Checksum:.*\((.*)%\)', line)
                if result:
                    self.information['message_short'] = 'Überprüfen...%s Prozent' % result[0]
                    self.information['progress'] = int(result[0])
                    self.update_view()         
            elif '(OK):Herunterladen abgeschlossen.(INPR):wird heruntergeladen.' in line:
                self.information['message_short'] = '(INPR):Download unvollständig.'
                self.information['progress'] = 0
                self.update_view()
            elif '(OK):download completed.(INPR):download in-progress.' in line:
                self.information['message_short'] = '(INPR):Download unvollständig.'
                self.information['progress'] = 0
                self.update_view()
            elif '(ERR):ein Fehler ist unterlaufen.' in line:  # Torrent Download fehlgeschlagen 
                self.information['message_short'] = 'Torrentdatei konnte nicht geladen werden. OTR-Daten nicht korrekt?'
                self.information['progress'] = 0
            elif '(ERR):error occurred.' in line:  # Torrent Download fehlgeschlagen 
                self.information['message_short'] = 'Torrentdatei konnte nicht geladen werden. OTR-Daten nicht korrekt?'
                self.information['progress'] = 0
            elif '(OK):Herunterladen abgeschlossen.'  in line:
                self.information['message_short'] = '(OK):Download vollständig.'
                self._finished()
                self.update_view()
            elif '(OK):download completed.'  in line:
                self.information['message_short'] = '(OK):Download vollständig.'
                self._finished()
                self.update_view()
             
        if self.__process.returncode == 0:
	    self.information['message_short'] = '(OK):Download vollständig.'
            self._finished()
            self.update_view()
        elif self.__process.returncode == 7:
	    self.information['message_short'] = '(INPR):Download unvollständig.'
            self.information['progress'] = 0
            self.update_view()
        else:
            self.information['message_short'] = '(EER):Fehler aufgetreten. Aria2c installiert und OTR Daten korrekt?'
            self.information['progress'] = 0
            self.update_view()
            
    #
    # Download
    #     
        
    def _download(self):   
        self.log = ''
        self.information['message_short'] = ''
        
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
                    urllib2.urlretrieve(url, torrent_filename)
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
            
            self.information['output'] = self._config.get('general', 'folder_new_otrkeys')
            command = self._config.get('downloader', 'aria2c_torrent') + ["-d", self.information['output'], "-T", torrent_filename]
            yield "Ausgeführt wird:\n%s\n" % " ".join(command)
            
            try:                
                self.__process = subprocess.Popen(command, stdout=subprocess.PIPE)
            except OSError, error:
                self.information['status'] = DownloadStatus.ERROR
                self.information['message_short'] = 'Aria2c ist nicht installiert.'
                yield "Ist aria2c installiert? Der Befehl konnte nicht ausgeführt werden:\nFehlermeldung: %s" % error
                return
                
            while self.__process.poll() == None:                          
                line = self.__process.stdout.readline().strip()

                if "Checksum" in line:
                    result = re.findall('Checksum:.*\((.*%)\)', line)
                    if result:
                        self.information['message_short'] = 'Überprüfen...%s' % result[0]
            
                elif "SEEDING" in line:
                    self.information['message_short'] = 'Seeden...'
                    self.information['status'] = DownloadStatus.SEEDING # _NOT_ DownloadStatus.FINISHED
                    self.information['progress'] = 100
                    self.information['est'] = ''
                    self.information['speed'] = ''
                    self.information['seeders'] = None
                    
                    result = re.findall('ratio:(.*)\) ', line)
                    if result:
                        self.information['ratio'] = result[0]
                    
                    result = re.findall('UP:(.*)\((.*)\)', line)
                    if result:                   
                        self.information['upspeed'] = result[0][0]
                        self.information['uploaded'] = result[0][1]
                    
                elif "%" in line:
                    self.information['message_short'] = ''
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
                else:        
                    yield line
                self.update_view()

            ### Process is terminated                
            stdout = self.__process.stdout.read().strip()
            yield stdout

            # A torrent download only stops:
            #   a) when the user clicks 'stop'
            #   b) when an error occured
            if self.information['status'] != DownloadStatus.STOPPED:                
                self.information['status'] = DownloadStatus.ERROR            
      
        elif self.information['download_type'] == DownloadTypes.BASIC:            
            self.information['output'] = self._config.get('general', 'folder_new_otrkeys')
            
            if self.information['preferred_downloader'] == 'wget':                
                command = self._config.get('downloader', 'wget') + ["-c", "-P", self.information['output'], self.link]
                yield "Ausgeführt wird:\n%s\n" % " ".join(command)
                
                try:                
                    self.__process = subprocess.Popen(command, stderr=subprocess.PIPE)
                except OSError, error:
                    self.information['status'] = DownloadStatus.ERROR
                    self.information['message_short'] = 'Wget ist nicht installiert.'
                    yield "Ist Wget installiert? Der Befehl konnte nicht ausgeführt werden:\n%s" % error
                    return
                    
                while True:
                    exit_code = self.__process.poll()
                    if exit_code != None:
                        if self.information['status'] != DownloadStatus.STOPPED:
                            if exit_code==0:
                                self._finished()
                            else:
                                self.information['status'] = DownloadStatus.ERROR
                        break
                    
                    line = self.__process.stderr.readline().strip()
                            
                    if line:
                        if not self.information['size']:
                            result = re.findall(': ([0-9]*) \(', line)
                            if result:
                                self.information['size'] = int(result[0])
                        
                        if "%" in line: 
                            result = re.findall('([0-9]{1,3})% (.*)[ =](.*)', line)

                            if result:
                                progress = int(result[0][0])
                                if self.information['progress'] == progress:
                                    continue
                                else:
                                    self.information['progress'] = progress
                                    
                                self.information['speed'] = result[0][1]
                                
                                if progress == 100:
                                    self._finished()
                                else:
                                    self.information['est'] = result[0][2]
                       
                        else:        
                            yield line    
                                        
                        self.update_view()
                        
                ### Process is terminated
                yield self.__process.stderr.read().strip()
            
            else:
                # Download with aria2c      
                if 'otrkey' in self.filename and os.path.exists(self.information['output'] + '/' +  self.filename) and self._config.get('general', 'password'):
                    self._check_file_with_torrent()    

                retries = -1
                command = self._config.get('downloader', 'aria2c') + ["-d", self.information['output'], self.link]            
                yield "Ausgeführt wird:\n%s\n" % " ".join(command)

                while retries != 0 and self.information['status'] == DownloadStatus.RUNNING:
                    self.log = ''
                    self.information['message_short'] = 'Download starten ...'
                    self.update_view()
                    
                    try:                
                        self.__process = subprocess.Popen(command, stdout=subprocess.PIPE)
                    except OSError, error:
                        self.information['status'] = DownloadStatus.ERROR
                        self.information['message_short'] = 'Aria2c ist nicht installiert.'
                        yield "Ist aria2c installiert? Der Befehl konnte nicht ausgeführt werden:\n%s" % error
                        return
                    
                    while self.__process.poll() == None:                    
                        line = self.__process.stdout.readline().strip()                    
	            
                        if "Checksum" in line:
                            result = re.findall('Checksum:.*\((.*)%\)', line)
                            if result:
                                self.information['message_short'] = 'Überprüfen...%s  Prozent' % result[0]
                                self.information['progress'] = int(result[0])
                                self.update_view()                  
                        elif "%" in line:
                            if "FileAlloc" in line:
                                result = re.findall('FileAlloc:.*\(([0-9]{1,3}%)', line)
                                self.information['message_short'] = 'Datei wird angelegt...%s' % result[0]
                            else:
                                self.information['message_short'] = ''
  
                            if not self.information['size']:
                                try:
                                    # aria2c gives size always in MiB (hopefully)
                                    size = re.findall('.*SIZE.*/(.*)\(', line)[0]
                                    size = size.strip('MiB')
                                    size = size.replace(',', '')
                                    size = int(round(float(size))) * 1024 * 1024
                                    self.information['size'] = size
                                    self.update_view()
                                    yield line
                                except:
                                    pass
                    
                            result = re.findall('\(([0-9]{1,3})%\).*CN:([0-9]{1,5}).*SPD:(.*) ETA:(.*)]', line)
 
                            if result:                            
                                self.information['progress'] = int(result[0][0])
                                self.information['message_short'] = 'Verbindungen: %s' % result[0][1]
                                self.information['speed'] = result[0][2]
                                self.information['est'] = result[0][3]                       
                                self.update_view()
                        else:        
                            yield line
                    
                    ### Process is terminated                
                    stdout = self.__process.stdout.read().strip()                
                    yield stdout
                    if not self.information['status'] in [DownloadStatus.STOPPED, DownloadStatus.ERROR]:
                        time.sleep(1) # wait for log being updated - very ugly
                        if '(INPR):wird heruntergeladen.' in self.log:
                            self.information['status'] = DownloadStatus.ERROR
                            self.information['message_short'] = '(INPR):Download unvollständig.'
                            self.information['progress'] = 0
                            self.update_view()
                            break
                        elif '(INPR):download in-progress.' in self.log:
                            self.information['status'] = DownloadStatus.ERROR
                            self.information['message_short'] = '(INPR):Download unvollständig.'
                            self.information['progress'] = 0
                            self.update_view()
                            break
                        elif '(OK):Herunterladen abgeschlossen.'  in self.log:
                            self.information['message_short'] = '(OK):Download vollständig.'
                            self._finished()
                            self.update_view()
                            break
                        elif '(OK):download completed.'  in self.log:
                            self.information['message_short'] = '(OK):Download vollständig.'
                            self._finished()
                            self.update_view()
                            break
                        else:                        
                            # Warteschlange                             
                            try:
                                page = urllib2.urlopen(self.link)
                            except IOError, e:
                                self.information['status'] = DownloadStatus.ERROR
                                page = e
        
                            headers = dict(page.info())
                            if 'x-otr-queueposition' in headers:
                                self.information['status'] = DownloadStatus.RUNNING
                                if 'retry-after' in headers:
                                    timer = int(headers['retry-after'])
                                else:
                                    timer = 30                               
                                while timer != 0 and self.information['status'] == DownloadStatus.RUNNING:
                                    self.information['message_short'] = 'Warteschlange Position: %s - nächster Versuch in %s Sekunden' % (headers['x-otr-queueposition'],timer)
                                    timer -= 1
                                    self.update_view()
                                    time.sleep(1)
                            elif 'x-otr-error-message' in headers:
                                self.information['status'] = DownloadStatus.RUNNING
                                if 'retry-after' in headers:
                                    timer = int(headers['retry-after'])
                                else:
                                    timer = 30
                                
                                while timer != 0 and self.information['status'] == DownloadStatus.RUNNING:
                                    self.information['message_short'] = 'Fehler: %s - nächster Versuch in %s Sekunden' % (headers['x-otr-error-message'],timer)
                                    timer -= 1
                                    self.update_view()
                                    time.sleep(1)
                            elif hasattr(page, 'reason'):
                                self.information['status'] = DownloadStatus.RUNNING
                                timer = 600
                                
                                while timer != 0 and self.information['status'] == DownloadStatus.RUNNING:
                                    self.information['message_short'] = 'Fehler: %s - nächster Versuch in %s Sekunden' % (page.reason,timer)
                                    timer -= 1
                                    self.update_view()
                                    time.sleep(1)
                            elif hasattr(page, 'code'):
                                self.information['status'] = DownloadStatus.RUNNING
                                if page.code == 200:
                                    timer = 5
                                else:   
                                    timer = 600
                                    
                                while timer != 0 and self.information['status'] == DownloadStatus.RUNNING:
                                    self.information['message_short'] = 'Fehler: %s - nächster Versuch in %s Sekunden' % (page.code,timer)
                                    timer -= 1
                                    self.update_view()
                                    time.sleep(1)                                    
                            else:
                                self.information['status'] = DownloadStatus.ERROR
                                self.information['message_short'] = '(EER):Fehler aufgetreten.'
                                self.information['progress'] = 0
                                break

                        retries -= 1
                        self.update_view()

                # Download Test
                if 'otrkey' in self.filename and os.path.exists(self.information['output'] + '/' +  self.filename) and self._config.get('general', 'password'):
                    self._check_file_with_torrent()  


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
            
            # write command to log, but strip out email and password            
            log = list(command)
            log[log.index('-p') + 1] = '*******'
            log[log.index('-e') + 1] = '*******'
            yield "Ausgeführt wird:\n%s\n" % " ".join(log)
            
            try:
                self.__process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError, error:
                self.information['status'] = DownloadStatus.ERROR
                self.information['message_short'] = 'Dekoder nicht gefunden.'
                yield "Der Pfad zum Dekoder scheint nicht korrekt zu sein. Der folgende Befehl konnte nicht ausgeführt werden\nFehlermeldung: %s" % error
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
                    
            stderr = self.__process.stderr.read().strip()
            if stderr:
                self.information['status'] = DownloadStatus.ERROR
                if "invalid option" in stderr:           
                    self.information['message_short'] = 'Der Dekoder ist veraltet.'
                    yield "Es ist ein veralteter Dekoder angegeben!\n"
                elif "maximale Anzahl":
                    self.information['message_short'] = 'Maximale Anzahl der Dekodierungen erreicht.'
                    yield unicode(stderr, 'iso-8859-1')
                else:
                    self.information['message_short'] = stderr
                    yield stderr
            
            if not self.information['status'] in [DownloadStatus.ERROR, DownloadStatus.STOPPED]:
                self._finished()
                # remove otrkey and .segments file
                otrkey = os.path.join(cache_dir, self.filename)
                fileoperations.remove_file(otrkey, None)
                fileoperations.remove_file(os.path.join(cache_dir, self.filename + '.segments'), None)

                if self.information['download_type'] == DownloadTypes.OTR_CUT:
                    # rename file to "cut" filename                    
                    filename = os.path.join(self.information['output'], self.filename.rstrip(".otrkey"))
                    new_filename, extension = os.path.splitext(filename)
                    new_filename += ".cut" + extension
                    fileoperations.rename_file(filename, new_filename, None)

                    conclusion = FileConclusion(Action.DECODEANDCUT, otrkey=otrkey, uncut_video=filename)
                    conclusion.decode.status = Status.OK
                    conclusion.cut_video = new_filename
                    conclusion.cut.cutlist = self.information['cutlist']
                    conclusion.cut.cutlist.read_from_file()
                    conclusion.cut.status = Status.OK
                    conclusion.cut.cut_action = Cut_action.CHOOSE_CUTLIST
                    if self._config.get('general', 'rename_cut'):                        
                        conclusion.cut.rename = self._app.rename_by_schema(self.filename.rstrip(".otrkey"))
                    else:
                        conclusion.cut.rename = os.path.basename(new_filename)
                    
                    self._app.conclusions_manager.add_conclusions(conclusion)
                    
        self.update_view()
                
    def start(self, force=False):
        def loop(*args):
            self.log += "%s\n" % args[0]
        
        if force or not self.information['status'] in [DownloadStatus.RUNNING, DownloadStatus.SEEDING]:
            self.__task = GeneratorTask(self._download, loop)
            self.__task.start()
        
    def stop(self):
        if self.information['status'] in [DownloadStatus.RUNNING, DownloadStatus.SEEDING]:
            self.information['status'] = DownloadStatus.STOPPED
            self.information['message_short'] = ""
            self.information['est'] = ""
            self.information['speed'] = ""
            self.update_view()
                
            if self.__process:
                try:
                    self.__process.kill()
                except OSError:
                    pass
