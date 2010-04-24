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

from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung.cutlists import Cutlist
from otrverwaltung.constants import DownloadStatus
from otrverwaltung import fileoperations

class DownloadTypes:
    TORRENT     = 0

    BASIC       = 4

    OTR_DECODE  = 2
    OTR_CUT     = 3    

class Download:
    
    def __init__(self, filename, link, output):         
        self.filename = filename
        self.link = link
        self.output = output
           
        self.size = None
        self.progress = 0
        self.speed = "" 
        self.est = ""  
        
        self.status = -1
        self.message_short = ''
        
        self.__task = None
        self.__process = None
    
    def download_basic(self, preferred_downloader, aria2c, wget):
        self.download_type = DownloadTypes.BASIC
        self.preferred_downloader = preferred_downloader
        
        self.commands = {
            'aria2c': aria2c + ["-d", self.output, self.link],
            'wget'  : wget + ["-c", "-P", self.output, self.link]
        }
    
    def download_decode(self, decoder, cache_dir, email, password, cutlist=None):
        if cutlist:
            self.download_type = DownloadTypes.OTR_CUT
            self.cutlist_server, self.cutlist_id = cutlist
        else:
            self.download_type = DownloadTypes.OTR_DECODE
        self.cache_dir = cache_dir
        self.command = [decoder, "-b", "0", "-n", "-i", self.link, "-o", self.output, "-c", cache_dir, "-e", email, "-p", password]        
    
    def _clear(self):
        self.est = ""
        self.speed = ""    
      
    def _finished(self):
        self.status = DownloadStatus.FINISHED
        self.est = ""

    def _check_for_errors(self, text):
        words = ['error', 'fehler']
        for word in words:
            if word in text.lower():
                self.status = DownloadStatus.ERROR
                return True
        return False
        
    def _download(self):   
        self.log = []
        
        self.status = DownloadStatus.RUNNING
      
        if self.download_type == DownloadTypes.BASIC:            
            if self.preferred_downloader == 'wget':
                try:                
                    self.__process = subprocess.Popen(self.commands['wget'], stderr=subprocess.PIPE)
                except OSError, error:
                    self.status = DownloadStatus.ERROR
                    self.message_short = 'Wget ist nicht installiert.'
                    yield "Ist Wget installiert? Der Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(self.commands['wget']), error)
                    return
                    
                sleep = 0
                while self.__process.poll() == None:                    
                    line = self.__process.stderr.readline().strip()
                            
                    if line:
                        if not self.size:
                            result = re.findall(': ([0-9]*) \(', line)
                            if result:
                                self.size = int(result[0])
                        
                        if "%" in line: 
                            sleep = 1                                               
                            result = re.findall('([0-9]{1,3})% (.*)[ =](.*)', line)

                            if result:
                                self.progress = int(result[0][0])
                                self.speed = result[0][1]
                                if self.progress == 100:
                                    self._finished()
                                else:
                                    self.est = result[0][2]
                       
                        else:        
                            yield line    
                                        
                        self.update_view()
                        
                    time.sleep(sleep)
                
                ### Process is terminated
                yield self.__process.stderr.read().strip()
            
            else:
                try:                
                    self.__process = subprocess.Popen(self.commands['aria2c'], stdout=subprocess.PIPE)
                except OSError, error:
                    self.status = DownloadStatus.ERROR
                    self.message_short = 'Aria2c ist nicht installiert.'
                    yield "Ist aria2c installiert? Der Befehl konnte nicht ausgeführt werden:\n%s\n\nFehlermeldung: %s" % (" ".join(self.commands['aria2c']), error)
                    return
                    
                while True:
                    error_code = self.__process.poll()
                    if error_code != None:
                        if not self.status in [DownloadStatus.STOPPED, DownloadStatus.ERROR]:
                            if error_code == 0:
                                self._finished()
                            else:
                                self.status = DownloadStatus.ERROR
                        break
                    
                    line = self.__process.stdout.readline().strip()
                    self._check_for_errors(line)
                            
                    if "%" in line:
                        if not self.size:
                            try:
                                # aria2c gives size always in MiB (hopefully)
                                size = re.findall('.*FileAlloc.*/(.*)\(', line)[0]
                                size = size.strip('MiB')
                                size = size.replace(',', '')
                                size = int(round(float(size))) * 1024 * 1024
                                self.size = size
                                self.update_view()
                                yield line
                            except:
                                pass
                    
                        result = re.findall('\(([0-9]{1,3})%\).*SPD:(.*) ETA:(.*)]', line)
       
                        if result:                            
                            self.progress = int(result[0][0])
                            self.speed = result[0][1]
                            self.est = result[0][2]                       
                            self.update_view()
                    else:        
                        yield line

                    time.sleep(1)
                
                ### Process is terminated                
                stdout = self.__process.stdout.read().strip()
                self._check_for_errors(stdout)
                yield stdout
                
            self.update_view()
            
        elif self.download_type in [DownloadTypes.OTR_DECODE, DownloadTypes.OTR_CUT]:
            if self.download_type == DownloadTypes.OTR_CUT:
                cutlist = Cutlist()
                cutlist.id = self.cutlist_id
                cutlist.download(self.cutlist_server, os.path.join(self.output, self.filename))
                command = self.command + ["-C", cutlist.local_filename]
            else:
                command = self.command
            
            try:
                self.__process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError, error:
                    self.status = DownloadStatus.ERROR
                    self.message_short = 'Dekoder nicht gefunden.'
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
                        self.progress = int(result[0])
                        
                    result = re.findall("[0-9]{1,3}%.*: (.*)", line)
                    if result:
                        self.speed = result[0]
                    
                    self.update_view()
                    
                    line = ''
                else:
                    line += char
            
            ### Process is terminated
                    
            stderr = self.__process.stderr.read()
            if "invalid option" in stderr:
                self.status = DownloadStatus.ERROR
                self.message_short = 'Der Dekoder ist veraltet.'
                yield "Es ist ein veralteter Dekoder angegeben!\n"
                
            yield stderr.strip()
            self._check_for_errors(stderr)
            
            if not self.status in [DownloadStatus.ERROR, DownloadStatus.STOPPED]:
                self._finished()
                # remove otrkey and .segments file
                fileoperations.remove_file(os.path.join(self.cache_dir, self.filename))
                fileoperations.remove_file(os.path.join(self.cache_dir, self.filename + '.segments'))

                if self.download_type == DownloadTypes.OTR_CUT:
                    # rename file to "cut" filename
                    filename = os.path.join(self.output, self.filename.rstrip(".otrkey"))
                    new_filename, extension = os.path.splitext(filename)
                    new_filename += ".cut" + extension
                    fileoperations.rename_file(filename, new_filename)
                                       
                    #TODO: Zusammenfassungsdialoganzeigemöglichkeit einblenden
                    
                self.update_view()
                
    def start(self):    
        def loop(*args):
            self.log.append(args[0])
            
        if not self.status == DownloadStatus.RUNNING:
            self.__task = GeneratorTask(self._download, loop)
            self.__task.start()
        
    def stop(self):    
        self._clear()
        self.update_view()        
        self.status = DownloadStatus.STOPPED    
            
        if self.__process:
            try:
                self.__process.kill()
            except OSError:
                pass
    
        if self.__task:
            self.__task.stop()
