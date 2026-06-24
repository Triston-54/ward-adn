import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import vm from 'vm';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/content/microbiology.json'), 'utf8'));

console.log('=== JSON field check ===');
for (const t of data.microbe_classification) {
  const missing = ['type', 'structure', 'treatment', 'examples', 'clinical_why'].filter((k) => !t[k]);
  console.log(`${t.type}: ${missing.length ? 'MISSING ' + missing.join(', ') : 'OK'}`);
}

const ctx = {
  console,
  URL,
  localStorage: { _d: {}, getItem(k) { return this._d[k] ?? null; }, setItem(k, v) { this._d[k] = v; } },
  location: { origin: 'http://localhost' },
  Response: class { constructor(b) { this._b = b; this.ok = true; } async json() { return JSON.parse(this._b); } },
  fetch: async (url) => {
    const m = url.match(/\/data\/content\/(.+)/);
    const text = fs.readFileSync(path.join(ROOT, 'data/content', m[1]), 'utf8');
    return { ok: true, json: async () => JSON.parse(text) };
  },
};
ctx.window = ctx;
ctx.globalThis = ctx;
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'static/js/data-api.js'), 'utf8'), ctx);

const res = await ctx.fetch('/api/microbiology/classification');
const api = await res.json();
console.log('\n=== API classification check ===');
for (const t of api.types) {
  console.log(`${t.type}: treatment=${Boolean(t.treatment)}, structure=${Boolean(t.structure)}, clinical_why=${Boolean(t.clinical_why)}`);
}