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

import gobject
import threading

class GeneratorTask(object):
    def __init__(self, generator, loop_callback=None, complete_callback=None):
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback

    def _start(self, *args, **kwargs):
        self._stopped = False
       
        for ret in self.generator(*args, **kwargs):
            if self._stopped:
                return
                
            if self.loop_callback is not None:           
                gobject.idle_add(self._loop, ret)

        if self.complete_callback is not None:
            gobject.idle_add(self.complete_callback)

    def _loop(self, ret):
        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)           
       
        self.loop_callback(*ret)

    def start(self, *args, **kwargs):
        threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

    def stop(self):
        self._stopped = True
