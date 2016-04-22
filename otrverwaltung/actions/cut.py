# -*- coding: utf-8 -*-
### BEGIN LICENSE
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
import re
import subprocess
import bisect
import logging

from otrverwaltung.actions.baseaction import BaseAction
from otrverwaltung.constants import Action, Cut_action, Status, Format, Program
from otrverwaltung import fileoperations
from otrverwaltung import path


class Cut(BaseAction):

    def __init__(self, app, gui):
        self.update_list = True
        self.app = app
        self.config = app.config
        self.gui = gui
        
    def cut_file_by_cutlist(self):
        raise Exception("Override this method!")
    
    def create_cutlist(self):
        raise Exception("Override this method!")
        
    def get_format(self, filename):
        root, extension = os.path.splitext(filename)
    
        if extension == '.avi':
            bframe_delay = 2
            if os.path.splitext(root)[1] == '.HQ':
                format = Format.HQ
                ac3name = os.path.splitext(root)[0] + ".HD.ac3"
            elif os.path.splitext(root)[1] == '.HD':
                format = Format.HD
                ac3name = root + ".ac3"
            else:
                format = Format.AVI
                ac3name = root + ".HD.ac3"
        elif extension == '.mp4':
            bframe_delay = 0
            if os.path.splitext(root)[1] == '.HQ':
                format = Format.HQ
                ac3name = os.path.splitext(root)[0] + ".HD.ac3"
            elif os.path.splitext(root)[1] == '.HD':
                format = Format.HD
                ac3name = root + ".ac3"
            else:
                format = Format.MP4
                ac3name = root + ".HD.ac3"
        elif extension == '.mkv':
            bframe_delay = 2
            if os.path.splitext(root)[1] == '.HQ':
                format = Format.HQ
                ac3name = os.path.splitext(root)[0] + ".HD.ac3"
            elif os.path.splitext(root)[1] == '.HD':
                format = Format.HD
                ac3name = root + ".ac3"
            else:
                format = Format.AVI
                ac3name = root + ".HD.ac3"
        elif extension == '.ac3':
                format = Format.AC3
                ac3name = root
        else:
            return -1, None
    
        if os.path.isfile(ac3name):
            return format, ac3name, bframe_delay
        else:
            return format, None, bframe_delay

    def get_program(self, filename, manually=False):
        if manually:
            programs = { Format.AVI : self.config.get('general', 'cut_avis_man_by'),
                         Format.HQ  : self.config.get('general', 'cut_hqs_man_by'),
                         Format.HD  : self.config.get('general', 'cut_hqs_man_by'),
                         Format.MP4 : self.config.get('general', 'cut_mp4s_man_by') }
        else:
            programs = { Format.AVI : self.config.get('general', 'cut_avis_by'),
                         Format.HQ  : self.config.get('general', 'cut_hqs_by'),
                         Format.HD  : self.config.get('general', 'cut_hqs_by'),
                         Format.MP4 : self.config.get('general', 'cut_mp4s_by') }
                     
        format, ac3, bframe_delay = self.get_format(filename)

        if format < 0:
            return -1, "Format konnte nicht bestimmt werden/wird noch nicht unterstützt.", False

        if format == Format.AC3:
            return -1, "AC3 wird automatisch mit der HD.avi verarbeitet und nicht einzeln geschnitten.", False

        config_value = programs[format]

        if 'avidemux' in config_value:
            return Program.AVIDEMUX, config_value, ac3
        elif 'intern-VirtualDub' in config_value:
            return Program.VIRTUALDUB, path.get_internal_virtualdub_path('VirtualDub.exe'), ac3
        elif 'intern-vdub' in config_value:
            return Program.VIRTUALDUB, path.get_internal_virtualdub_path('vdub.exe'), ac3
        elif 'vdub' in config_value or 'VirtualDub' in config_value:
            return Program.VIRTUALDUB, config_value, ac3
        elif 'CutInterface' in config_value and manually:
            return Program.CUT_INTERFACE, config_value, ac3
        elif 'SmartMKVmerge' in config_value:
            return Program.SMART_MKVMERGE, config_value, ac3
        else:
            return -2, "Programm '%s' konnte nicht bestimmt werden. Es werden VirtualDub und Avidemux unterstützt." % config_value, False

    def generate_filename(self, filename, forceavi=0):
        """ generate filename for a cut video file. """

        root, extension = os.path.splitext(os.path.basename(filename))
        if forceavi == 1:
            extension = '.avi'
        new_name = root + "-cut" + extension

        cut_video = os.path.join(self.config.get('general', 'folder_cut_avis'), new_name)

        return cut_video

    def mux_ac3(self, filename, cut_video, ac3_file, cutlist):	# cuts the ac3 and muxes it with the avi into an mkv
        mkvmerge = self.config.get_program('mkvmerge')
        root, extension = os.path.splitext(filename)
        mkv_file = os.path.splitext(cut_video)[0] + ".mkv"
        # env
        my_env = os.environ.copy()
        my_env["LANG"] = "C"

        # creates the timecodes string for splitting the .ac3 with mkvmerge
        timecodes = (','.join([self.get_timecode(start) + ',' + self.get_timecode(start+duration) for start, duration in cutlist.cuts_seconds]))
        # splitting .ac3. Every second fragment will be used.
