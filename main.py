import ast
import os
import sys
from pynput.keyboard import KeyCode, Listener
import subprocess
import numpy
import time
import threading

os.environ['KIVY_VIDEO'] = "ffpyplayer"
os.environ["KIVY_PROFILE_LANG"] = "1"

import kivy
from pathlib import Path

kivy.require('1.9.1')

from kivy.core.window import Window
from kivy.factory import Factory  # NOQA: F401
from kivy.lang import Builder
from kivy.loader import Loader
from kivy.uix.videoplayer import VideoPlayer
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast


from libs.baseclass.dialog_change_theme import (
    ProjectDialogChangeTheme,
    ProjectUsageCode,
)
from libs.baseclass.expansionpanel import ProjectExpansionPanelContent
from libs.baseclass.list_items import (  # NOQA: F401
    ProjectOneLineLeftIconItem,
)

from kivymd import __version__, images_path
from kivymd.app import MDApp
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine

if getattr(sys, "frozen", False):  # bundle mode with PyInstaller
    os.environ["PROJECT_ROOT"] = sys._MEIPASS
else:
    sys.path.append(os.path.abspath(__file__).split("demos")[0])
    os.environ["PROJECT_ROOT"] = str(Path(__file__).parent)
    # os.environ["PROJECT_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    print(f'PROJECT ROOT = {os.environ["PROJECT_ROOT"]}')


os.environ["PROJECT_ASSETS"] = os.path.join(
    os.environ["PROJECT_ROOT"], f"assets{os.sep}"
)
Window.softinput_mode = "below_target"
class ProjectApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Teal"
        self.dialog_change_theme = None
        self.toolbar = None
        self.data_screens = {}
        self.recording = False

        # Initialize file manager status
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
        )
        # Detect only .mp4 extensions
        self.file_manager.ext = [".mp4"]

        print(f"images_path = {images_path}")
        Loader.loading_image = f"{images_path}transparent.png"

    def build(self):

        Window.bind(on_request_close=self.on_request_close)

        return Builder.load_file(
            f"{os.environ['PROJECT_ROOT']}/libs/kv/start_screen.kv"
        )

    # When kivy app is closed
    def on_request_close(self, *args):
        print("on request close")
        os.system("rm -rf ./tmp/*")
        self.stop()
        return True

    def file_manager_open(self):
        self.file_manager.show(f"{os.environ['PROJECT_ROOT']}")  # output manager to the screen
        self.manager_open = True

    # Select path for video
    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        self.exit_manager()
        toast(path)

        # Set video path
        self.source_video_path = path
        self.video_player = self.root.ids["backdrop_front_layer"].ids["video_player"]

        # Render videos with different vocal percentages
        self.render_videos()

        self.slider = self.root.ids["backdrop_front_layer"].ids["slider"]
        self.slider.bind(value = self.on_value)

    # Change video based on slider
    def on_value(self, instance, percentage):
        self.video_player.source = f"./tmp/mixed_{int(percentage)}.mp4"

    def render_videos(self):

        # Separate video and audio into two files
        cmd = f"yes | ffmpeg -i {self.source_video_path} ./tmp/only_audio.wav"
        subprocess.call(cmd, shell=True)

        cmd = f"yes | ffmpeg -i {self.source_video_path} -an -vcodec copy ./tmp/only_video.mp4"
        subprocess.call(cmd, shell=True)

        # Separate vocals and audios
        cmd = f"yes | spleeter separate -i ./tmp/only_audio.wav -p spleeter:2stems -o ./tmp/"
        subprocess.call(cmd, shell=True)

        # Generate MVs with different vocal percentages
        for i in numpy.arange(0, 1.2, 0.2):
            cmd = f"yes | ffmpeg  -i ./tmp/only_video.mp4 -channel_layout stereo -i ./tmp/only_audio/vocals.wav -channel_layout stereo -i ./tmp/only_audio/accompaniment.wav -filter_complex '[1]volume={i}[a1];[2]volume=1[a2];[a1][a2]amix=inputs=2[a]' -map 0:v -map '[a]' -c:v copy ./tmp/mixed_{int(i*100)}.mp4"
            subprocess.call(cmd, shell=True)

        # Set default to 0
        self.video_player.source = "./tmp/mixed_0.mp4"

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''
        self.manager_open = False
        self.file_manager.close()

    def show_dialog_change_theme(self):
        if not self.dialog_change_theme:
            self.dialog_change_theme = ProjectDialogChangeTheme()
            self.dialog_change_theme.set_list_colors_themes()
        self.dialog_change_theme.open()

    def on_start(self):
        """Creates a list of items with examples on start screen."""
        Builder.load_file(
            f"{os.environ['PROJECT_ROOT']}/libs/kv/dialog_change_theme.kv",
        )
        Builder.load_file(
            f"{os.environ['PROJECT_ROOT']}/libs/kv/base_content.kv",
        )

    def back_to_home_screen(self):
        self.root.ids.screen_manager.current = "home"

    def switch_theme_style(self):
        self.theme_cls.theme_style = (
            "Light" if self.theme_cls.theme_style == "Dark" else "Dark"
        )
        self.root.ids.backdrop.ids._front_layer.md_bg_color = [0, 0, 0, 0]

    def callback_for_menu_items(self, *args):
        toast(args[0])

    # Starts our recording process
    def record(self):
        self.recording_process = subprocess.Popen(["python3", "-u", f"{os.environ['PROJECT_ROOT']}/record/video.py"], stdin=subprocess.PIPE, bufsize=1, universal_newlines=True)
        self.recording_process.stdin.write("Start Recording!!\n")

    # Terminates our recording process
    def stop_record(self):
        self.recording_process.stdin.write("end\n")
        print("finish writing end to child")

    # Recording button is pressed
    def button_record(self):
        if self.recording:
            print("stop recording")
            self.recording = False
            self.stop_record()
        else:
            print("start recording")
            self.recording = True
            self.record()

    def add_expansion_panel(self, card):
        content = ProjectExpansionPanelContent()
        card.add_widget(
            MDExpansionPanel(
                icon=f"{os.environ['PROJECT_ASSETS']}avatar.png",
                content=content,
                panel_cls=MDExpansionPanelOneLine(text=f"KivyMD {__version__}"),
            )
        )


ProjectApp().run()
