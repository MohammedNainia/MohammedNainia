"""Check that MPFB2 (MakeHuman for Blender) is installed, enabled and has its asset pack.
    blender -b -P check_mpfb.py
Prints one OK/MISSING line per item."""
import bpy, addon_utils, os

print('\n===== PaperLit: MPFB2 check =====')
print('Blender', bpy.app.version_string)
mods = [m for m in addon_utils.modules() if 'mpfb' in m.__name__.lower()]
if not mods:
    print('MISSING  MPFB2 is not installed (Edit > Preferences > Get Extensions > search MPFB > Install)')
else:
    m = mods[0]; name = m.__name__
    enabled, loaded = addon_utils.check(name)
    print('OK       installed as', name, '| version', '.'.join(map(str, m.bl_info.get('version', ()))))
    print(('OK       enabled' if enabled else 'MISSING  installed but NOT enabled (tick it in Preferences > Add-ons)'))
    if not enabled:
        try: addon_utils.enable(name, default_set=True); print('         enabled it now for this check')
        except Exception as e: print('         could not enable:', e)
    # find the asset pack: MPFB keeps user data in the extension's user folder
    roots = []
    try: roots.append(bpy.utils.extension_path_user(name.split('.')[-1] if name.startswith('bl_ext') else name, path='', create=False))
    except Exception: pass
    try:
        import importlib; ls = importlib.import_module(name + '.services.locationservice').LocationService
        for fn in ('get_user_data', 'get_user_home', 'get_mpfb_data'):
            try: roots.append(getattr(ls, fn)())
            except Exception: pass
    except Exception as e: print('         (location service not reachable:', e, ')')
    found = {}
    for r in [x for x in roots if x and os.path.isdir(x)]:
        for dp, dn, fn in os.walk(r):
            for f in fn:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.mhclo', '.mhskin', '.mhmat', '.mhpxy', '.mhtarget', '.target', '.gz'):
                    k = os.path.basename(dp); found[k] = found.get(k, 0) + 1
    print('         data folders checked:', [x for x in roots if x])
    if found:
        print('OK       assets found:', ', '.join(f'{k} ({v})' for k, v in sorted(found.items())[:12]))
        hair = any('hair' in k for k in found); skins = any('skin' in k for k in found); clothes = any('cloth' in k for k in found)
        print(('OK' if hair else 'MISSING').ljust(9), 'hair assets'); print(('OK' if skins else 'MISSING').ljust(9), 'skin assets'); print(('OK' if clothes else 'MISSING').ljust(9), 'clothes assets')
    else:
        print('MISSING  no asset pack found: in Blender, open the MPFB panel (N key in the 3D view) > Apps/Assets > Load pack from zip, using the free "system assets" pack')
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    gpus = [d.name for d in prefs.devices if d.type == 'OPTIX']
    print(('OK       GPU (OptiX): ' + ', '.join(gpus)) if gpus else 'MISSING  no OptiX GPU visible')
except Exception as e: print('         GPU check failed:', e)
print('=================================\n')
