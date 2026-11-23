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
Props (house, school, street): kitchen_table, chair, armchair, bed, wardrobe, stove, fridge, floor_lamp, bookshelf, school_desk, car, street_lamp, bench, bin, tree, gravestone.
Buildings: house_family, house_old, cottage, hospital, church, crypt, gas_station.
Hospital: hospital_bed, drip_stand, wheelchair, screen.  Church: pew, altar, candle_stand.  Cemetery: fence, cemetery_gate, cross_grave, angel, dead_tree.
Desert: car_wreck, cow_skull, rocks.  Playground: swings, slide, roundabout.

## Movement (scenes/moves.js)

```js
import {relaxed, idle, travel, travelTime} from './moves.js';
reset(P); idle(P, t);                    // the default stance: relaxed (weight on one leg, soft elbows, shoulders down) and breathing
const path = [{from: [-3, 0], heading: Math.PI / 2}, {idle: 1.5}, {walk: [2, 0]}, {turn: -Math.PI / 2}, {look: 'L'}, {run: [5, 1]}];
reset(P); travel(P, t, path);            // walks / runs along it with the feet planted (the speed comes from the puppet's own stride), turns on the spot with little steps
```
Headings: 0 faces +z (the camera), PI/2 faces +x. See it: `scenes/haru_lab.html?mode=move` (and `?mode=face` for the face and stance from all sides).

## Sitting and lying: contact (scenes/contact.js), the rule

Never place a seated or lying character by hand (no guessed heights like `BED_TOP - .38`). Use the contact helpers: they measure the prop's real
shape (a slab map from rays, once per prop) and the character's real skinned vertices, so she rests ON the seat or mattress and never sinks in.
```js
import {sitOn, lieOn, sitUpIn, settleOn, turnToward, sinkCheck} from './contact.js';
turnToward(chair, V(-1.45, 0, -2.4));   // turn the chair to face something (its front is measured: the side away from the backrest)
sitOn(haru, chair); idle(haru, q, .2);  // sitChair pose, bottom on the seat, back in front of the backrest; set arms after
lieOn(haru, bed);                       // on her back along the bed, head on the pillow end (measured), tilted up as the pillow needs
sitUpIn(gran, bed, {fix: P => {...}});  // sitting up against the head section, facing the foot
```
Beds: the pillow end is found from the model; lay the bed lengthwise in the room and let `seatOf(bed).head` tell you which way it points.
Before every render: `node check_contact.js --scene <name>` sweeps the reel and exits with an error if anyone is more than 4 cm inside
any furniture (the scene exposes `window.contactAt(t)`, see night_count.html). Test a prop and a character alone: `scenes/contact_lab.html?char=haru&prop=chair&do=sit`.

## Masks and anything on a face
Build them from the face rig (`P.rigFace`: eyes, mouth, face box in model units; `P.rigPt` turns them into the puppet's units), keep the top edge
under the eye centre minus 1.7 eye radii (the widest drawn eye reaches about 1.05), and assert it in code (night_count.html does).

## Whole places (sets)

`scenes/lib_sets.js` builds finished, lit places from these models plus our own ground, sky, fog and lights:

```js
import {buildSet} from './lib_sets.js';
const S = await buildSet('cemetery', scene);        // also: street, hospital, ward, church, church_in, desert ({time: 'night'} or dusk), playground, forest
haru.root.position.copy(S.spots.haru);              // named spots: where to stand (cemetery: gate, angel, crypt; ward: bed; church_in: altar ...)
const sh = S.shots.wide; cam.position.copy(sh.pos); cam.lookAt(sh.look); cam.fov = sh.fov;   // named cameras; every set has 'wide' and 'haru'
S.update(t);                                         // each frame: failing lamps flicker, candles waver, the roundabout turns
```

Several sets can sit in one scene (`{at: [100, 0, 0]}`); `S.apply()` restores a set's sky and fog after a cut. Each set adds a soft fill light on its
haru spot so a face reads in the dark (`{fill: 0}` turns it off). See every set: `scenes/set_view.html?set=church_in` (`&time=night`, `&cam=x,y,z,lx,ly,lz,fov`),
and `YTB/channel_art/library_sets.png`.
Everything faces +z (the camera looks down -z), lengths are in metres.
See them: `scenes/lib_view.html` (`?show=chars`, `?show=props&grid=1`, `?char=mum`), and `YTB/channel_art/library_cast.png`, `library_props.png`.

## Adding a character (about 430 credits)

1. Artlist image (Nano Banana 2, 130): edit from Haru's blank-face image (generation `01a20472-a03b-705e-beec-2791c8c5c082`) with a prompt like
   "A new character in exactly the same clay stop-motion style, studio lighting and plain light grey background as the reference figure: <who and what they wear>.
   Full body, front view, standing straight, arms hanging slightly away from the body. Smooth blank face with only a small round nose: no eyes, no eyebrows, no mouth."
2. 3D (Hyper3D Rodin v2.5 Fast, image-to-3D, 300) from that image.
3. `python tools/glb_slim.py raw.glb data/lib/chars/<name>.glb` then `python tools/glb_autorig.py data/lib/chars/<name>.glb` (`--child` for a small child in a skirt;
   `--rot 90` if it came out facing sideways). Long skirts and coats are detected and the hips placed by proportion.
   If the face bulges forward (a muzzle), `python tools/glb_face_flatten.py data/lib/chars/<name>.glb` flattens it and shrinks the nose (`--dry` to see the profile first).
4. Add it to `index.json` (`file`, `desc`, `height`, `made`) and check it in `lib_view.html?char=<name>`.

## Adding a prop (300 credits)

Text-to-3D, Hyper3D Rodin v2.5 Fast, prompt: "<the object>, handmade plasticine clay stop-motion miniature, matte clay surface with fingerprints, single object, no base, no background".
Then `python tools/glb_slim.py raw.glb data/lib/props/<name>.glb --max 1024` and an `index.json` entry with `height` (or `length` for long things), `desc`, `tags`.

## Known limits

- Arms fused to the body in the generated mesh: big arm moves (arms fully up, reaching far out) stretch the side of the top a little.
- Long coats and skirts follow the hips; in strong poses they can still crease or split slightly.
- Hair is part of the head (no sway yet).
- Buildings are outsides only (no rooms inside): rooms are built in code, as `ward` and `church_in` do.
