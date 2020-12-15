import subprocess
import numpy as np

source_video_path = input()

# Separate video and audio into two files
cmd = f"yes | ffmpeg -i {source_video_path} ./tmp/only_audio.wav"
subprocess.call(cmd, shell=True)

cmd = f"yes | ffmpeg -i {source_video_path} -an -vcodec copy ./tmp/only_video.mp4"
subprocess.call(cmd, shell=True)

# Separate vocals and audios
cmd = f"yes | spleeter separate -i ./tmp/only_audio.wav -p spleeter:2stems -o ./tmp/"
subprocess.call(cmd, shell=True)

# Generate MVs with different vocal percentages
for i in np.arange(0, 1.2, 0.2):
    cmd = f"yes | ffmpeg  -i ./tmp/only_video.mp4 -channel_layout stereo -i ./tmp/only_audio/vocals.wav -channel_layout stereo -i ./tmp/only_audio/accompaniment.wav -filter_complex '[1]volume={i}[a1];[2]volume=1[a2];[a1][a2]amix=inputs=2[a]' -map 0:v -map '[a]' -c:v copy ./tmp/mixed_{int(i*100)}.mp4"
    subprocess.call(cmd, shell=True)
