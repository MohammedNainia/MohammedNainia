# The clay library

Generated clay characters and props, made once with Artlist and reused in every reel.
`index.json` lists every item with its file, real-world size (metres; Haru is 1.26 m), description and how it was made.
`generations.txt` keeps the Artlist generation ids, so any item can be downloaded again.

## Using it in a scene

```js
import {lib} from './library.js';
const haru = await lib.char('haru');      // a puppet: same joints as makePerson, so pose(), walk(), look(), the scenes' reset() all work
haru.expr('scared'); haru.mouth('open', .6); haru.eyes('closed');   // the drawn 2D face
scene.add(haru.root);
const chair = await lib.prop('chair');    // a Group standing on y = 0, centred, at its real size
const tree = await lib.prop('tree', {height: 7});
```

Characters: haru, mum, dad, woman_red, grandma, boy, girl.
Props: kitchen_table, chair, armchair, bed, wardrobe, stove, fridge, floor_lamp, bookshelf, school_desk, car, street_lamp, bench, bin, tree, gravestone.
See them: `scenes/lib_view.html` (`?show=chars`, `?show=props&grid=1`, `?char=mum`), and `YTB/channel_art/library_cast.png`, `library_props.png`.

## Adding a character (about 430 credits)

1. Artlist image (Nano Banana 2, 130): edit from Haru's blank-face image (generation `01a20472-a03b-705e-beec-2791c8c5c082`) with a prompt like
   "A new character in exactly the same clay stop-motion style, studio lighting and plain light grey background as the reference figure: <who and what they wear>.
   Full body, front view, standing straight, arms hanging slightly away from the body. Smooth blank face with only a small round nose: no eyes, no eyebrows, no mouth."
2. 3D (Hyper3D Rodin v2.5 Fast, image-to-3D, 300) from that image.
3. `python tools/glb_slim.py raw.glb data/lib/chars/<name>.glb` then `python tools/glb_autorig.py data/lib/chars/<name>.glb` (`--child` for a small child in a skirt;
   `--rot 90` if it came out facing sideways). Long skirts and coats are detected and the hips placed by proportion.
4. Add it to `index.json` (`file`, `desc`, `height`, `made`) and check it in `lib_view.html?char=<name>`.

## Adding a prop (300 credits)

Text-to-3D, Hyper3D Rodin v2.5 Fast, prompt: "<the object>, handmade plasticine clay stop-motion miniature, matte clay surface with fingerprints, single object, no base, no background".
Then `python tools/glb_slim.py raw.glb data/lib/props/<name>.glb --max 1024` and an `index.json` entry with `height` (or `length` for long things), `desc`, `tags`.

## Known limits

- Arms fused to the body in the generated mesh: big arm moves (arms fully up, reaching far out) stretch the side of the top a little.
- Long coats and skirts follow the hips; in strong poses they can still crease or split slightly.
- Hair is part of the head (no sway yet).
