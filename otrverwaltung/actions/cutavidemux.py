# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
# Copyright (C) 2013 Markus Liebl <lieblm@web.de>
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


from gtk import events_pending, main_iteration, RESPONSE_OK
import os
import subprocess
import time

from otrverwaltung.actions.cut import Cut
from otrverwaltung.constants import Action, Cut_action, Status, Format, Program
from otrverwaltung import path
from otrverwaltung import fileoperations

class CutAvidemux(Cut):

    def __init__(self, app, gui):
        self.update_list = True
        self.app = app
        self.config = app.config
        self.gui = gui
        
    def __del__(self):
        # clean up
        pass
        
    def cut_file_by_cutlist(self, filename, cutlist=None,  program_config_value=None):
        return self.__cut_file_avidemux(filename, program_config_value, cutlist.cuts_frames)
        

    def create_cutlist(self,  filename, program_config_value):
        """ read cuts from avidemux 2 and 3
            returns cut_frames und cutlist_error """
            
        format, ac3_file = self.get_format(filename)
        fps, dar, sar, max_frames, ac3_stream, error = self.analyse_mediafile(filename)
        if fps == None:
            return None, error
            
        # env
        my_env = os.environ.copy()
        my_env["LANG"] = "C"
        my_env["LC_COLLATE"] = "C"
        
        if '.avi' in filename and "avidemux3" in program_config_value: 
            try:
                mkvmerge = subprocess.Popen([self.config.get_program('mkvmerge'),  '--ui-language',  'en_US', '-o', filename+'.mkv', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,  env=my_env)
                self.show_progress(mkvmerge)
                returncode = mkvmerge.wait()
                if returncode != 0 and returncode != 1:
                    return None,  'Fehler beim Muxen zu MKV'
            except OSError:
                return "mkvmerge konnte nicht aufgerufen werden.", None, None
            
        try:
            if os.path.isfile(filename+'.mkv'):
                avidemux = subprocess.Popen([program_config_value, filename+'.mkv'], bufsize=-1 ,stdout=subprocess.PIPE)
            else:
                avidemux = subprocess.Popen([program_config_value, filename], bufsize=-1 ,stdout=subprocess.PIPE)
        except OSError:
            if os.path.isfile(filename+'.mkv'):
                fileoperations.remove_file(filename+'.mkv')
            return "Avidemux konnte nicht aufgerufen werden: " + program_config_value, None
            
        seg_lines = []
        pts_correction = 0
    
        for line in avidemux.stdout.readlines():
            if line.startswith(' Seg'):
                # delete not interesting parts
                line = line[:line.find("audio")]

                parts = line.split(',')

                seg_id = int(parts[0].split(':')[-1])
                if format == Format.HQ or format == Format.HD:
                    start = int(parts[1].split(':')[-1])-2
                else:
                    start = int(parts[1].split(':')[-1])
                size = int(parts[2].split(':')[-1])
                seg_lines.append((seg_id, start, size))

            # Avidemux3
            # The first frame has a PTS >0, adjusting to 40 ms
            elif '[addReferenceVideo]  The first frame has a PTS >0' in line:
                pts_correction = float(line.split(' ')[13])*1000
            elif line.startswith(' We have '):
                seg_lines = []
            elif line.startswith('Segment :'):
                line = line[line.find(':')+1:]
                seg_id = int(line.split('/')[0])
            elif 'duration     :' in line:
                line = line[line.find(':')+1:]
                size = (float(line.split(' ')[0]))*fps/1000000
            elif 'refStartPts  :' in line:
                line = line[line.find(':')+1:]
                start = (float(line.split(' ')[0])-pts_correction)*fps/1000000
                if start > 0:
                    seg_lines.append((seg_id, start, size))
                else:
                    # correct values for first keyframe
                    seg_lines.append((seg_id, 0.0, size-fps*pts_correction/1000000))
            else:
                pass

        # keep only necessary items
        seg_lines.reverse()
        temp_cuts = []

        for seg_id, start, duration in seg_lines:
            if seg_id == 0:
                temp_cuts.append((start, duration))
                break
            else:
                temp_cuts.append((start, duration))

        temp_cuts.reverse()

        cuts_frames = []
        count = 0
        for start, duration in temp_cuts:
            cuts_frames.append((start, duration))
            count += 1

        if os.path.isfile(filename+'.mkv'):
            fileoperations.remove_file(filename+'.mkv')

        if len(cuts_frames) == 0:
            cutlist_error = "Es wurde nicht geschnitten."
        else:
            cutlist_error = None
            
        return cuts_frames,  cutlist_error
    
    def __cut_file_avidemux(self, filename, program_config_value, cuts):
        format, ac3_file = self.get_format(filename)
        # make file for avidemux2.5 scripting engine
        f = open("tmp.js", "w")

        f.writelines([
            '//AD\n',
            'var app = new Avidemux();\n',
            '\n'
            '//** Video **\n',
            'app.load("%s");\n' % filename,
            '\n',
            'app.clearSegments();\n'
            ])

        for frame_start, frames_duration in cuts:
            if format == Format.HQ or format == Format.HD:
                #2-Frame-Delay for HQ,HD Format
                f.write("app.addSegment(0, %i, %i);\n" %(frame_start+2, frames_duration))
            else:
                f.write("app.addSegment(0, %i, %i);\n" %(frame_start, frames_duration))

        cut_video = self.generate_filename(filename)

        f.writelines([
            '//** Postproc **\n',
            'app.video.setPostProc(3,3,0);\n'
            ])

        if self.config.get('general', 'smart'):
            f.write('app.video.codec("Copy","CQ=4","0");\n')

        f.writelines([
            '//** Audio **\n',
            'app.audio.reset();\n',
            'app.audio.codec("copy",128,0,"");\n',
            'app.audio.normalizeMode=0;\n',
            'app.audio.normalizeValue=0;\n',
            'app.audio.delay=0;\n',
            'app.audio.mixer="NONE";\n',
            'app.audio.scanVBR="";\n',
            'app.setContainer="AVI";\n',
            'setSuccess(app.save("%s"));\n' % cut_video
            ])

        f.close()

        # start avidemux:
        try:
            avidemux = subprocess.Popen([program_config_value, "--nogui", "--force-smart", "--run", "tmp.js", "--quit"], stderr=subprocess.PIPE)
        except OSError:
            return None, "Avidemux konnte nicht aufgerufen werden: " + program_config_value

        self.gui.main_window.set_tasks_progress(50)

        while avidemux.poll() == None:
            time.sleep(1)
#            TODO: make it happen
#            line = avidemux.stderr.readline()
#
#            if "Done:" in line:
#                progress = line[line.find(":") + 1 : line.find("%")]
#                self.gui.main_window.set_tasks_progress(int(progress))
#
            while events_pending():
                main_iteration(False)

        fileoperations.remove_file('tmp.js')

        return cut_video, None

