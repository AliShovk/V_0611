"""Пост-обработка готовых кадров эпизода: vgen/postfx.finish + перекодирование."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/root/Vgen_041126')
from PIL import Image

from vgen import postfx

SRC = '/root/Vgen_041126/storage/cartoon-gazobeton-v3/frames'
DST = '/root/Vgen_041126/storage/cartoon-gazobeton-v3/frames_post'
OUT = '/root/Vgen_041126/storage/cartoon-gazobeton-v3'
FFMPEG = '/usr/bin/ffmpeg'

os.makedirs(DST, exist_ok=True)


def work(name):
    img = Image.open(os.path.join(SRC, name)).convert('RGB')
    out = postfx.finish(img)
    out.save(os.path.join(DST, name), quality=95)


names = sorted(os.listdir(SRC))
with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(work, names))
print('обработано кадров:', len(names))

silent = os.path.join(OUT, 'video_post_silent.mp4')
subprocess.run([FFMPEG, '-y', '-v', 'error', '-framerate', '30',
                '-i', os.path.join(DST, 'f%05d.png'), '-i', os.path.join(OUT, 'voice.mp3'),
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', silent],
               check=True)

final = os.path.join(OUT, 'final_post.mp4')
subprocess.run([FFMPEG, '-y', '-v', 'error', '-i', silent, '-i', os.path.join(OUT, 'sfx.wav'),
                '-filter_complex', '[1:a]volume=0.35[sfx];[0:a][sfx]amix=inputs=2:duration=first:dropout_transition=2[a]',
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
                '-shortest', '-movflags', '+faststart', final], check=True)
print('готово:', final)
