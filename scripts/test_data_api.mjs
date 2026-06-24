/**
 * Smoke test for static/js/data-api.js — run: node scripts/test_data_api.mjs
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import vm from 'vm';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const contentCache = new Map();

const context = {
  console,
  URL,
  localStorage: {
    _data: {},
    getItem(k) { return this._data[k] ?? null; },
    setItem(k, v) { this._data[k] = v; },
  },
  location: { origin: 'http://127.0.0.1:8777', pathname: '/modules/terminology.html' },
  Response: class Response {
    constructor(body, init = {}) {
      this._body = body;
      this.status = init.status ?? 200;
      this.ok = this.status >= 200 && this.status < 300;
      this.headers = new Map(Object.entries(init.headers || {}));
    }
    async json() { return JSON.parse(this._body); }
    async text() { return this._body; }
  },
  fetch: async (url) => {
    const u = new URL(url, 'http://127.0.0.1:8777');
    const filePath = path.join(ROOT, u.pathname.replace(/^\//, '').replace(/\//g, path.sep));
    if (!fs.existsSync(filePath)) {
      return { ok: false, status: 404, json: async () => ({}), text: async () => '' };
    }
    const text = fs.readFileSync(filePath, 'utf8');
    return { ok: true, status: 200, json: async () => JSON.parse(text), text: async () => text };
  },
};

context.window = context;
context.globalThis = context;

const code = fs.readFileSync(path.join(ROOT, 'static/js/data-api.js'), 'utf8');
vm.runInNewContext(code, context);

const { WardData } = context;

async function testDirect() {
  const terms = await WardData.Terminology.getAllTerms();
  console.log('Direct getAllTerms:', terms.length);
  try {
    const seq = await WardData.Assessment.headToToe();
    console.log('Direct headToToe:', seq.length);
  } catch (e) {
    console.log('Direct headToToe: FAIL (arrow this bug)', e.message);
  }
  const micro = await WardData.Microbiology.flashcards(5);
  console.log('Direct micro flashcards:', micro.count);
}

async function testFetch(pathname) {
  const res = await context.fetch(pathname);
  if (!res?.json) {
    console.error('Bad response for', pathname, res);
    return { ok: false, data: {} };
  }
  const data = await res.json();
  if (data.error) console.error('API error for', pathname, data.error);
  return { ok: res.ok, data };
}

async function testIntercepted() {
  const terms = await testFetch('/api/terminology/terms?limit=60');
  console.log('Intercepted /api/terminology/terms total:', terms.data.total, 'terms:', terms.data.terms?.length);

  const search = await testFetch('/api/terminology/terms?q=cardio&limit=10');
  console.log('Intercepted search cardio total:', search.data.total, '(query bug if equals full count)');

  const fc = await testFetch('/api/terminology/flashcards?count=5&due_only=true');
  console.log('Intercepted flashcards count:', fc.data.count, 'stats total:', fc.data.stats?.total_cards);

  const ht = await testFetch('/api/assessment/head-to-toe');
  console.log('Intercepted head-to-toe steps:', ht.data.sequence?.length);

  const content = await testFetch('/api/assessment/content');
  console.log('Intercepted assessment content skills:', content.data.skills?.length);

  const micro = await testFetch('/api/microbiology/flashcards?count=8');
  console.log('Intercepted micro flashcards:', micro.data.count);

  const nclex = await testFetch('/api/nclex-prep/content');
  console.log('Intercepted nclex categories:', nclex.data.categories?.length ?? Object.keys(nclex.data).length);
}

async function main() {
  await testDirect();
  await testIntercepted();
}

main().catch((e) => {
  console.error('FAIL', e);
  process.exit(1);
});