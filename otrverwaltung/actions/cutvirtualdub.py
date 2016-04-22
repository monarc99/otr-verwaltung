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
from otrverwaltung import codec
from otrverwaltung import fileoperations

class CutVirtualdub(Cut):

    def __init__(self, app, gui):
        self.update_list = True
        self.app = app
        self.config = app.config
        self.gui = gui
        
    def __del__(self):
        # clean up
        pass
        
    def cut_file_by_cutlist(self, filename, cutlist=None,  program_config_value=None):
        return self.__cut_file_virtualdub(filename, program_config_value, cutlist.cuts_frames)

    def create_cutlist(self,  filename, program_config_value):
        cut_video_is_none, error = self.__cut_file_virtualdub(filename, program_config_value, cuts=None, manually=True)
 
        if error != None:
            return None,  error
        format, ac3_file, bframe_delay = self.get_format(filename)
        cuts_frames, cutlist_error = self.__create_cutlist_virtualdub(os.path.join(self.config.get('general', 'folder_uncut_avis'), "cutlist.vcf"), format)

        return cuts_frames,  cutlist_error

    def __cut_file_virtualdub(self, filename, config_value, cuts=None, manually=False):
        format, ac3_file, bframe_delay = self.get_format(filename)
        fps, dar, sar, max_frames, ac3_stream, error = self.analyse_mediafile(filename)
        if sar == None or dar == None:
            return None, error
            
        # find wine
        cmd_exists = lambda x: any(os.access(os.path.join(pathx, x), os.X_OK) for pathx in os.environ["PATH"].split(os.pathsep))
        if cmd_exists('wineconsole'):
            winecommand = 'wineconsole'
        elif cmd_exists('wine'):
            winecommand = 'wine'
        else:
            return None, "Wine konnte nicht aufgerufen werden."
        
            
        if format == Format.HQ:
            if self.config.get('general', 'h264_codec') == 'ffdshow':
                if dar == "16:9":
                    comp_data = codec.get_comp_data_h264_169()
                else:
                    comp_data = codec.get_comp_data_h264_43()
                compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'x264vfw':
                comp_data = codec.get_comp_data_x264vfw_dynamic(sar,self.config.get('general', 'x264vfw_hq_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'komisar':
                comp_data = codec.get_comp_data_komisar_dynamic(sar,self.config.get('general', 'komisar_hq_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            else:
                return None, "Codec nicht unterstützt. Nur ffdshow, x264vfw und komisar unterstützt."

        elif format == Format.HD:
            if self.config.get('general', 'h264_codec') == 'ffdshow':
                if dar == "16:9":
                    comp_data = codec.get_comp_data_hd_169()
                else:
                    comp_data = codec.get_comp_data_hd_43()
                compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'x264vfw':
                comp_data = codec.get_comp_data_x264vfw_dynamic(sar,self.config.get('general', 'x264vfw_hd_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'komisar':
                comp_data = codec.get_comp_data_komisar_dynamic(sar,self.config.get('general', 'komisar_hd_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            else:
                return None, "Codec nicht unterstützt. Nur ffdshow, x264vfw und komisar unterstützt."

        elif format == Format.MP4:
            if self.config.get('general', 'h264_codec') == 'komisar':
                comp_data = codec.get_comp_data_komsiar_dynamic(sar,self.config.get('general', 'komisar_mp4_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            else:
                comp_data = codec.get_comp_data_x264vfw_dynamic(sar,self.config.get('general', 'x264vfw_mp4_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
        elif format == Format.AVI:
            comp_data = codec.get_comp_data_dx50()
            compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
        else:
            return None, "Format nicht unterstützt (Nur Avi DX50, HQ H264 und HD sind möglich)."

        # make file for virtualdub scripting engine
        if manually:
            # TODO: kind of a hack
            curr_dir = os.getcwd()
            try:
                os.chdir(os.path.dirname(config_value))
            except OSError:
                return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value

        self.gui.main_window.set_tasks_progress(50)
        while events_pending():
                main_iteration(False)

        f = open("/tmp/tmp.vcf", "w")

        if not manually:
            f.write('VirtualDub.Open("%s");\n' % filename)

        if self.config.get('general', 'smart'):
            f.writelines([
                'VirtualDub.video.SetMode(1);\n',
                'VirtualDub.video.SetSmartRendering(1);\n',
                compression,
                'VirtualDub.video.SetCompData(%s);\n' % comp_data
                ])
        else:
            f.write('VirtualDub.video.SetMode(0);\n')

        f.write('VirtualDub.subset.Clear();\n')

        if not manually:
            keyframes, error = self.get_keyframes_from_file(filename)
            
            if keyframes == None:
                return None,  "Keyframes konnten nicht ausgelesen werden."
            
            for frame_start, frames_duration in cuts:
                # interval does not begin with keyframe
                if not frame_start in keyframes and format == Format.HQ or format == Format.HD:
                    try: # get next keyframe
                        frame_start_keyframe =self.get_keyframe_after_frame(keyframes, frame_start)
                    except ValueError:
                        frame_start_keyframe = -1
                        
                    if frame_start+frames_duration > frame_start_keyframe:
                        # 'Smart Rendering Part mit anschließenden kopierten Part'
                        if frame_start_keyframe < 0:
                            # copy end of file
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+2, frames_duration-2))
                        else:
                            # smart rendering part  (duration -2 due to smart rendering bug)
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+2, frame_start_keyframe-frame_start-2))
                            #vd smart rendering bug
                            if ac3_file != None:
                                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start_keyframe-1, 1))                            
                                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start_keyframe-1, 1))                            
                            # copy part
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start_keyframe, frames_duration-(frame_start_keyframe-frame_start)))
                    else:
                        print 'reiner Smart Rendering Part'
                        try: # get next keyframe after the interval
                            next_keyframe = self.get_keyframe_after_frame(keyframes, frame_start+frames_duration-2)
                        except ValueError:
                            next_keyframe = -1   
                        if next_keyframe - (frame_start+frames_duration) > 2:
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+2, frames_duration))
                        else:
                            # workaround for smart rendering bug
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+2, frames_duration-2))
                            if ac3_file != None:
                                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (next_keyframe-1, 1))                            
                                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (next_keyframe-1, 1))                            
                else:
                    if not (frame_start+frames_duration) in keyframes and format == Format.HQ or format == Format.HD:
                        # 'Kopieren mit keinem Keyframe am Ende'
                        f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start, frames_duration-2))
                        # we all love workarounds
                        if ac3_file != None:
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+frames_duration-1, 1))
                            f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start+frames_duration-1, 1))
                    else:
                        print 'reines Kopieren'
                        f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start, frames_duration))
                        
            cut_video = self.generate_filename(filename,1)

            f.writelines([
                'VirtualDub.SaveAVI("%s");\n' % cut_video,
                'VirtualDub.Close();'
                ])

        f.close()

        # start vdub
        if not os.path.exists(config_value):
            return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value

        if manually:
            win_filename = "Z:" + filename.replace(r"/", r"\\")
            command = 'VirtualDub.exe /s Z:\\\\tmp\\\\tmp.vcf "%s"' % win_filename
        else:
            command = "%s /s Z:\\\\tmp\\\\tmp.vcf /x" % config_value

        if 'intern-VirtualDub' in config_value:
            command = 'WINEPREFIX=' + os.path.dirname(config_value) + '/wine' + " " + winecommand + " " + command
        else:
            command = winecommand + " " + command
        
        try:
            vdub = subprocess.Popen(command, shell=True)
        except OSError:
            return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value

        while vdub.poll() == None:
            time.sleep(1)

            while events_pending():
                main_iteration(False)

        fileoperations.remove_file('/tmp/tmp.vcf')

        if manually:
            os.chdir(curr_dir)
            return None, None

        return cut_video, None

    def __create_cutlist_virtualdub(self, filename, format):
        """ returns: cuts, error_message """

        try:
            f = open(filename, 'r')
        except IOError:
            return None, "Die VirtualDub-Projektdatei konnte nicht gelesen werden.\nWurde das Projekt in VirtualDub nicht gespeichert?\n(Datei: %s)." % filename

        cuts_frames = [] # (start, duration)
        count = 0

        for line in f.readlines():
            if "VirtualDub.subset.AddRange" in line:
                try:
                    start, duration = line[line.index('(') + 1 : line.index(')')].split(',')
                except (IndexError, ValueError), message:
                    return None, "Konnte Schnitte nicht lesen, um Cutlist zu erstellen. (%s)" % message

                if format == Format.HQ or format == Format.HD:
                    cuts_frames.append((int(start)-2, int(duration)))
                else:
                    cuts_frames.append((int(start), int(duration)))

        if len(cuts_frames) == 0:
            return None, "Konnte keine Schnitte finden!"

        fileoperations.remove_file(filename)

        return cuts_frames, None