#        return_value = subprocess.call([mkvmerge, "--split", "timecodes:" + timecodes, "-o", root + "-%03d.mka", ac3_file])
        try:
            blocking_process = subprocess.Popen([mkvmerge, '--ui-language',  'en_US',  "--split", "timecodes:" + timecodes, "-o", root + "-%03d.mka", ac3_file ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,  env=my_env)
        except OSError as e:
            return None,  e.strerror + ": " + mkvmerge
        return_value = blocking_process.wait()
        # return_value=0 is OK, return_value=1 means a warning. Most probably non-ac3-data that has been omitted.
        # TODO: Is there some way to pass this warning to the conclusion dialog?
        if return_value != 0 and return_value != 1:
            return None, None, str(return_value)

        if len(cutlist.cuts_seconds) == 1:              # Only the second fragment is needed. Delete the rest.
            fileoperations.rename_file(root + "-002.mka", root + ".mka")
            fileoperations.remove_file(root + "-001.mka")
            if os.path.isfile(root + "-003.mka"):
                fileoperations.remove_file(root + "-003.mka")

        else:                                           # Concatenating every second fragment.
            command = [mkvmerge, "-o", root + ".mka", root + "-002.mka"]
            command[len(command):] = ["+" + root + "-%03d.mka" % (2*n) for n in range(2,len(cutlist.cuts_seconds)+1)]
#            return_value = subprocess.call(command)
            try:
                blocking_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,  env=my_env)
            except OSError as e:
                return None,  e.strerror + ": " + mkvmerge
            return_value = blocking_process.wait()
            if return_value != 0:               # There should be no warnings here
                return None, None, str(return_value)

            for n in range(1,2*len(cutlist.cuts_seconds)+2):    # Delete all temporary audio fragments
                if os.path.isfile(root + "-%03d.mka" % n):
                    fileoperations.remove_file(root + "-%03d.mka" % n)

        # Mux the cut .avi with the resulting audio-file into mkv_file
        # TODO: Is there some way to pass possible warnings to the conclusion dialog?
