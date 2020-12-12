from __future__ import print_function, division
import threading
import time
import numpy as np
import cv2
import pyaudio
import wave
import subprocess
import os
import pdb
import sys
from pynput.keyboard import KeyCode, Listener

class VideoThread(threading.Thread):

    def __init__(self, name="./tmp/temp_video.mp4", fourcc="mp4v", sizex=640, sizey=480, camindex=0, fps=60):
        threading.Thread.__init__(self)
        self.open = True
        self.device_index = camindex
        self.fps = fps                  # fps should be the minimum constant rate at which the camera can
        self.fourcc = fourcc            # capture images (with no decrease in speed over time; testing is required)
        self.video_cap = cv2.VideoCapture(self.device_index)

        self.width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
        self.height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)

        self.frameSize = (self.width, self.height) # video formats and sizes also depend and vary according to the camera used
        self.video_filename = name
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 1
        self.start_time = time.time()

    def run(self):
        "Video starts being recorded"
        # counter = 1
        timer_start = time.time()
        timer_current = 0
        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                self.frame_counts += 1
                time.sleep(1 / self.fps)
                # print("Video Thread recording")
            else:
                print("breaking!")
                break

    def close(self):
        print("Video thread set state to close")
        self.open = False

    def stop(self):
        "Finishes the video recording therefore the thread too"
        while self.open:
            time.sleep(1)

        print("Stop video thread")
        self.video_cap.release()
        self.video_out.release()
        cv2.destroyAllWindows()
        print("Finish writing video file")

class AudioThread(threading.Thread):
    "Audio class based on pyAudio and Wave"
    def __init__(self, filename="./tmp/temp_audio.wav", rate=16000, fpb=1024, channels=1):
        threading.Thread.__init__(self)
        self.open = True
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_filename = filename
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer = self.frames_per_buffer)
        self.audio_frames = []

    def run(self):
        "Audio starts being recorded"
        self.stream.start_stream()
        while self.open:
            data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
            self.audio_frames.append(data)

    def close(self):
        print("Audio thread set state to close")
        self.open = False

    def stop(self):
        "Finishes the audio recording therefore the thread too"
        while self.open:
            time.sleep(1)

        print("Stop audio thread")
        # Wait for audio thread to end itself
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        waveFile = wave.open(self.audio_filename, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.audio_frames))
        waveFile.close()
        print("Finish writing audio file")


def on_press(key):
    pass
    # print('{0} pressed'.format(key))

def on_release(key):
    print('{0} release'.format(key))
    if key.char == 'q':
        # Stop listener
        return False

def record():
    # Create new threads
    video_thread = VideoThread()
    audio_thread = AudioThread()

    # Start new Threads
    video_thread.start()
    audio_thread.start()

    for line in sys.stdin:
        print(line)
        if str(line) == "end\n":
            break

    end_time = time.time()

    # Close threads to prepare for stop
    audio_thread.close()
    video_thread.close()

    time.sleep(1)

    # Terminate threads completely
    audio_thread.stop()
    video_thread.stop()

    # Print video data
    frame_counts = video_thread.frame_counts
    elapsed_time = end_time - video_thread.start_time
    recorded_fps = frame_counts / elapsed_time

    print("total frames " + str(frame_counts))
    print("elapsed time " + str(elapsed_time))
    print("recorded fps " + str(recorded_fps))

    while threading.activeCount() > 1:
        print(threading.activeCount())
        print(video_thread.is_alive())
        print(audio_thread.is_alive())
        time.sleep(1)

    filename = "test"

    # Create empty files so that ffmpeg can work (do not know why though)
    # os.system("touch ./tmp/temp_video.mp4 ./tmp/temp_audio.wav ./tmp/temp_video2.mp4");

    # If the fps rate was higher/lower than expected, re-encode it to the expected
    print("Re-encoding")
    cmd = "yes | ffmpeg -threads 2 -r " + str(recorded_fps) + " -i ./tmp/temp_video.mp4 -r " + str(recorded_fps) + " ./tmp/temp_video2.mp4"
    subprocess.call(cmd, shell=True)

    print("Muxing")
    cmd = "yes | ffmpeg -channel_layout mono -i ./tmp/temp_audio.wav -i ./tmp/temp_video2.mp4 -c:v copy -c:a aac " + filename + ".mp4"
    subprocess.call(cmd, shell=True)

    # Create empty files so that ffmpeg can work (do not know why though)
    os.system("rm ./tmp/temp_video.mp4 ./tmp/temp_audio.wav ./tmp/temp_video2.mp4");

    print("Exiting Main Thread")

if __name__ == "__main__":
    record()
