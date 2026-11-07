import os, shutil
WIN_FFMPEG = r'C:\Users\Legion\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
FFMPEG = WIN_FFMPEG if os.name == 'nt' else (shutil.which('ffmpeg') or 'ffmpeg')
FFPROBE = os.path.join(os.path.dirname(FFMPEG), 'ffprobe.exe') if os.name == 'nt' else (shutil.which('ffprobe') or 'ffprobe')
FPS = 30
SR = 44100
FONT = next((f for f in [r'C:\Windows\Fonts\georgia.ttf', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
                         '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'] if os.path.exists(f)), None)
