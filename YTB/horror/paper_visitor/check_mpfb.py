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
    cats = {}
    for r in [x for x in roots if x and os.path.isdir(x)]:
        for dp, dn, fn in os.walk(r):
            parts = [x.lower() for x in os.path.normpath(dp).split(os.sep)]
            for f in fn:
                if os.path.splitext(f)[1].lower() in ('.mhclo', '.mhskin', '.mhmat', '.mhpose', '.bvh', '.mhpxy', '.mheyebrows', '.mhmaterial'):
                    for c in ('hair', 'skins', 'clothes', 'eyebrows', 'eyelashes', 'eyes', 'teeth', 'poses', 'proxymeshes'):
                        if c in parts: cats[c] = cats.get(c, 0) + 1
    print('         data folders checked:', [x for x in roots if x])
    for r in [x for x in roots if x and os.path.isdir(x)]:
        print('         top folders in', r, ':', sorted(os.listdir(r))[:20])
    print('         assets by type:', cats or 'none')
    for c, label in (('hair', 'hair'), ('skins', 'skin'), ('clothes', 'clothes'), ('eyebrows', 'eyebrows'), ('eyelashes', 'eyelashes')):
        print(('OK' if cats.get(c) else 'MISSING').ljust(9), f'{label} assets ({cats.get(c, 0)} files)')
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    gpus = [d.name for d in prefs.devices if d.type == 'OPTIX']
    print(('OK       GPU (OptiX): ' + ', '.join(gpus)) if gpus else 'MISSING  no OptiX GPU visible')
except Exception as e: print('         GPU check failed:', e)
print('=================================\n')
