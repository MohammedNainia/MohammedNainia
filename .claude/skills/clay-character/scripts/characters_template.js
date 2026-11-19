// The cast: one clay character system (haru3.js), each character is a few settings.
//   import {makeChar} from './characters.js';   const mum = makeChar('mum');   // or makeChar('mum', {hood: 0x333333}) to change one thing
// Settings (defaults = Haru): top hoodie|sweater|cardigan, bottom pants|skirt, hairStyle haru|bun|horseshoe|curlybob,
// legs (extra leg length), head (head size), height (overall), belly 0..1, age 0..1 (creases, stoop), glasses,
// colours: skin hood(top) pants(trousers or tights) skirt shoe hair brow button rim. detail: mesh detail (path tracing: .6)
import {makeHaru3} from './haru3.js';

export const CAST = {
  haru: {},
  mum: {top: 'cardigan', hood: 0x5b4256, button: 0xd9cfb8, pants: 0x2f2e35, shoe: 0x2b2522, hair: 0x3b2a20, brow: 0x2b1d16,
        hairStyle: 'bun', legs: .27, head: 1.12, height: 1.14, skin: 0xdc9a74},
  grandma: {top: 'cardigan', hood: 0x7d8c6c, button: 0xe8dfc8, bottom: 'skirt', skirt: 0x4d4658, pants: 0xb88f78, shoe: 0x3a302a,
            hair: 0xc9c6c0, brow: 0xa8a49e, hairStyle: 'curlybob', age: .8, glasses: true, legs: .2, head: 1.16, height: 1.04, skin: 0xe0a382},
  grandpa: {top: 'sweater', hood: 0x56677a, pants: 0x6e6455, shoe: 0x3b2e26, hair: 0xb0aea8, brow: 0xc8c4bc, hairStyle: 'horseshoe',
            age: .9, glasses: true, belly: .6, legs: .24, head: 1.14, height: 1.12, skin: 0xd99a76},
};
export const makeChar = (name, extra = {}) => makeHaru3(Object.assign({}, CAST[name] || {}, extra));
