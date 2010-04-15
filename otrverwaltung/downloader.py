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
import sys

from otrverwaltung.GeneratorTask import GeneratorTask

class DownloadTypes:
    TORRENT     = 0
    WGET        = 1
    OTR_DECODE  = 2
    OTR_CUT     = 3    

class Download:
    
    def __init__(self, command, filename, download_type):
        self.command = command
        self.filename = filename
        self.download_type = download_type
        
        self.size = ""
        self.progress = "?"
        self.speed = "?" 
        self.est = "?"
        self.log = []
        
        self.__task = None
        self.__process = None
        
    def _download(self):     
        if self.download_type == DownloadTypes.WGET:
            self.__process = subprocess.Popen(self.command, stderr=subprocess.PIPE)
            while self.__process.poll() == None:
                line = self.__process.stderr.readline().strip()
                        
                if line:
                    if not self.size:
                        result = re.findall(': ([0-9]*) \(', line)
                        if result:
                            self.size = result[0]                            
                    
                    if "%" in line:                                                
                        result = re.findall('([0-9]{1,3}%) (.*)[ =](.*)', line)

                        if result:
                            self.progress = result[0][0]
                            self.speed = result[0][1]
                            if self.progress == "100%":
                                yield "Download.....100%"
                                self.est = "Fertig."
                            else:
                                self.est = result[0][2]
                   
                    else:        
                        yield line    
                                    
                    self.update_view()
                    
                time.sleep(1)
            
            yield self.__process.stderr.read().strip()
            
        elif self.download_type in [DownloadTypes.OTR_DECODE, DownloadTypes.OTR_CUT]:       
            self.__process = subprocess.Popen("%s  >/tmp/stdout 2>&1" % " ".join(self.command), shell=True)

            # TODO: cleanup
            while self.__process.poll()==None:
                file = open('/tmp/stdout', 'r')
                stdout = file.readlines()                
                file.close()
                                
                if len(stdout)>0 and "%" in stdout[-1]:
                    result = re.findall("([0-9]{1,3}%).*: (.*)", stdout[-1].strip())
                    if result:
                        self.progress = result[0][0]
                        self.speed = result[0][1]
                        self.update_view()
                        
                time.sleep(2)
                
            file = open('/tmp/stdout', 'r')
            self.log = file.readlines()
            file.close()
            
    def start(self):    
        def loop(*args):
            self.log.append(args[0])
        
        def completed():
            pass
    
        self.__task = GeneratorTask(self._download, loop, completed)
        self.__task.start()
        
    def stop(self):
        if self.__task:
            self.__task.stop()
            self.__task = None
            
        if self.__process:
            self.__process.kill()
            self.__process = None
