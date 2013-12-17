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
            format = Format.MP4
            ac3name = root + ".HD.ac3"
        elif extension == '.mkv':
            if os.path.splitext(root)[1] == '.HQ':
                format = Format.HQ
                ac3name = os.path.splitext(root)[0] + ".HD.ac3"
            elif os.path.splitext(root)[1] == '.HD':
                format = Format.HD
                ac3name = root + ".ac3"
            else:
                format = Format.AVI
                ac3name = root + ".HD.ac3"
        else:
            return -1, None
    
        if os.path.isfile(ac3name):
            return format, ac3name
        else:
            return format, None

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
                     
        format, ac3 = self.get_format(filename)                 

        if format < 0:
            return -1, "Format konnte nicht bestimmt werden/wird noch nicht unterstützt.", False
                             
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
    
        try:
            index = open(filename + '.ffindex_track00.kf.txt', 'r')
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
                elif 'Color primaries' in line and 'BT.709-5' in line:
                    x264_opts.extend(bt709)
                elif 'Color primaries' in line and 'BT.470-6' in line:
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
                elif 'Encoding settings' in line:
                    for pair in line.strip().split(' : ')[1].split(' / '):
                        option,  value = pair.split('=', 1)
                        if option == 'cabac':
                            if value == '0':
                                x264_opts.extend(['--no-cabac'])
                        elif option == 'ref':
                            x264_opts.extend(['--ref',  value])
                        elif option == 'deblock':
                            enabled,  alpha,  beta = value.split(':', 2)
                            if enabled == '0':
                                x264_opts.extend(['-no-deblock'])
                            x264_opts.extend(['--deblock',  alpha+':'+beta])
                        elif option == 'me':
                            x264_opts.extend(['--me',  value])
                        elif option == 'subme':
                            x264_opts.extend(['--subme',  value])
                        elif option == 'psy':
                            if value == '0':
                                x264_opts.extend(['--no-psy'])
                        elif option == 'psy_rd':
                            rd,  trellis = value.split(':', 1)
                            x264_opts.extend(['--psy-rd',  rd+':'+trellis])
                        elif option == 'mixed_ref':
                            if value == '0':
                                x264_opts.extend(['--no-mixed-refs'])
                        elif option == 'me_range':
                            x264_opts.extend(['--merange',  value])
                        elif option == 'chroma_me':
                            if value == '0':
                                x264_opts.extend(['--no-chroma-me'])
                        elif option == 'trellis':
                            x264_opts.extend(['--trellis',  value])
                        elif option == '8x8dct':
                            if value == '0':
                                x264_opts.extend(['--no-8x8dct'])
                        elif option == 'deadzone':
                            inter,  intra = value.split(',', 1)
                            x264_opts.extend(['--deadzone-inter',  inter, '--deadzone-intra',  intra ])
                        elif option == 'fast_pskip':
                            if value == '0':
                                x264_opts.extend(['--no-fast-pskip'])
                        elif option == 'chroma_qp_offset':
                            x264_opts.extend(['--chroma-qp-offset',  value])
                        elif option == 'decimate':
                            if value == '0':
                                x264_opts.extend(['--no-dct-decimate'])
                        elif option == 'constrained_intra':
                            if value == '1':
                                x264_opts.extend(['--constrained-intra'])
                        elif option == 'bframes':
                            x264_opts.extend(['--bframes',  value])
                        elif option == 'b_pyramid':
                            x264_opts.extend(['--b-pyramid',  value])                            
                        elif option == 'b_adapt':
                            x264_opts.extend(['--b-adapt',  value])                            
                        elif option == 'b_bias':
                            x264_opts.extend(['--b-bias',  value])                            
                        elif option == 'direct':
                            if value == '0':
                                x264_opts.extend(['--direct',  'none'])                            
                            elif value == '1':
                                x264_opts.extend(['--direct',  'spatial'])                            
                            elif value == '2':
                                x264_opts.extend(['--direct',  'temporal'])                            
                            elif value == '3':
                                x264_opts.extend(['--direct',  'auto'])                            
                        elif option == 'weightb' or option == 'wpredb':
                            if value == '0':
                                x264_opts.extend(['--no-weightb'])
                        elif option == 'open_gop':
                            if value == '1':
                                x264_opts.extend(['--open-gop'])
                        elif option == 'weightp' or option == 'wpredp':
                            x264_opts.extend(['--weightp',  value])                            
                        elif option == 'keyint':
                            x264_opts.extend(['--keyint',  value])                            
                        elif option == 'keyint_min':
                            x264_opts.extend(['--min-keyint',  value])                            
                        elif option == 'scenecut':
                            x264_opts.extend(['--scenecut',  value])                            
                        elif option == 'intra_refresh':
                            if value == '1':
                                x264_opts.extend(['--intra-refresh'])
                        elif option == 'rc_lookahead':
                            x264_opts.extend(['--rc-lookahead',  value])                            
                        elif option == 'mbtree':
                            if value == '0':
                                x264_opts.extend(['--no-mbtree'])
                        elif option == 'crf':
                            x264_opts.extend(['--crf',  value])                            
                        elif option == 'qp':
                            x264_opts.extend(['--qp',  value])                            
                        elif option == 'qcomp':
                            x264_opts.extend(['--qcomp',  value])                            
                        elif option == 'qpmin':
                            x264_opts.extend(['--qpmin',  value])                            
                        elif option == 'qpmax':
                            x264_opts.extend(['--qpmax',  value])                            
                        elif option == 'qpstep':
                            x264_opts.extend(['--qpstep',  value])                            
                        elif option == 'ip_ratio':
                            x264_opts.extend(['--ipratio',  value])                            
                        elif option == 'pb_ratio':
                            x264_opts.extend(['--pbratio',  value])                            
                        elif option == 'aq':
                            if value == '0':
                                x264_opts.extend(['--aq-mode',  value ])
                            else:
                                mode,  strength = value.split(':', 1)
                                x264_opts.extend(['--aq-mode',  mode,  '--aq-strength',  strength])
                        elif option == 'lookahead_threads':
                            x264_opts.extend(['--sync-lookahead',  value])                            
                        elif option == 'sliced_threads':
                            if value != '0':
                                x264_opts.extend(['--sliced-threads'])            
                        elif option == 'constrained_intra':
                            x264_opts.extend(['--constrained-intra',  value])            
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
