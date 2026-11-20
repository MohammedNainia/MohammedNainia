// The cast: one clay character system (haru3.js), each character is a few settings.
//   import {makeChar} from './characters.js';   const mum = makeChar('mum');   // or makeChar('mum', {hood: 0x333333}) to change one thing
// Settings (defaults = Haru): top hoodie|sweater|cardigan, bottom pants|skirt, hairStyle haru|bun|horseshoe|curlybob,
// legs (extra leg length), head (head size), height (overall), belly 0..1, age 0..1 (creases, stoop), glasses,
// colours: skin hood(top) pants(trousers or tights) skirt shoe hair brow button rim. detail: mesh detail (path tracing: .6)
import {makeHaru3} from './haru3.js';

export const CAST = {
  haru: {seed: 1},
  mum: {top: 'cardigan', hood: 0x5b4256, button: 0xd9cfb8, pants: 0x2f2e35, shoe: 0x2b2522, hair: 0x3b2a20, brow: 0x2b1d16,
        hairStyle: 'bun', legs: .27, head: 1.12, height: 1.14, skin: 0xdc9a74},
  grandma: {top: 'cardigan', hood: 0x7d8c6c, button: 0xe8dfc8, bottom: 'skirt', skirt: 0x4d4658, pants: 0xb88f78, shoe: 0x3a302a,
            hair: 0xc9c6c0, brow: 0xa8a49e, hairStyle: 'curlybob', age: .8, glasses: true, legs: .2, head: 1.16, height: 1.04, skin: 0xe0a382},
  grandpa: {top: 'sweater', hood: 0x56677a, pants: 0x6e6455, shoe: 0x3b2e26, hair: 0xb0aea8, brow: 0xc8c4bc, hairStyle: 'horseshoe',
            age: .9, glasses: true, belly: .6, legs: .24, head: 1.14, height: 1.12, skin: 0xd99a76},
  // Haru's friends
  mina: {top: 'tshirt', hood: 0x4f8fbf, stripes: 0xeae4d6, pants: 0x3d5a80, shoe: 0xd94a4a, hair: 0x4a2e1e, brow: 0x3a2418,
         hairStyle: 'ponytail', tie: 0xe8c64a, skin: 0xc98b65, seed: 3},
  leo: {top: 'sweater', hood: 0x3f7a4a, stripes: 0xe0b44a, bottom: 'shorts', pants: 0x6b5b4b, shoe: 0x2f3a4a, hair: 0x1e1a18, brow: 0x1e1a18,
        hairStyle: 'boyshort', skin: 0x8d5a3b, legs: .17, height: 1.04, seed: 5},
};
export const makeChar = (name, extra = {}) => makeHaru3(Object.assign({}, CAST[name] || {}, extra));
