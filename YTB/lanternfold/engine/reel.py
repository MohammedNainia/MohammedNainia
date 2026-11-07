"""Load a reel folder: reel.json + scene.py + derived timing."""
import os, json, importlib.util, numpy as np

class Reel:
    def __init__(self, d):
        self.dir = os.path.abspath(d)
        self.cfg = json.load(open(os.path.join(self.dir, 'reel.json'), encoding='utf-8'))
        self.slug = os.path.basename(self.dir)
        self.build = os.path.join(self.dir, 'build'); os.makedirs(self.build, exist_ok=True)
        self.timing_path = os.path.join(self.dir, 'timing.json')
    def path(self, *p): return os.path.join(self.dir, *p)
    @property
    def timing(self):
        return json.load(open(self.timing_path))
    def story(self, v):            # video seconds -> story seconds
        KV, KS = zip(*self.timing['knots']); return float(np.interp(v, KV, KS))
    def video(self, s):            # story seconds -> video seconds
        KV, KS = zip(*self.timing['knots']); return float(np.interp(s, KS, KV))
    def scene(self):
        spec = importlib.util.spec_from_file_location(f'scene_{self.slug}', self.path('scene.py'))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
