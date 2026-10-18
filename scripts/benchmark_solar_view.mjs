// Synthetic canvas command equivalence + warmed CPU timing; no browser/GPU/FPS claim.
import fs from 'node:fs';
import vm from 'node:vm';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const [beforePath, afterPath, fixturePath] = process.argv.slice(2);
const fixtures = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

function controller(source) {
  let recording = false, commands = [], gradientId = 0, width = 640, height = 440;
  const record = (...values) => { if(recording) commands.push(values); };
  const target = {};
  for(const method of ['beginPath','closePath','moveTo','lineTo','arc','ellipse','rect',
                       'fill','stroke','save','restore','clip','translate','rotate',
                       'fillRect','fillText','setLineDash']) {
    target[method] = (...args) => record(method, ...args);
  }
  target.measureText = text => ({width: text.length * 7});
  for(const method of ['createRadialGradient','createLinearGradient']) {
    target[method] = (...args) => {
      const id = ++gradientId;
      record(method, id, ...args);
      return {id, addColorStop: (...args) => record('addColorStop', id, ...args)};
    };
  }
  const ctx = new Proxy(target, {
    set(obj, key, value) {record('set', key, value?.id ? {gradient: value.id} : value); obj[key] = value; return true;}
  });
  const nodes = new Map();
  const document = {querySelectorAll: () => [], getElementById: id => {
    if(!nodes.has(id)) nodes.set(id, {setAttribute: (key, value) => record('attribute', id, key, value)});
    return nodes.get(id);
  }};
  const sandbox = {
    document, playing: false, speed: 1, activeView: 'lab', settings: {},
    isScenario: () => true, escapeHTML: text => text, fmt: (v, d) => Number(v).toFixed(d),
    updatePlayButton: () => {}, canvasContext: id => ({ctx, w: id === 'solar-system-canvas' ? width : 160,
                                                          h: id === 'solar-system-canvas' ? height : 142}),
  };
  vm.createContext(sandbox);
  vm.runInContext(source + '\n;globalThis.controller = SolarView;', sandbox);
  const api = sandbox.controller;
  return {
    receive(payload) {sandbox.settings.scenario = payload.scene.focus.kind; api.receive(payload);},
    frame: f => api.seek(f),
    scope: value => api.setScope(value),
    resize(w, h) {width=w; height=h;},
    capture(action) {
      commands=[]; gradientId=0; recording=true;
      action(); recording=false;
      return createHash('sha256').update(JSON.stringify(commands)).digest('hex');
    }
  };
}

const sources = [beforePath, afterPath].map(path => fs.readFileSync(path, 'utf8'));
const results = {};
for(const name of ['blackhole', 'sirius', 'earth_rotation']) {
  const pair = sources.map(controller), payload = fixtures[name];
  const hashes=[];
  for(const test of pair) {
    test.receive(payload);
    hashes.push(test.capture(() => {
      for(const [w,h] of [[640,440],[340,380]]) {
        test.resize(w,h);
        for(const scope of ['all','inner']) {
          test.scope(scope);
          for(const time of [0,.23,.71,1]) test.frame(time);
        }
      }
      // Settings receive must discard geometry from a different trajectory.
      const alternate=structuredClone(payload);
      alternate.scene.bodies[0].trajectory[0][1]+=.01;
      test.receive(alternate); test.frame(0); test.receive(payload); test.frame(.4);
    }));
  }
  assert.equal(hashes[0], hashes[1], `${name}: canvas commands changed`);
  const timings = [[],[]];
  // Two rounds, each five batches after warmup. No command recording while timing.
  for(let repeat=0;repeat<2;repeat++) {
    for(let variant=0;variant<2;variant++) {
      const test=pair[variant]; test.resize(640,440); test.receive(payload); test.scope('all');
      for(let i=0;i<80;i++) test.frame(i/80);
      const batches=[];
      for(let batch=0;batch<5;batch++) {
        const start=performance.now();
        for(let i=0;i<160;i++) test.frame(i/160);
        batches.push((performance.now()-start)/160);
      }
      timings[variant].push({median_ms:[...batches].sort((a,b)=>a-b)[2], batches_ms:batches});
    }
  }
  results[name]={canvas_sha256:hashes[0], baseline:timings[0], candidate:timings[1]};
}
console.log(JSON.stringify({node:process.version, kind:'stub-canvas CPU, not browser FPS', results}));
