import threading
import time
import numpy as np
import cv2
import pyaudio
import wave
import subprocess
import os
import sys
import pdb

class VideoThread(threading.Thread):

    def __init__(self, name="./tmp/temp_video.mp4", fourcc="mp4v", camindex=0, fps=60):
        threading.Thread.__init__(self)
        # State of the of the video thread
        self.open = True
        self.closed = False

        self.device_index = camindex    # for web cam
        self.fps = fps                  # fps captured by camera
        self.fourcc = fourcc            # to specify the recorded data format

        self.video_cap = cv2.VideoCapture(self.device_index)

        # Recorded frame size of our video (depend and vary according to the camera used)
        self.width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
        self.height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
        self.frameSize = (self.width, self.height)

        self.video_filename = name

        # Video writers and output
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)

        self.frame_counts = 1
        self.start_time = time.time()

    # Main method to record video
    def run(self):
        "Start recording video"
        while self.open:
            # Read frame
            ret, video_frame = self.video_cap.read()
            # Write to file if successful
            if ret:
                self.video_out.write(video_frame)
                self.frame_counts += 1
                time.sleep(1 / self.fps)
            else:
                break

        # Indicate that the thread is completely done with run()
        self.closed = True

    # Called when ending signal is received
    def close(self):
        print("Video thread set state to close")
        self.open = False

    # Release and clean up the objects we used for recording the video
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
    def __init__(self, filename="./tmp/temp_audio.wav", rate=16000, fpb=1024, channels=1):
        threading.Thread.__init__(self)

        # State of the of the audio thread
        self.open = True
        self.closed = False
        # Specifications for audio recorded
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_filename = filename
        self.audio = pyaudio.PyAudio()
        # Stream that records the audio
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer = self.frames_per_buffer,
                                      )
        # Store the audio frames recorded
        self.audio_frames = []

    # Main method to record audio
    def run(self):
        "Start recording audio"
        self.stream.start_stream()
        # Read data from microphone
        while self.open:
            data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
            self.audio_frames.append(data)
        # Indicate that the thread is completely done with run()
        self.closed = True

    # Called when ending signal is received
    def close(self):
        print("Audio thread set state to close")
        self.open = False

    # Release and clean up the objects we used for recording the audio
    def stop(self):
        "Finishes the audio recording therefore the thread too"
        while self.open:
            time.sleep(1)

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        # Wrtie the file with the data we stored in the list
        waveFile = wave.open(self.audio_filename, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.audio_frames))
        waveFile.close()

        print("Finish writing audio file")

if __name__ == "__main__":

    # Create new threads
    video_thread = VideoThread()
    audio_thread = AudioThread()

    # Start new Threads
    video_thread.start()
    audio_thread.start()

    # If parent process sends end signal through pipe, start termination process
    for line in sys.stdin:
        if str(line) == "end\n":
            break

    # Record ending time of recording
    end_time = time.time()

    # Close threads to prepare for stop
    audio_thread.close()
    video_thread.close()

    # Wait for the two threads to close completely by polling
    while not (audio_thread.closed and video_thread.closed):
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

    # Wait until all threads have completely closed
    while threading.activeCount() > 1:
        time.sleep(1)

    filename = "recording"

    # If the fps rate was higher/lower than expected, re-encode it to the expected
    print("Re-encoding")
    cmd = "yes | ffmpeg -threads 2 -r " + str(recorded_fps) + " -i ./tmp/temp_video.mp4 -r " + str(recorded_fps) + " ./tmp/temp_video2.mp4"
    subprocess.call(cmd, shell=True)

    # Mux the audio with the video
    print("Muxing")
    cmd = "yes | ffmpeg -channel_layout mono -i ./tmp/temp_audio.wav -i ./tmp/temp_video2.mp4 -c:v copy -c:a aac " + filename + ".mp4"
    subprocess.call(cmd, shell=True)

    # Remove unused files
    os.remove("tmp/temp_video.mp4")
    os.remove("tmp/temp_audio.wav")
    os.remove("tmp/temp_video2.mp4")

    print("Exiting Main Thread")

