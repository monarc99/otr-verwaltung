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
        self.speed = "?" 
        self.est = "?"  
        
        self.status = -1
        
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
        self.command = [decoder, "-b", "0", "-n", "-i", self.link, "-o", self.output, "-c", cache_dir, "-e", email, "-p", password]        
    
    def _clear(self):
        self.est = ""
        self.speed = ""    
      
    def _finished(self):
        yield "Download.....100%"
        self.status = DownloadStatus.FINISHED
        self.est = "Fertig."
        
    def _download(self):   
        self.log = []
        
        self.status = DownloadStatus.RUNNING
      
        if self.download_type == DownloadTypes.BASIC:            
            if self.preferred_downloader == 'wget':
                self.__process = subprocess.Popen(self.commands['wget'], stderr=subprocess.PIPE)
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
                
                yield self.__process.stderr.read().strip()
            
            else:
                self.__process = subprocess.Popen(self.commands['aria2c'], stdout=subprocess.PIPE)
                while True:
                    error_code = self.__process.poll()
                    if error_code:
                        if self.status != DownloadStatus.STOPPED:                            
                            if error_code == 0:
                                self._finished()
                            else:
                                self.status = DownloadStatus.ERROR
                        break
                    
                    line = self.__process.stdout.readline().strip()
                            
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
                
                yield self.__process.stdout.read().strip()
                
            self.update_view()
            
        elif self.download_type in [DownloadTypes.OTR_DECODE, DownloadTypes.OTR_CUT]:
            if self.download_type == DownloadTypes.OTR_CUT:
                cutlist = Cutlist()
                cutlist.id = self.cutlist_id
                cutlist.download(self.cutlist_server, os.path.join(self.output, self.filename))
                command = self.command + ["-C", cutlist.local_filename]
            else:
                command = self.command
            
            self.__process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
                        if self.progress == 100:
                            yield "Download.....100%"
                            self.status = DownloadStatus.FINISHED
                            self.est = "Fertig."
                        
                    result = re.findall("[0-9]{1,3}%.*: (.*)", line)
                    if result:
                        self.speed = result[0]
                    
                    self.update_view()
                    
                    line = ''
                else:
                    line += char
                    
            stderr = self.__process.stderr.read()
            for err in stderr.split('\n'):                
                yield err.strip()
                if "Fehler" in err:
                    self.status = DownloadStatus.ERROR
                
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
            self.__process.kill()
    
        if self.__task:
            self.__task.stop()
