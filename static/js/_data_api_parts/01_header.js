/**
 * The Ward — Client-side Data API
 * Loads JSON from /data/content/ and intercepts /api/* fetch calls.
 */
(function (global) {
  'use strict';

  const MODULES = {
    terminology: { name: 'Medical Terminology', total: 220 },
    microbiology: { name: 'Microbiology', total: 47 },
    dosage: { name: 'NURS 145 — Drug & Dosage', total: 53 },
    assessment: { name: 'NURS 146 — Health Assessment', total: 132 },
    mental_health: { name: 'NURS 147 — Mental Health', total: 55 },
    pathophysiology: { name: 'Pathophysiology', total: 76 },
    maternal_child: { name: 'NURS 148 — Maternal-Child', total: 115 },
  };

  const SRS_INTERVALS = [1, 3, 7, 14, 30, 60];
  const LS_CUSTOM_TERMS = 'ward_custom_terms';
  const LS_DOSAGE_FAVS = 'ward_dosage_favorites';
  const LS_TERMINOLOGY_SRS = 'ward_terminology_srs';
  const LS_ASSESSMENT_SRS = 'ward_assessment_srs';
  const LS_AUDIT = 'ward_audit_records';
  const TERMINOLOGY_DEFAULT_SOURCE = { title: 'Medical Terminology for Health Professions', citation: 'Ehrlich & Schroeder, 8th Ed.', verified_date: '2026-06' };

  const REFERENCE_TYPE_STYLES = { Textbook: 'textbook', 'OER Textbook': 'oer', 'Exam Blueprint': 'nclex', 'Clinical Guideline': 'guideline', 'Program Curriculum': 'curriculum' };
  const MODULE_SOURCE_KEYS = {
    terminology: ['terminology', 'nclex', 'new_river_ctc'], microbiology: ['microbiology', 'cdc_infection', 'nclex'],
    dosage: ['dosage', 'nclex', 'new_river_ctc'], assessment: ['assessment', 'nclex', 'new_river_ctc'],
    mental_health: ['mental_health', 'nclex', 'new_river_ctc'], maternal_child: ['maternal_child', 'nclex', 'new_river_ctc'],
    pathophysiology: ['assessment', 'nclex', 'new_river_ctc'], general: ['nclex', 'new_river_ctc'],
  };
  const MODULE_VERIFY_CONTEXT = {
    terminology: { summary: 'Terms built from verified prefix/root/suffix components.', why_verify: 'Accurate terminology prevents documentation errors.', primary_type: 'Textbook' },
    microbiology: { summary: 'Pathogen profiles and infection chain from Open RN OER and CDC.', why_verify: 'Infection control must match current standards.', primary_type: 'OER Textbook' },
    dosage: { summary: 'Calculations aligned with Ogden & Fluharty and NCLEX.', why_verify: 'Dosage errors are a leading cause of preventable harm.', primary_type: 'Textbook' },
    assessment: { summary: 'Head-to-toe sequence and red flags from Open RN Nursing Skills.', why_verify: 'Assessment drives clinical judgment.', primary_type: 'OER Textbook' },
    mental_health: { summary: 'Therapeutic communication and safety from Open RN OER.', why_verify: 'Mental health content must reflect current screening standards.', primary_type: 'OER Textbook' },
    maternal_child: { summary: 'OB/Peds content from Open RN OER.', why_verify: 'Maternal-child safety requires evidence-based protocols.', primary_type: 'OER Textbook' },
    pathophysiology: { summary: 'Disease processes aligned with Open RN and NCLEX.', why_verify: 'Pathophysiology must connect cellular disruption to bedside care.', primary_type: 'OER Textbook' },
    general: { summary: 'All Ward content verified against nursing education standards.', why_verify: 'Teaching-first content requires traceable sources.', primary_type: 'Exam Blueprint' },
  };
  const NCLEX_RELEVANCE = {
    terminology: 'Supports NCLEX Safe and Effective Care Environment and Health Promotion.',
    microbiology: 'Aligns with NCLEX Patient Safety and Infection Control.',
    dosage: 'High-stakes NCLEX competency — dimensional analysis and IV rates.',
    assessment: 'Maps to NCLEX Physiological Integrity and clinical judgment.',
    mental_health: 'Aligns with NCLEX Psychosocial Integrity.',
    maternal_child: 'Aligns with NCLEX Health Promotion and Physiological Integrity.',
    general: 'All modules align with the NCLEX-RN Test Plan (NCSBN).',
    nclex: 'Primary reference for NCLEX category alignment.', cdc_infection: 'CDC guidelines for infection control items.', new_river_ctc: 'New River CTC ADN curriculum alignment.',
  };
  const AUDIT_MODULE_LABELS = { terminology: 'Medical Terminology', microbiology: 'Microbiology', dosage: 'NURS 145 — Dosage', assessment: 'NURS 146 — Health Assessment', mental_health: 'NURS 147 — Mental Health', pathophysiology: 'Pathophysiology', maternal_child: 'NURS 148 — Maternal-Child' };

  const _contentCache = new Map();
  let _nativeFetch = global.fetch.bind(global);

  async function loadContent(filename) {
    if (_contentCache.has(filename)) return _contentCache.get(filename);
    const res = await _nativeFetch(`/data/content/${filename}`);
    if (!res.ok) { _contentCache.set(filename, {}); return {}; }
    const data = await res.json();
    _contentCache.set(filename, data);
    return data;
  }
  function preloadContent(filenames) { return Promise.all(filenames.map(loadContent)); }

  function safeSample(pool, count) {
    if (!pool?.length || count <= 0) return [];
    const copy = [...pool]; shuffleArray(copy);
    return copy.slice(0, Math.min(count, copy.length));
  }
  function shuffleArray(arr) { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; }
  function jsonResponse(data, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }
  function textResponse(text, ct = 'text/html') { return new Response(text, { status: 200, headers: { 'Content-Type': ct } }); }
  function notFound(msg = 'Not found') { return jsonResponse({ error: msg }, 404); }
  function fmtG(n) { const num = Number(n); return Number.isInteger(num) ? String(num) : parseFloat(num.toPrecision(12)).toString(); }
  function escHtml(t) { return String(t ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function todayISO() { return new Date().toISOString().slice(0, 10); }
  function addDaysISO(days) { const d = new Date(); d.setDate(d.getDate() + days); return d.toISOString().slice(0, 10); }
  function shuffleMcOptions(options, correctIndex) {
    const indexed = options.map((opt, i) => [i, opt]); shuffleArray(indexed);
    return { options: indexed.map(([, o]) => o), correct_index: indexed.findIndex(([o]) => o === correctIndex) };
  }
  function lsGet(key, fb) { try { const r = localStorage.getItem(key); return r ? JSON.parse(r) : fb; } catch { return fb; } }
  function lsSet(key, v) { localStorage.setItem(key, JSON.stringify(v)); }
  function nextId(items) { return (items.length ? Math.max(...items.map((x) => x.id || 0)) : 0) + 1; }
  function parseBody(init) { if (!init?.body) return null; try { return typeof init.body === 'string' ? JSON.parse(init.body) : init.body; } catch { return null; } }
  function qInt(p, k, fb) { const v = p.get(k); return v != null && v !== '' ? parseInt(v, 10) : fb; }
  function qBool(p, k, fb = false) { const v = p.get(k); return v == null ? fb : v === 'true' || v === '1'; }
  function qStr(p, k) { return p.get(k) || null; }
  function noopProgress() { return { percentage: 0, items_completed: 0 }; }
  function noopStats(mid, extra = {}) { return { module_id: mid, percentage: 0, items_completed: 0, items_total: MODULES[mid]?.total || 0, streak_days: 0, last_practiced: null, ...extra }; }

  async function getSource(moduleKey) {
    const sources = await loadContent('sources.json'); const s = sources[moduleKey] || {};
    return { title: s.title || moduleKey, url: s.url || null, citation: s.citation || '', verified_date: s.verified_date || '2026-06' };
  }
  function formatCitation(s) { const c = (s.citation || '').trim(); const t = (s.title || '').trim(); const v = s.verified_date || '2026-06'; return c ? `${c} (verified ${v})` : t ? `${t} (verified ${v})` : `Verified source (${v})`; }
  function enrichSource(key, raw) {
    const rt = raw.reference_type || 'Reference';
    return { id: key, title: raw.title || 'Unknown', url: raw.url || null, citation: raw.citation || '', verified_date: raw.verified_date || '2026-06', reference_type: rt, reference_type_style: REFERENCE_TYPE_STYLES[rt] || 'reference', rationale: raw.rationale || '', formatted_citation: formatCitation(raw), nclex_relevance: NCLEX_RELEVANCE[key] || NCLEX_RELEVANCE.general };
  }
  async function getModuleSources(moduleId) {
    const registry = await loadContent('sources.json'); const keys = MODULE_SOURCE_KEYS[moduleId] || MODULE_SOURCE_KEYS.general;
    const sources = keys.filter((k) => registry[k]).map((k) => enrichSource(k, registry[k]));
    return { module_id: moduleId, sources, nclex_relevance: NCLEX_RELEVANCE[moduleId] || NCLEX_RELEVANCE.general, verify_context: MODULE_VERIFY_CONTEXT[moduleId] || MODULE_VERIFY_CONTEXT.general, count: sources.length };
  }

  function getSrsState(store, cardKey) {
    const all = lsGet(store, {}); return all[cardKey] || { ease_factor: 2.5, interval_days: 0, repetitions: 0, next_review: todayISO(), correct_count: 0, incorrect_count: 0 };
  }
  function recordSrsReview(store, cardKey, quality) {
    const all = lsGet(store, {}); const state = { ...getSrsState(store, cardKey) };
    if (quality === 0) { state.repetitions = 0; state.interval_days = 1; state.incorrect_count++; state.ease_factor = Math.max(1.3, state.ease_factor - 0.2); }
    else { state.correct_count++; state.repetitions++; const idx = Math.min(state.repetitions - 1, SRS_INTERVALS.length - 1); state.interval_days = SRS_INTERVALS[idx];
      if (quality === 3) { state.interval_days = Math.floor(state.interval_days * 1.5); state.ease_factor = Math.min(3, state.ease_factor + 0.1); }
      else if (quality === 1) state.interval_days = Math.max(1, Math.floor(state.interval_days / 2)); }
    state.next_review = addDaysISO(state.interval_days); all[cardKey] = state; lsSet(store, all);
    return { card_key: cardKey, repetitions: state.repetitions, interval_days: state.interval_days, next_review: state.next_review, ease_factor: Math.round(state.ease_factor * 100) / 100 };
  }

  function checkScenarioAnswer(pool, qid, idx, opt, msgs) {
    const q = pool.find((x) => x.id === qid);
    if (!q) return { correct: false, feedback: 'Scenario not found.', explanation: '', clinical_why: '' };
    const ci = q.correct_index ?? -1; let correct = idx === ci;
    if (opt != null && !correct) correct = String(opt).trim() === String(q.options[ci]).trim();
    return { correct, correct_index: ci, correct_answer: q.options[ci], explanation: q.explanation || '', clinical_why: q.clinical_why || '', feedback: correct ? msgs.correct : msgs.incorrect };
  }