#        return_value = subprocess.call([mkvmerge, "-o", mkv_file, cut_video, root + ".mka"])
        try:
            blocking_process = subprocess.Popen([mkvmerge, "-o", mkv_file, cut_video, root + ".mka"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,  env=my_env)
        except OSError as e:
            return None,  e.strerror + ": " + mkvmerge
        return_value = blocking_process.wait()
        if return_value != 0 and return_value != 1:
            return None, None, str(return_value)

        fileoperations.remove_file(root + ".mka")       # Delete remaining temporary files
        fileoperations.remove_file(cut_video)
        return mkv_file, ac3_file, None

    def get_timecode(self, time):           # converts the seconds into a timecode-format that mkvmerge understands
        minute, second = divmod(int(time),60)		# discards milliseconds
        hour, minute = divmod(minute, 60)
        second = time - minute * 60 - hour * 3600	# for the milliseconds
        return "%02i:%02i:%f" % (hour, minute, second)


    def analyse_mediafile(self, filename):
        """ Gets fps, dar, sar, number of frames and id of the ac3_stream of a movie using ffmpeg.
            Returns without error:
                fps, dar, sar, max_frames, ac3_stream, None
            with error:
                None, None, None, None, None, error_message """
                
        try:
            process = subprocess.Popen([self.config.get_program('ffmpeg'), "-i", filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except OSError:
            return None, None, None, None, None,"FFMPEG (static) konnte nicht ausgeführt werden!"
    
        log = process.communicate()[0]
    
        video_infos_match = re.compile(r".*(Duration).*(\d{1,}):(\d{1,}):(\d{1,}.\d{1,}).*|.*(SAR) (\d{1,}:\d{1,}) DAR (\d{1,}:\d{1,}).*\, (\d{2,}\.{0,}\d{0,}) tbr.*|.*(Stream).*(\d{1,}:\d{1,}).*Audio.*ac3.*")
        seconds = 0
        ac3_stream = fps = dar = sar = None
    
        for line in log.split('\n'):
            m = re.search(video_infos_match,line)
    
            if m:
                if "Duration" == m.group(1):
                    try:
                        seconds = float(m.group(2))*3600 + float(m.group(3))*60 + float(m.group(4))
                    except ValueError:
                        return None, None, None, None,  "Dauer des Film konnte nicht ausgelesen werden."
                elif "SAR" == m.group(5):
                    try:
                        sar = m.group(6)
                        dar = m.group(7)
                        fps = float(m.group(8))
                    except ValueError:
                        return None, None, None, None,  "Video Stream Informationen konnte nicht ausgelesen werden."                        
                elif "Stream" == m.group(9):
                    ac3_stream = m.group(10)
            else:
                pass
                
        if seconds != 0 and fps != None and sar != None and dar != None:
            max_frames = seconds * fps
            return fps,  dar,  sar,  max_frames, ac3_stream,  None
    
        return None, None, None, None, None, "Es konnten keine Video Infos der zu bearbeitenden Datei ausgelesen werden."
    
    def get_keyframes_from_file(self, filename):
        """ returns keyframe list - in frame numbers"""
        
        if not os.path.isfile(filename + '.ffindex_track00.kf.txt'):
            try:
                command = [self.config.get_program('ffmsindex'),  '-p', '-f', '-k',  filename ]
                ffmsindex = subprocess.call(command)
            except OSError:
                return None, "ffmsindex konnte nicht aufgerufen werden."
    
        if os.path.isfile(filename + '.ffindex_track00.kf.txt'):
            filename_keyframes = filename + '.ffindex_track00.kf.txt'
        elif os.path.isfile(filename + '.ffindex_track01.kf.txt'):
            filename_keyframes = filename + '.ffindex_track01.kf.txt'
        elif os.path.isfile(filename + '.ffindex_track02.kf.txt'):
            filename_keyframes = filename + '.ffindex_track02.kf.txt'
        else:
            filename_keyframes = None

        try:
            index = open(filename_keyframes, 'r')
        except IOError:
            return None,  "Keyframe File von ffmsindex konnte nicht geöffnet werden."
        index.readline()
        index.readline()
        try:
            list =[int(i) for i in index.read().splitlines()]
        except ValueError:
            return None,  "Keyframes konnten nicht ermittelt werden."
        index.close()
        if os.path.isfile(filename + '.ffindex'):
            fileoperations.remove_file(filename +'.ffindex')
            
        return list,  None
    
    def get_keyframe_in_front_of_frame(self, keyframes,  frame):
        """Find keyframe less-than to frame."""
    
        i = bisect.bisect_left(keyframes, frame)
        if i:
            return keyframes[i-1]
        raise ValueError
    
    def get_keyframe_after_frame(self,  keyframes, frame):
        """Find keyframe greater-than to frame."""
       
        i = bisect.bisect_right(keyframes, frame)
        if i != len(keyframes):
            return keyframes[i]
        raise ValueError 
            
    def complete_x264_opts(self, x264_opts, filename):
        """Analyse filename and complete the x264 options 
        returns 
          x264_opts  x264 options
          x264_core  x264 core version
        """
        
        bt709 = ['--videoformat', 'pal', '--colorprim', 'bt709', '--transfer', 'bt709', '--colormatrix',  'bt709']
        bt470bg = ['--videoformat', 'pal', '--colorprim', 'bt470bg', '--transfer', 'bt470bg', '--colormatrix',  'bt470bg']
        
        try:
            blocking_process = subprocess.Popen([self.config.get_program('mediainfo'), filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        except OSError as e:
            return None, "Fehler: %s Filename: %s Error: %s" % str(e.errno),  str(e.filename),  str(e.strerror)
        except ValueError as e:
            return None,  "Falscher Wert: %s" % str(e)
        
        while True:
            line = blocking_process.stdout.readline()

            if line != '':
                if 'x264 core' in line:
                    print line
                    try:
                        x264_core = int(line.strip().split(' ')[30])
                        print x264_core
                    except ValueError as e:
                        continue
                    except IndexError as e:
                        continue
                elif 'Color primaries' in line and '709' in line:
                    x264_opts.extend(bt709)
                elif 'Color primaries' in line and '470' in line:
                    x264_opts.extend(bt470bg)
                elif 'Format profile' in line and '@L' in line:
                    try:
                        level = ['--level', str(float(line.strip().split('L')[1]))] # test for float
                        profile = ['--profile', line.strip().split('@L')[0].split(':')[1].lower().lstrip()]
                    except ValueError as e:
                        continue
                    except IndexError as e:
                        continue
                    x264_opts.extend(profile)
                    x264_opts.extend(level)
                elif 'Frame rate' in line:
                    try:
                        fps = ['--fps', str(float(line.strip().split(' ')[3]))]
                    except ValueError as e:
                        continue
                    except IndexError as e:
                        continue
                    x264_opts.extend(fps)
            else:
                break
        return x264_opts,  x264_core

    def show_progress(self, blocking_process):
        progress_match = re.compile(r".*(?<=\[|\ )(\d{1,}).*%.*")
        time_match = re.compile(r".*(\d{1,}):(\d{1,}):(\d{1,}.\d{1,}).*")
        mp4box_match = re.compile(r".*\((\d{2,})\/\d{2,}\).*")
        
        max_sec = 0.0
                
        while True:
            line = blocking_process.stdout.readline()
            logging.debug(line)
            if line == '':
                break
            elif 'x264 [info]: started' in line:
                self.gui.main_window.set_tasks_text('Kodiere Video')
                self.gui.main_window.set_tasks_progress(0)
            elif 'x264 [info]' in line:
                continue
            elif 'time=' in line:
                m = re.search(time_match,line)
                if m:
                    sec = float(m.group(1))*3600 + float(m.group(2))*60 + float(m.group(3))
                    self.gui.main_window.set_tasks_progress(int(sec/max_sec*100))
            elif '%' in line:
                m = re.search(progress_match,line)
                if m:
                    self.gui.main_window.set_tasks_progress(int(m.group(1)))
            elif 'Importing' in line:
                m = re.search(mp4box_match,line)
                if m:
                    self.gui.main_window.set_tasks_text('Importiere Stream')
                    self.gui.main_window.set_tasks_progress(int(m.group(1)))
            elif 'ISO File Writing' in line:
                m = re.search(mp4box_match,line)
                if m:
                    self.gui.main_window.set_tasks_text('Schreibe MP4')
                    self.gui.main_window.set_tasks_progress(int(m.group(1)))
            elif 'Duration' in line:
                m = re.search(time_match,line)
                if m:
                    max_sec = float(m.group(1))*3600 + float(m.group(2))*60 + float(m.group(3))
            elif 'video_copy' in line and '.mkv\' has been opened for writing' in line:
                self.gui.main_window.set_tasks_text('Splitte Video')
                self.gui.main_window.set_tasks_progress(0)
            elif 'audio_copy' in line and '.mkv\' has been opened for writing' in line:
                self.gui.main_window.set_tasks_text('Schneide Audio')
                self.gui.main_window.set_tasks_progress(0)
            elif '.mkv\' has been opened for writing.' in line:
                self.gui.main_window.set_tasks_text('Muxe MKV')                
                self.gui.main_window.set_tasks_progress(0)
            elif 'ffmpeg version' in line:
                self.gui.main_window.set_tasks_text('Kodiere Audio')
                self.gui.main_window.set_tasks_progress(0)
            else: 
                continue

            while events_pending():
                main_iteration(False)

    def get_norm_volume(self, filename, stream):
        """ Gets the volume correction of a movie using ffprobe. 
            Returns without error:              
                        norm_vol, None
                    with error:
                        1.0, error_message """
            
        self.gui.main_window.set_tasks_text('Berechne den Normalisierungswert')
        self.gui.main_window.set_tasks_progress(0)
        try:
            process1 = subprocess.Popen([path.get_tools_path('intern-ffprobe'), '-v',  'error','-of','compact=p=0:nk=1','-drc_scale','1.0','-show_entries','frame_tags=lavfi.r128.I','-f','lavfi','amovie='+filename+':si='+stream+',ebur128=metadata=1'], stdout=subprocess.PIPE)       
        except OSError:
            return "1.0", "FFMPEG wurde nicht gefunden!"            
                
        log = process1.communicate()[0]
            
    
        loudness = ref = -23
        for line in log.splitlines():
            sline = line.rstrip()
            if sline:
                loudness = sline
                adjust = ref - float(loudness)
        self.gui.main_window.set_tasks_progress(100)
        if adjust:
            return str(adjust)+'dB',  None
        else:
            return "1.0", "Volume konnte nicht bestimmt werden."

    def available_cpu_count(self):
        """ Number of available virtual or physical CPUs on this system, i.e.
        user/real as output by time(1) when called with an optimally scaling
        userspace-only program"""
    
        # cpuset
        # cpuset may restrict the number of *available* processors
        try:
            m = re.search(r'(?m)^Cpus_allowed:\s*(.*)$',
                          open('/proc/self/status').read())
            if m:
                res = bin(int(m.group(1).replace(',', ''), 16)).count('1')
                if res > 0:
                    return res
        except IOError:
            pass
    
        # Python 2.6+
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except (ImportError, NotImplementedError):
            pass
    
        # http://code.google.com/p/psutil/
        try:
            import psutil
            return psutil.NUM_CPUS
        except (ImportError, AttributeError):
            pass
    
        # POSIX
        try:
            res = int(os.sysconf('SC_NPROCESSORS_ONLN'))
    
            if res > 0:
                return res
        except (AttributeError, ValueError):
            pass
    
        # Windows
        try:
            res = int(os.environ['NUMBER_OF_PROCESSORS'])
    
            if res > 0:
                return res
        except (KeyError, ValueError):
            pass
    
        # jython
        try:
            from java.lang import Runtime
            runtime = Runtime.getRuntime()
            res = runtime.availableProcessors()
            if res > 0:
                return res
        except ImportError:
            pass
    
        # BSD
        try:
            sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'],
                                      stdout=subprocess.PIPE)
            scStdout = sysctl.communicate()[0]
            res = int(scStdout)
    
            if res > 0:
                return res
        except (OSError, ValueError):
            pass
    
        # Linux
        try:
            res = open('/proc/cpuinfo').read().count('processor\t:')
    
            if res > 0:
                return res
        except IOError:
            pass
    
        # Solaris
        try:
            pseudoDevices = os.listdir('/devices/pseudo/')
            res = 0
            for pd in pseudoDevices:
                if re.match(r'^cpuid@[0-9]+$', pd):
                    res += 1
    
            if res > 0:
                return res
        except OSError:
            pass
    
        # Other UNIXes (heuristic)
        try:
            try:
                dmesg = open('/var/run/dmesg.boot').read()
            except IOError:
                dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
                dmesg = dmesgProcess.communicate()[0]
    
            res = 0
            while '\ncpu' + str(res) + ':' in dmesg:
                res += 1
    
            if res > 0:
                return res
        except OSError:
            pass
    
        raise Exception('Can not determine number of CPUs on this system')
        
    def meminfo(self):
        """ return meminfo dict """
        
        meminfo=dict()
        with os.popen('cat /proc/meminfo') as f:
            for l in f:
                x = l.split()
                meminfo[x[0][:-1]] = int(x[1])
        return meminfo
