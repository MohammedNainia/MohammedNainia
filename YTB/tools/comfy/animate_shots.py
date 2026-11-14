"""Animate still images into short clips with Wan 2.2 image-to-video in your local ComfyUI (0 credits).
ComfyUI must be running (default http://127.0.0.1:8188) with the files from get_wan22.bat.

    py animate_shots.py shots.json                 every shot in the list
    py animate_shots.py shots.json --only t4       one shot (test first!)
    py animate_shots.py shots.json --fast          3 s clips instead of 5 s, for testing

shots.json = [{"id": "t4", "image": "stills/t4_all_d.png", "prompt": "...", "seconds": 5}, ...]
Output: clips/<id>.mp4 (480x848, 16 fps) next to shots.json. Then upscale with your upscaler and
smooth to 30 fps:  ffmpeg -i in.mp4 -vf "minterpolate=fps=30:mi_mode=mci" out.mp4  (or RIFE if you have it)."""
import json, os, sys, time, uuid, urllib.request, urllib.parse, subprocess, random, shutil

URL = os.environ.get('COMFY_URL', 'http://127.0.0.1:8188')
NEG = ('blurry, jitter, flicker, morphing, deformed, extra limbs, extra people, text, subtitles, watermark, '
       'camera shake, fast motion, cartoonish exaggeration, low quality, static image')

def api(path, data=None, raw=False):
    req = urllib.request.Request(URL + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r: return r.read() if raw else json.load(r)

def upload(path):
    bnd = uuid.uuid4().hex; name = os.path.basename(path)
    body = (f'--{bnd}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\nContent-Type: image/png\r\n\r\n').encode() \
        + open(path, 'rb').read() + f'\r\n--{bnd}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n--{bnd}--\r\n'.encode()
    req = urllib.request.Request(URL + '/upload/image', data=body, headers={'Content-Type': f'multipart/form-data; boundary={bnd}'})
    with urllib.request.urlopen(req, timeout=120) as r: return json.load(r)['name']

def graph(image_name, prompt, frames, w, h, seed, prefix):
    """Wan 2.2 A14B i2v, two experts (high noise steps 0-2, low noise 2-4) with the lightx2v 4-step LoRAs."""
    return {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors', 'weight_dtype': 'default'}},
        '2': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors', 'weight_dtype': 'default'}},
        '3': {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': ['1', 0], 'lora_name': 'wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors', 'strength_model': 1.0}},
        '4': {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': ['2', 0], 'lora_name': 'wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors', 'strength_model': 1.0}},
        '5': {'class_type': 'ModelSamplingSD3', 'inputs': {'model': ['3', 0], 'shift': 5.0}},
        '6': {'class_type': 'ModelSamplingSD3', 'inputs': {'model': ['4', 0], 'shift': 5.0}},
        '7': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'umt5_xxl_fp8_e4m3fn_scaled.safetensors', 'type': 'wan', 'device': 'default'}},
        '8': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['7', 0], 'text': prompt}},
        '9': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['7', 0], 'text': NEG}},
        '10': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'wan_2.1_vae.safetensors'}},
        '11': {'class_type': 'LoadImage', 'inputs': {'image': image_name}},
        '12': {'class_type': 'WanImageToVideo', 'inputs': {'positive': ['8', 0], 'negative': ['9', 0], 'vae': ['10', 0], 'start_image': ['11', 0],
                                                          'width': w, 'height': h, 'length': frames, 'batch_size': 1}},
        '13': {'class_type': 'KSamplerAdvanced', 'inputs': {'model': ['5', 0], 'add_noise': 'enable', 'noise_seed': seed, 'steps': 4, 'cfg': 1.0,
                                                           'sampler_name': 'euler', 'scheduler': 'simple', 'positive': ['12', 0], 'negative': ['12', 1],
                                                           'latent_image': ['12', 2], 'start_at_step': 0, 'end_at_step': 2, 'return_with_leftover_noise': 'enable'}},
        '14': {'class_type': 'KSamplerAdvanced', 'inputs': {'model': ['6', 0], 'add_noise': 'disable', 'noise_seed': seed, 'steps': 4, 'cfg': 1.0,
                                                           'sampler_name': 'euler', 'scheduler': 'simple', 'positive': ['12', 0], 'negative': ['12', 1],
                                                           'latent_image': ['13', 0], 'start_at_step': 2, 'end_at_step': 10000, 'return_with_leftover_noise': 'disable'}},
        '15': {'class_type': 'VAEDecode', 'inputs': {'samples': ['14', 0], 'vae': ['10', 0]}},
        '16': {'class_type': 'SaveImage', 'inputs': {'images': ['15', 0], 'filename_prefix': prefix}},
    }

def run(shot, root, fast):
    from PIL import Image
    img = os.path.join(root, shot['image']); iw, ih = Image.open(img).size
    w, h = (480, 848) if ih >= iw else (848, 480)                       # Wan likes multiples of 16
    secs = 3 if fast else shot.get('seconds', 5); frames = 16 * secs + 1
    name = upload(img); prefix = f"wan_{shot['id']}_{uuid.uuid4().hex[:6]}"
    pid = api('/prompt', {'prompt': graph(name, shot['prompt'], frames, w, h, shot.get('seed', random.randint(1, 2**31)), prefix)})['prompt_id']
    t0 = time.time(); print(f"  {shot['id']}: queued ({frames} frames, {w}x{h})", flush=True)
    while True:
        time.sleep(3); hist = api(f'/history/{pid}')
        if pid in hist:
            st = hist[pid].get('status', {})
            if st.get('status_str') == 'error': sys.exit(f"  {shot['id']}: ComfyUI error, see the ComfyUI window: {st.get('messages', '')[-1:]}")
            outs = [im for o in hist[pid]['outputs'].values() for im in o.get('images', [])]
            if outs: break
    tmp = os.path.join(root, 'clips', '_frames_' + shot['id']); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for k, im in enumerate(sorted(outs, key=lambda x: x['filename'])):
        q = urllib.parse.urlencode({'filename': im['filename'], 'subfolder': im['subfolder'], 'type': im['type']})
        open(os.path.join(tmp, f'{k:04d}.png'), 'wb').write(api('/view?' + q, raw=True))
    out = os.path.join(root, 'clips', shot['id'] + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '16', '-i', os.path.join(tmp, '%04d.png'), '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], check=True)
    shutil.rmtree(tmp); print(f"  {shot['id']}: done in {time.time() - t0:.0f} s -> {out}", flush=True)

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    path = sys.argv[1]; root = os.path.dirname(os.path.abspath(path)); shots = json.load(open(path))
    if '--only' in sys.argv: shots = [s for s in shots if s['id'] == sys.argv[sys.argv.index('--only') + 1]]
    os.makedirs(os.path.join(root, 'clips'), exist_ok=True)
    try: api('/system_stats')
    except Exception: sys.exit(f'ComfyUI is not reachable at {URL}. Start ComfyUI first.')
    for s in shots: run(s, root, '--fast' in sys.argv)
