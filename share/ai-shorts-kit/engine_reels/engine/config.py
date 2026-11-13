import os, shutil
def _ffmpeg():                                    # FFMPEG env var > ffmpeg on PATH > the copy bundled with imageio-ffmpeg
    if os.environ.get('FFMPEG'): return os.environ['FFMPEG']
    if shutil.which('ffmpeg'): return shutil.which('ffmpeg')
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: return 'ffmpeg'
FFMPEG = _ffmpeg()
FFPROBE = os.environ.get('FFPROBE') or shutil.which('ffprobe') or os.path.join(os.path.dirname(FFMPEG), 'ffprobe' + ('.exe' if os.name == 'nt' else ''))
FPS = 30
SR = 44100
FONT = next((f for f in [r'C:\Windows\Fonts\georgia.ttf', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
                         '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'] if os.path.exists(f)), None)
