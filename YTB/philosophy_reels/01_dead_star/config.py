import os, shutil
# On Windows set these to your paths; on Linux/macOS the system ffmpeg is used.
WIN_FFMPEG = r'C:\Users\Legion\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
FFMPEG = WIN_FFMPEG if os.name == 'nt' else (shutil.which('ffmpeg') or 'ffmpeg')
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build')
VOICE = os.path.join(HERE, 'voice.mp3')          # drop the ElevenLabs MP3 here
FONT_CANDIDATES = [r'C:\Windows\Fonts\georgia.ttf', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
                   '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf']
FONT = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
