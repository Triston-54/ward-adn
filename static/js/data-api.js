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

  function contentBasePath() {
    const base = (global.WARD_BASE_PATH || '').replace(/\/$/, '');
    return `${base}/data/content/`;
  }

  async function loadContent(filename) {
    if (_contentCache.has(filename)) return _contentCache.get(filename);
    const res = await _nativeFetch(`${contentBasePath()}${filename}`);
    if (!res.ok) {
      console.error(`[WardData] Failed to load ${filename}: HTTP ${res.status}`);
      return {};
    }
    try {
      const data = await res.json();
      _contentCache.set(filename, data);
      return data;
    } catch (err) {
      console.error(`[WardData] Invalid JSON in ${filename}:`, err);
      return {};
    }
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

  const Microbiology = {
    data: () => loadContent('microbiology.json'), source: () => getSource('microbiology'),
    async infectionChain() { const d = await this.data(); return { links: d.infection_chain || [], interventions: d.chain_interventions || {}, source: await this.source() }; },
    async evaluateChainBreak(linkId, iid) {
      const d = await this.data(); const ints = (d.chain_interventions || {})[linkId] || []; const chosen = ints.find((i) => i.id === iid);
      if (!chosen) return { correct: false, feedback: 'Invalid selection. Choose a chain link and intervention.', clinical_why: '' };
      const chain = Object.fromEntries((d.infection_chain || []).map((c) => [c.id, c])); const ln = chain[linkId]?.name || linkId;
      return { correct: !!chosen.correct, feedback: chosen.explanation, clinical_why: chosen.clinical_why || (chosen.correct ? `Breaking the ${ln} link prevents pathogen spread.` : `This does not primarily break the ${ln} link.`), link: ln, intervention: chosen.label };
    },
    async classification() { const d = await this.data(); return { types: d.microbe_classification || [], source: await this.source() }; },
    async pathogens() { const d = await this.data(); return { pathogens: d.healthcare_pathogens || [], source: await this.source() }; },
    async concepts() { const d = await this.data(); return { concepts: d.concepts || [], source: await this.source() }; },
    async gramStain() { const d = await this.data(); return { procedure: d.gram_stain_procedure || [], interpretation: d.gram_stain_interpretation || {}, source: await this.source() }; },
    async clinical() { const d = await this.data(); return { hand_hygiene: d.hand_hygiene || {}, ppe: d.ppe_guide || {}, hai_types: d.hai_types || [], source: await this.source() }; },
    async breakChainScenarios(n) { return safeSample((await this.data()).break_chain_scenarios || [], n); },
    async whatIfScenarios(n) { return safeSample((await this.data()).what_if_scenarios || [], n); },
    async practice(n, mode) {
      const d = await this.data(); const nclex = d.practice_questions || []; const app = d.application_questions || [];
      const pool = mode === 'nclex' ? nclex : mode === 'application' ? app : [...nclex, ...app]; const appSet = new Set(app);
      return safeSample(pool, n).map((q) => { const item = { ...q, type: appSet.has(q) ? 'application' : 'nclex' }; if (item.options) Object.assign(item, shuffleMcOptions(item.options, item.correct_index)); return item; });
    },
    async breakPoints() { const d = await this.data(); return { break_points: d.break_points || [], source: await this.source() }; },
    async flashcards(count) {
      const d = await this.data(); let p = [...(d.healthcare_pathogens || [])]; shuffleArray(p); if (count != null) p = p.slice(0, Math.min(count, p.length));
      const cards = p.map((x) => ({ id: x.name.toLowerCase().replace(/ /g, '-'), front: x.name, back: x.full_name || '', precautions: x.precautions || '', nursing_action: x.nursing_action || '', clinical_why: x.clinical_why || '', type: x.type || '', source: x.source }));
      return { cards, count: cards.length, source: await this.source() };
    },
    async buildClipboard() {
      const [d, src] = await Promise.all([this.data(), this.source()]);
      const lines = ['THE WARD — MICROBIOLOGY STUDY SHEET', '='.repeat(50), '', 'CHAIN OF INFECTION'];
      (d.infection_chain || []).forEach((l, i) => lines.push(`${i+1}. ${l.name}`, `   ${l.description}`, `   Break it: ${l.intervention}`, ''));
      lines.push('KEY BREAK POINTS'); (d.break_points || []).forEach((b) => lines.push(`• ${b}`));
      lines.push('', 'HEALTHCARE PATHOGENS'); (d.healthcare_pathogens || []).forEach((p, i) => lines.push(`${i+1}. ${p.name}`, `   Precautions: ${p.precautions || ''}`, `   Nursing: ${p.nursing_action || ''}`, ''));
      lines.push(`Source: ${src.citation} · ${src.verified_date}`); return { format: 'text', content: lines.join('\n') };
    },
    async buildStudySheetHtml() {
      const [d, src] = await Promise.all([this.data(), this.source()]);
      const cr = (d.infection_chain || []).map((l,i)=>`<tr><td>${i+1}</td><td><strong>${escHtml(l.name)}</strong></td><td>${escHtml(l.description)}</td><td>${escHtml(l.intervention)}</td></tr>`).join('');
      const pr = (d.healthcare_pathogens || []).map((p,i)=>`<tr><td>${i+1}</td><td><strong>${escHtml(p.name)}</strong></td><td>${escHtml(p.type||'')}</td><td>${escHtml(p.precautions||'')}</td><td>${escHtml(p.nursing_action||'')}</td></tr>`).join('');
      return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Microbiology Study Sheet</title><style>body{font-family:Georgia,serif;margin:2cm}table{width:100%;border-collapse:collapse;font-size:11px}th{background:#064e3b;color:#fff;padding:8px}td{padding:6px 8px;border-bottom:1px solid #ddd}</style></head><body><h1>The Ward — Microbiology</h1><p>Source: ${escHtml(src.citation)}</p><h2>Chain of Infection</h2><table><thead><tr><th>#</th><th>Link</th><th>Description</th><th>Break It</th></tr></thead><tbody>${cr}</tbody></table><h2>Pathogens</h2><table><thead><tr><th>#</th><th>Name</th><th>Type</th><th>Precautions</th><th>Nursing</th></tr></thead><tbody>${pr}</tbody></table></body></html>`;
    },
    async buildFlashcardsMarkdown() {
      const d = await this.data(); const lines = ['# The Ward — Microbiology Pathogen Flashcards\n'];
      (d.healthcare_pathogens || []).forEach((p, i) => lines.push(`## Card ${i+1}`, `**Front:** ${p.name}`, `**Back:** ${p.full_name||''}`, `**Precautions:** ${p.precautions||''}`, `**Nursing:** ${p.nursing_action||''}`, ''));
      return { format: 'markdown', content: lines.join('\n') };
    },
    async summary() { const d = await this.data(); return { chain_links: (d.infection_chain||[]).length, pathogens: (d.healthcare_pathogens||[]).length, concepts: (d.concepts||[]).length, practice_total: (d.practice_questions||[]).length+(d.application_questions||[]).length, scenarios: (d.break_chain_scenarios||[]).length+(d.what_if_scenarios||[]).length, break_points: (d.break_points||[]).length, items_total: 47 }; },
  };

  const Terminology = {
    defaultSource: async () => { const s = (await loadContent('sources.json')).terminology || TERMINOLOGY_DEFAULT_SOURCE; return { title: s.title||TERMINOLOGY_DEFAULT_SOURCE.title, url: s.url||null, citation: s.citation||TERMINOLOGY_DEFAULT_SOURCE.citation, verified_date: s.verified_date||'2026-06' }; },
    async getAllTerms() {
      const [base, extra] = await Promise.all([loadContent('terminology.json'), loadContent('terminology_terms.json')]);
      const seen = new Set(); const merged = [];
      [...(base.terms||[]), ...(extra.terms||[])].forEach((t) => { const k = t.term.toLowerCase(); if (!seen.has(k)) { seen.add(k); merged.push(t); } });
      return merged.sort((a,b) => a.term.localeCompare(b.term));
    },
    async getComponents() { const d = await loadContent('terminology.json'); return { prefixes: d.prefixes||[], roots: d.roots||[], suffixes: d.suffixes||[] }; },
    async searchTerms(q, cat, limit=50) {
      let terms = await this.getAllTerms();
      if (q) { const ql = q.toLowerCase(); terms = terms.filter((t) => t.term.toLowerCase().includes(ql) || t.definition.toLowerCase().includes(ql) || (t.breakdown||'').toLowerCase().includes(ql)); }
      if (cat) terms = terms.filter((t) => t.category === cat);
      return [terms.slice(0, limit), terms.length];
    },
    async buildWord(req) {
      const norm = (p) => (p||'').trim().toLowerCase().replace(/-/g,'');
      const comb = (r,s) => { if (r && s && /[aeiou]$/.test(r) && /^[aeiou]/.test(s)) r = r.slice(0,-1); return r+s; };
      const prefix = norm(req.prefix), root = norm(req.root), suffix = norm(req.suffix);
      const cd = await this.getComponents();
      const P = Object.fromEntries(cd.prefixes.map((p)=>[norm(p.element),p])); const R = Object.fromEntries(cd.roots.map((r)=>[norm(r.element),r])); const S = Object.fromEntries(cd.suffixes.map((s)=>[norm(s.element),s]));
      const components = [], meanings = [];
      if (prefix && P[prefix]) { components.push({type:'prefix',element:P[prefix].element,meaning:P[prefix].meaning}); meanings.push(P[prefix].meaning); } else if (prefix) components.push({type:'prefix',element:prefix,meaning:'(unknown prefix)'});
      if (R[root]) { components.push({type:'root',element:R[root].element,meaning:R[root].meaning}); meanings.push(R[root].meaning); } else components.push({type:'root',element:root,meaning:'(check root spelling)'});
      if (suffix && S[suffix]) { components.push({type:'suffix',element:S[suffix].element,meaning:S[suffix].meaning}); meanings.push(S[suffix].meaning); } else if (suffix) components.push({type:'suffix',element:suffix,meaning:'(unknown suffix)'});
      const built = `${prefix}${comb(root,suffix)}`; const known = Object.fromEntries((await this.getAllTerms()).map((t)=>[t.term.toLowerCase(),t]));
      let likely = meanings.join(' + ') || 'Unable to derive meaning'; let note = 'Breaking terms into parts helps decode unfamiliar words — core ADN competency.';
      if (known[built.toLowerCase()]) { likely = known[built.toLowerCase()].definition; note = known[built.toLowerCase()].clinical_relevance || note; }
      return { built_term: built, components, likely_meaning: likely, clinical_note: note, source: await this.defaultSource() };
    },
    async generateMc(n) {
      const terms = await this.getAllTerms(); const pool = safeSample(terms, n); const all = terms.map((t)=>t.term);
      return pool.map((t,i) => { const d = safeSample(all.filter((x)=>x.toLowerCase()!==t.term.toLowerCase()), Math.min(3,all.length-1)); const opts = [t.term,...d]; shuffleArray(opts); return { id:`mc-${t.term}-${i}`, type:'multiple_choice', question:`What medical term means: "${t.definition}"?`, options:opts, correct_index:opts.indexOf(t.term), correct_answer:t.term, explanation:`**${t.term}** — ${t.breakdown||''}. ${t.clinical_relevance||''}`, source:t.source||TERMINOLOGY_DEFAULT_SOURCE, nclex_category:'Reduction of Risk Potential' }; });
    },
    async generateType(n) { return safeSample(await this.getAllTerms(), n).map((t,i)=>({ id:`type-${t.term}-${i}`, type:'type_term', question:`Type the medical term for: "${t.definition}"`, hint:t.breakdown||'', correct_answer:t.term, acceptable_answers:[t.term.toLowerCase(),t.term.replace(/-/g,'')], explanation:`**${t.term}** — ${t.breakdown||''}`, source:t.source||TERMINOLOGY_DEFAULT_SOURCE })); },
    async generateMixed(mc, ty) { return shuffleArray([...(await this.generateMc(mc)), ...(await this.generateType(ty))]); },
    async getDueFlashcards(n, dueOnly) {
      const today = todayISO(); const cards = (await this.getAllTerms()).map((t) => { const st = getSrsState(LS_TERMINOLOGY_SRS, t.term.toLowerCase()); const due = !st.next_review || st.next_review <= today; return { key:t.term.toLowerCase(), front:t.term, back:t.definition, breakdown:t.breakdown||'', clinical:t.clinical_relevance||'', source:t.source||TERMINOLOGY_DEFAULT_SOURCE, due, repetitions:st.repetitions, interval_days:st.interval_days, next_review:st.next_review }; });
      cards.sort((a,b)=>(a.due===b.due?0:a.due?-1:1)||b.repetitions-a.repetitions); return (dueOnly?cards.filter((c)=>c.due):cards).slice(0,n);
    },
    async flashcardStats() {
      const terms = await this.getAllTerms(); const all = lsGet(LS_TERMINOLOGY_SRS,{}); const today = todayISO(); let due=0, mastered=0;
      terms.forEach((t)=>{ const st=all[t.term.toLowerCase()]; if(!st) due++; else { if(st.next_review<=today) due++; if(st.repetitions>=4) mastered++; } });
      return { total_cards:terms.length, due_today:due, mastered, progress_pct: terms.length?Math.round(mastered/terms.length*1000)/10:0 };
    },
    buildStudySheetHtml(terms, title='Study Sheet') {
      const rows = terms.map((t,i)=>`<tr><td>${i+1}</td><td><strong>${escHtml(t.term)}</strong></td><td>${escHtml(t.definition)}</td><td>${escHtml(t.clinical_relevance||'')}</td></tr>`).join('');
      return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${escHtml(title)}</title><style>body{font-family:Georgia,serif;margin:2cm}table{width:100%;border-collapse:collapse;font-size:11px}th{background:#0f172a;color:#fff;padding:8px}td{padding:6px 8px;border-bottom:1px solid #ddd}</style></head><body><h1>The Ward — Medical Terminology</h1><p>${escHtml(title)} · ${terms.length} terms</p><table><thead><tr><th>#</th><th>Term</th><th>Definition</th><th>Clinical</th></tr></thead><tbody>${rows}</tbody></table></body></html>`;
    },
    buildClipboardText(terms) {
      const lines = ['THE WARD — MEDICAL TERMINOLOGY STUDY SHEET','='.repeat(50),''];
      terms.forEach((t,i)=>{ lines.push(`${i+1}. ${t.term}`,`   Definition: ${t.definition}`); if(t.breakdown) lines.push(`   Breakdown: ${t.breakdown}`); if(t.clinical_relevance) lines.push(`   Clinical: ${t.clinical_relevance}`); lines.push(''); });
      lines.push('Source: Ehrlich & Schroeder, 8th Ed.'); return lines.join('\n');
    },
    getCustomTerms: () => lsGet(LS_CUSTOM_TERMS, []),
    saveCustomTerm(req) { const items = Terminology.getCustomTerms(); const e = { id:nextId(items), term:(req.term||'').trim(), definition:(req.definition||'').trim(), prefix:req.prefix?.trim()||null, root:req.root?.trim()||null, suffix:req.suffix?.trim()||null, clinical_note:req.clinical_note?.trim()||null, is_favorite:false, created_at:new Date().toISOString() }; items.push(e); lsSet(LS_CUSTOM_TERMS,items); return e; },
  };

  const Dosage = {
    data: () => loadContent('dosage.json'), source: () => getSource('dosage'),
    async getFirstPrinciples(ct) { const d = await this.data(); const fp = d.first_principles||{}; if(ct==='basic')ct='liquid'; if(ct==='iv_drip')ct='iv_drip_gtt'; return fp[ct]||fp.liquid||{}; },
    roundAnswer(v,u) { if(u.includes('gtt'))return Math.round(v); if(u.includes('tablet')||u.includes('capsule'))return Math.round(v*100)/100; if(u.includes('mL/hr'))return Math.round(v*10)/10; return Math.round(v*100)/100; },
    workStep(s,t,f,r,res='') { return {step:String(s),title:t,formula:f,reasoning:r,result:res}; },
    missing(msg,clin,warn) { return {answer:0,unit:'',steps:[msg],work_steps:[],derivation:'',derivation_latex:'',derivation_result:'',clinical_note:clin,safety_warnings:warn||['Complete all required fields.'],nursing_considerations:[],pharmacology_note:'',calc_label:'Incomplete calculation'}; },
    async calculate(req) {
      let ct = req.calc_type; if(ct==='basic')ct='liquid'; if(ct==='iv_drip')ct='iv_drip_gtt';
      const sw = req.show_work!==false; const src = await this.source();
      const H = { tablet_capsule:()=>Dosage.calcTablet(req,src,sw), liquid:()=>Dosage.calcLiquid(req,src,sw), iv_drip_gtt:()=>Dosage.calcGtt(req,src,sw), iv_drip_ml_hr:()=>Dosage.calcMlHr(req,src,sw), weight_based:()=>Dosage.calcWeight(req,src,sw), pediatric:()=>Dosage.calcPediatric(req,src,sw), geriatric:()=>Dosage.calcGeriatric(req,src,sw) };
      if(!H[ct]) return {...Dosage.missing('Unknown calculation type.','Select a valid calculation type.'),source:src};
      return {...await H[ct](),source:src};
    },
    async calcTablet(req,src,sw) {
      if(!req.ordered_dose||!req.available_dose) return Dosage.missing('Missing required values.','Enter ordered and available dose.');
      const D=req.ordered_dose,Hv=req.available_dose,ans=D/Hv,unit=ans!==1?'tablet(s)':'tablet';
      const steps=[`1. Ordered: ${D}`,`2. Available: ${Hv}`,`3. ${D} ÷ ${Hv} = ${fmtG(ans)} ${unit}`];
      const ws=sw?[Dosage.workStep(1,'Desired',`D=${D}`,'Read order carefully.',`${D}`),Dosage.workStep(2,'Available',`H=${Hv}`,'Check label.',`${Hv}`),Dosage.workStep(3,'Formula',`\\frac{${D}}{${Hv}}`,'Divide ordered by available.',`${fmtG(ans)} tablet(s)`)] :[];
      const warn=[]; if(ans>3)warn.push('Large number of tablets — verify order.'); if(ans>0&&ans<1&&![0.25,0.5,0.75].includes(ans))warn.push('Unusual fraction — confirm tablet can be split.');
      return {answer:Dosage.roundAnswer(ans,unit),unit,steps,work_steps:ws,derivation_latex:`\\frac{${D}}{${Hv}}`,derivation_result:fmtG(ans),derivation:`\\frac{${D}}{${Hv}} = ${fmtG(ans)}`,clinical_note:`Administer ${fmtG(ans)} tablet(s) to deliver ${D}.`,safety_warnings:warn.length?warn:['High-alert meds require double-check.'],nursing_considerations:['Document partial doses clearly.'],pharmacology_note:'Confirm therapeutic range.',calc_label:`Tablet/Capsule: ${D} ordered, ${Hv} available`,source:src};
    },
    async calcLiquid(req,src,sw) {
      if(!req.ordered_dose||!req.available_dose||!req.available_volume) return Dosage.missing('Missing required values.','Enter ordered dose, available dose, and volume.');
      const D=req.ordered_dose,Hv=req.available_dose,V=req.available_volume,ans=(D/Hv)*V,unit='mL';
      const steps=[`1. Ordered: ${D}`,`2. Available: ${Hv} in ${V} mL`,`3. (${D} ÷ ${Hv}) × ${V} = ${ans.toFixed(2)} mL`];
      const ws=sw?[Dosage.workStep(1,'Desired',`D=${D}`,'Same units.',`${D}`),Dosage.workStep(2,'Have',`${Hv}/${V} mL`,'Label concentration.',`${Hv}/${V}`),Dosage.workStep(3,'Formula',`\\frac{${D}}{${Hv}}\\times${V}`,'Cancel to mL.',`${ans.toFixed(2)} mL`)] :[];
      const warn=[]; if(ans<0.5)warn.push('Volume < 0.5 mL — use calibrated syringe.'); if(ans>30)warn.push('Large oral volume — assess tolerance.');
      return {answer:Dosage.roundAnswer(ans,unit),unit,steps,work_steps:ws,derivation_latex:`\\frac{${D}}{${Hv}}\\times${V}`,derivation_result:ans.toFixed(4),derivation:`\\frac{${D}}{${Hv}}\\times${V} = ${ans.toFixed(4)}`,clinical_note:`Administer ${ans.toFixed(2)} mL orally.`,safety_warnings:warn.length?warn:['Double-check unit conversions.'],nursing_considerations:['Stay with patient until swallowed.'],pharmacology_note:'Verify therapeutic range.',calc_label:`Liquid: ${D} ordered, ${Hv}/${V} mL`,source:src};
    },
    async calcGtt(req,src,sw) {
      if(!req.volume_to_infuse_ml||!req.time_minutes||!req.drop_factor) return Dosage.missing('Missing required values.','Enter volume, time, and drop factor.');
      const V=req.volume_to_infuse_ml,T=req.time_minutes,DF=req.drop_factor,ans=(V*DF)/T,unit='gtt/min';
      const steps=[`1. Volume: ${V} mL`,`2. Time: ${T} min`,`3. DF: ${DF}`,`4. (${V}×${DF})÷${T} = ${ans.toFixed(1)} gtt/min`];
      const ws=sw?[Dosage.workStep(1,'Volume/Time',`V=${V}, T=${T}`,'Convert hours to minutes if needed.',`${V} mL over ${T} min`),Dosage.workStep(2,'Drop factor',`DF=${DF}`,'Read tubing package.',`${DF} gtt/mL`),Dosage.workStep(3,'Rate',`\\frac{${V}\\times${DF}}{${T}}`,'Count drops 1 minute.',`${Math.round(ans)} gtt/min`)] :[];
      return {answer:Dosage.roundAnswer(ans,unit),unit,steps,work_steps:ws,derivation_latex:`\\frac{${V}\\times${DF}}{${T}}`,derivation_result:ans.toFixed(2),derivation:`\\frac{${V}\\times${DF}}{${T}} = ${ans.toFixed(2)}`,clinical_note:`Set rate to ~${Math.round(ans)} gtt/min.`,safety_warnings:['Never rely on memory for drop factor.'],nursing_considerations:['Assess IV site during infusion.'],pharmacology_note:'Monitor for fluid overload.',calc_label:`IV gtt/min: ${V} mL over ${T} min`,source:src};
    },
    async calcMlHr(req,src,sw) {
      if(!req.volume_to_infuse_ml||!req.time_minutes) return Dosage.missing('Missing required values.','Enter volume and time.');
      const V=req.volume_to_infuse_ml,Th=req.time_minutes/60; if(Th<=0) return Dosage.missing('Invalid time.','Time must be > 0.');
      const ans=V/Th,unit='mL/hr';
      const steps=[`1. Volume: ${V} mL`,`2. Time: ${req.time_minutes} min = ${Th.toFixed(2)} hr`,`3. ${V} ÷ ${Th.toFixed(2)} = ${ans.toFixed(1)} mL/hr`];
      const ws=sw?[Dosage.workStep(1,'Hours',`T=${Th.toFixed(2)} hr`,'Convert minutes to hours.',`${Th.toFixed(2)} hr`),Dosage.workStep(2,'Rate',`\\frac{${V}}{${Th.toFixed(4)}}`,'Volume ÷ hours.',`${ans.toFixed(2)} mL/hr`)] :[];
      return {answer:Dosage.roundAnswer(ans,unit),unit,steps,work_steps:ws,derivation_latex:`\\frac{${V}}{${Th.toFixed(4)}}`,derivation_result:ans.toFixed(2),derivation:`\\frac{${V}}{${Th.toFixed(4)}} = ${ans.toFixed(2)}`,clinical_note:`Program pump at ${ans.toFixed(1)} mL/hr.`,safety_warnings:['Confirm pump settings for high-alert infusions.'],nursing_considerations:['Document pump settings.'],pharmacology_note:'Check max infusion rates for electrolytes.',calc_label:`IV mL/hr: ${V} mL over ${req.time_minutes} min`,source:src};
    },
    async calcWeight(req,src,sw) {
      if(!req.patient_weight_kg||!req.dose_per_kg) return Dosage.missing('Missing required values.','Enter weight and dose per kg.');
      const W=req.patient_weight_kg,dpk=req.dose_per_kg,ans=W*dpk; let final=ans,unit='mg',label=`Weight-based: ${W} kg × ${dpk} mg/kg`,clinical=`Calculated dose = ${fmtG(ans)} mg.`;
      let steps=[`1. Weight: ${W} kg`,`2. ${W} × ${dpk} = ${fmtG(ans)} mg`];
      if(req.doses_per_day&&req.doses_per_day>1){ final=ans/req.doses_per_day; unit='mg per dose'; label+=` ÷ ${req.doses_per_day} doses`; clinical=`Each dose = ${fmtG(final)} mg (total ${fmtG(ans)} mg/day).`; steps.push(`3. ÷ ${req.doses_per_day} doses = ${fmtG(final)} mg/dose`); }
      const ws=sw?[Dosage.workStep(1,'Weight',`W=${W} kg`,'Use kg not lbs.',`${W} kg`),Dosage.workStep(2,'Dose',`${W}\\times${dpk}`,'Multiply weight × mg/kg.',`${fmtG(ans)} mg`)] :[];
      return {answer:Dosage.roundAnswer(final,unit),unit,steps,work_steps:ws,derivation_latex:`${W}\\times${dpk}`,derivation_result:fmtG(ans),derivation:`${W}×${dpk} = ${fmtG(ans)}`,clinical_note:clinical,safety_warnings:['Never exceed published maximum dose.'],nursing_considerations:['Document weight used.'],pharmacology_note:'Monitor levels when applicable.',calc_label:label,source:src};
    },
    async calcPediatric(req,src,sw) { const r=await Dosage.calcWeight(req,src,sw); r.safety_warnings=['Pediatric dosing requires current weight.',...r.safety_warnings]; r.nursing_considerations=['Verify with pharmacist for infants.',...r.nursing_considerations]; r.pharmacology_note='Check pediatric references (Harriet Lane).'; if(r.calc_label) r.calc_label='Pediatric: '+r.calc_label.replace('Weight-based: ',''); return r; },
    async calcGeriatric(req,src,sw) {
      if(!req.ordered_dose) return Dosage.missing('Missing ordered dose.','Enter standard adult dose.');
      const adult=req.ordered_dose,factor=[0.5,0.75].includes(req.geriatric_factor)?req.geriatric_factor:0.75,adj=adult*factor,pct=Math.floor(factor*100);
      const steps=[`1. Adult dose: ${adult} mg`,`2. Factor: ${factor}`,`3. ${adult} × ${factor} = ${adj.toFixed(1)} mg`];
      const ws=sw?[Dosage.workStep(1,'Adult dose',`D=${adult}`,'Usual adult dose.',`${adult} mg`),Dosage.workStep(2,'Reduction',`${adult}\\times${factor}`,'Start low, go slow.',`${adj.toFixed(1)} mg`)] :[];
      const dl=`D_{geriatric}=${adult}\\times${factor}`;
      return {answer:Math.round(adj*10)/10,unit:`mg (${pct}% adjusted)`,steps,work_steps:ws,derivation:`${dl} = ${adj.toFixed(1)}`,derivation_latex:dl,derivation_result:adj.toFixed(1),clinical_note:`Consider starting at ${adj.toFixed(1)} mg (${pct}% of adult).`,safety_warnings:['Review Beers Criteria.'],nursing_considerations:['Assess fall risk.'],pharmacology_note:'ADME changes in older adults.',calc_label:`Geriatric: ${adult} mg × ${factor}`,source:src};
    },
    async content() { const d=await this.data(); return { calc_types:d.calc_types||[], error_traps:d.error_traps||[], pharmacology_safety:d.pharmacology_safety||[], drug_classes:d.drug_classes||[], pharm_categories:d.pharm_categories||[], source:await this.source() }; },
    getDrugClass(id) { return this.data().then((d)=>(d.drug_classes||[]).find((x)=>x.id===id)||null); },
    async checkPractice(pid,idx) { const p=(await this.data()).practice_problems?.find((x)=>x.id===pid); if(!p) return {correct:false,message:'Problem not found.'}; const ok=idx===p.correct_index; return {correct:ok,correct_index:p.correct_index,explanation:p.explanation||'',answer:p.answer||'',trap:p.trap||'',nursing_note:p.nursing_note||'',work_steps:p.work_steps||[]}; },
    getFavorites: () => lsGet(LS_DOSAGE_FAVS,[]),
    saveFavorite(req) { const items=Dosage.getFavorites(); const e={id:nextId(items),calc_type:req.calc_type,label:req.label,inputs_json:req.inputs_json,result_json:req.result_json,is_favorite:true,created_at:new Date().toISOString()}; items.unshift(e); lsSet(LS_DOSAGE_FAVS,items); return e; },
    deleteFavorite(id) { lsSet(LS_DOSAGE_FAVS,Dosage.getFavorites().filter((x)=>x.id!==Number(id))); return {status:'deleted',id:Number(id)}; },
  };

  const SOAP_RX = { sub:/\b(patient reports?|states?|denies?|complains?|feels?|says?|history of|describes?)\b/i, obj:/\b(vitals?|bp\b|hr\b|rr\b|spo2|temp|observed|auscult|palp|inspected|alert|oriented)\b/i, ass:/\b(related to|r\/t|risk for|impaired|acute|diagnosis|overload|infection|distress)\b/i, plan:/\b(notify|monitor|administer|assess|reassess|escalat|order|implement|document|educate|protocol)\b/i };
  const NUM_RX = /\d+(?:\.\d+)?(?:\s*%|\/\d+)?|\d+\/\d+/g;

  const Assessment = {
    data: () => loadContent('assessment.json'), source: () => getSource('assessment'),
    headToToe: async () => [...((await Assessment.data()).head_to_toe_sequence||[])].sort((a,b)=>(a.order||0)-(b.order||0)),
    bodySystems: async () => (await Assessment.data()).body_systems||[],
    bodySystem: async (id) => (await Assessment.bodySystems()).find((s)=>s.id===id)||null,
    redFlags: async () => (await Assessment.data()).red_flags_master||[],
    redFlagsWithIds: async () => (await Assessment.redFlags()).map((f,i)=>({...f,id:f.id||`rf-${String(i).padStart(3,'0')}`})),
    async redFlagDrill(n, sys) {
      let pool = await Assessment.redFlagsWithIds(); if(sys){const f=pool.filter((x)=>x.system===sys); if(f.length>=4)pool=f;}
      const all = await Assessment.redFlagsWithIds();
      return safeSample(pool,n).map((flag)=>{
        const distr=[]; shuffleArray([...all.filter((x)=>x.id!==flag.id)]).forEach((f)=>{if(distr.length<3&&f.action!==flag.action&&!distr.includes(f.action))distr.push(f.action);});
        ['Continue routine assessment','Document and notify provider at next visit','Apply comfort measures'].forEach((fb)=>{if(distr.length<3&&fb!==flag.action&&!distr.includes(fb))distr.push(fb);});
        const sh=shuffleMcOptions([flag.action,...distr.slice(0,3)],0);
        return {id:flag.id,finding:flag.finding,system:flag.system,priority:flag.priority,options:sh.options,correct_index:sh.correct_index};
      });
    },
    async checkRedFlagDrill(fid, idx, opt) {
      const flag=(await Assessment.redFlagsWithIds()).find((f)=>f.id===fid); if(!flag) return {correct:false,feedback:'Red flag not found.',explanation:'',clinical_why:'',escalation_path:''};
      const ans=flag.action; const correct=opt!=null?String(opt).trim()===String(ans).trim():false;
      return {correct,feedback:correct?'Correct — appropriate immediate nursing action!':`Incorrect. Immediate action: ${ans}`,explanation:`**${flag.finding}** (${flag.system}). Action: ${ans}`,clinical_why:'Immediate escalation protects patient safety.',correct_answer:ans,escalation_path:`Escalation: ${ans}`,finding:flag.finding,system:flag.system,priority:flag.priority};
    },
    async practice(n,mode,sys) {
      const d=await Assessment.data(); let pool=[...(d.practice_questions||[])];
      if(sys) pool=pool.filter((q)=>q.system===sys);
      if(mode==='priority'){pool=pool.filter((q)=>/priority|first|immediate/i.test(q.question||'')); if(!pool.length)pool=[...(d.practice_questions||[])];}
      else if(mode==='red_flags') pool=pool.filter((q)=>['neurological','cardiovascular','respiratory','gastrointestinal'].includes(q.system));
      return safeSample(pool,n).map((q)=>{const item={...q}; if(item.options)Object.assign(item,shuffleMcOptions(item.options,item.correct_index)); return item;});
    },
    async checkPractice(qid,idx,opt) {
      const q=(await Assessment.data()).practice_questions?.find((x)=>x.id===qid); if(!q) return {correct:false,feedback:'Question not found.',explanation:'',clinical_why:''};
      const ans=q.options[q.correct_index]; let ok=idx===q.correct_index; if(opt!=null) ok=String(opt).trim()===String(ans).trim();
      return {correct:ok,feedback:ok?'Correct!':`Incorrect. Best answer: ${ans}`,explanation:q.explanation||'',clinical_why:q.clinical_why||'',correct_answer:ans,nclex_category:q.nclex_category,system:q.system};
    },
    specialPopulations: async () => (await Assessment.data()).special_populations||[],
    specialPopulation: async (id) => (await Assessment.specialPopulations()).find((p)=>p.id===id)||null,
    checklists: async () => (await Assessment.data()).assessment_checklists||[],
    checklist: async (id) => (await Assessment.checklists()).find((c)=>c.id===id)||null,
    soapExercises: async () => (await Assessment.data()).soap_exercises||[],
    soapExercise: async (id) => (await Assessment.soapExercises()).find((e)=>e.id===id)||null,
    sbarExercises: async () => (await Assessment.data()).sbar_exercises||[],
    sbarExercise: async (id) => (await Assessment.sbarExercises()).find((e)=>e.id===id)||null,
    flashcards: async () => (await Assessment.data()).flashcards||[],
    async getDueFlashcards(n,sys,dueOnly) {
      let pool=await Assessment.flashcards(); if(sys) pool=pool.filter((c)=>c.system===sys); shuffleArray(pool);
      const today=todayISO(); const enriched=pool.map((card)=>{const st=getSrsState(LS_ASSESSMENT_SRS,card.id); const due=!st.next_review||st.next_review<=today; return {id:card.id,front:card.front||'',system:card.system||'',system_name:card.system_name||'',type:card.type||'normal_vs_abnormal',normal:card.normal||'',abnormal:card.abnormal||'',abnormal_action:card.abnormal_action||'',clinical_why:card.clinical_why||'',due,repetitions:st.repetitions,interval_days:st.interval_days,next_review:st.next_review};}).filter((c)=>!dueOnly||c.due);
      enriched.sort((a,b)=>(a.due===b.due?0:a.due?-1:1)||b.repetitions-a.repetitions); return enriched.slice(0,n);
    },
    async flashcardStats() {
      const cards=await Assessment.flashcards(); const all=lsGet(LS_ASSESSMENT_SRS,{}); const today=todayISO(); let due=0,mastered=0;
      cards.forEach((c)=>{const st=all[c.id]; if(!st)due++; else{if(!st.next_review||st.next_review<=today)due++; if(st.repetitions>=4)mastered++;}});
      return {total:cards.length,due_today:due,mastered,new:Math.max(0,cards.length-Object.keys(all).length)};
    },
    async recordFlashcardReview(cid,q) { const cards=await Assessment.flashcards(); if(!cards.find((c)=>c.id===cid)) return {error:'Card not found',card_id:cid}; const r=recordSrsReview(LS_ASSESSMENT_SRS,cid,q); return {card_id:cid,...r}; },
    assessNextScenarios: async (n) => safeSample((await Assessment.data()).assess_next_scenarios||[],n).map((s)=>{const item={...s}; if(item.options)Object.assign(item,shuffleMcOptions(item.options,item.correct_index)); return item;}),
    async checkAssessNext(sid,idx,opt) {
      const s=(await Assessment.data()).assess_next_scenarios?.find((x)=>x.id===sid); if(!s) return {correct:false,feedback:'Scenario not found.',explanation:'',clinical_why:''};
      const ans=s.options[s.correct_index]; let ok=idx===s.correct_index; if(opt!=null) ok=String(opt).trim()===String(ans).trim();
      return {correct:ok,feedback:ok?'Correct!':`Priority: ${ans}`,explanation:s.explanation||'',clinical_why:s.clinical_why||'',correct_answer:ans,scenario_title:s.title};
    },
    findingTokens(findings) { const t=new Set(); Object.values(findings||{}).forEach((v)=>{const tx=String(v).toLowerCase(); (tx.match(NUM_RX)||[]).forEach((m)=>t.add(m.replace(/ /g,''))); (tx.match(/[a-z]{4,}/g)||[]).forEach((w)=>{if(!['patient','with','bilateral'].includes(w))t.add(w);});}); return t; },
    lengthScore(text) { const n=text.trim().length; if(n<15)return 0; if(n<40)return 40+n/40*30; if(n<120)return 70+Math.min(30,(n-40)/2); return 100; },
    keywordCoverage(text,tokens) { if(!tokens.size)return 1; const l=text.toLowerCase().replace(/ /g,''); return Math.min(1,[...tokens].filter((x)=>l.includes(x)).length/Math.max(3,tokens.size*0.35)); },
    scoreSoapSection(text,section,tokens) {
      const fb=[],st=[]; const s=text.trim(); let sc=Assessment.lengthScore(s);
      if(!s) return [0,[`${section}: section is empty.`],st];
      if(section==='subjective'){if(!SOAP_RX.sub.test(s)){fb.push('Subjective: include patient-reported language.');sc-=15;}else st.push('Good subjective language.'); if(SOAP_RX.obj.test(s)&&!SOAP_RX.sub.test(s)){fb.push('Move vitals to Objective.');sc-=20;}}
      else if(section==='objective'){const cov=Assessment.keywordCoverage(s,tokens); sc=sc*0.5+cov*50; if(cov<0.4)fb.push('Objective: add measurable findings from case.'); else st.push('Objective covers key findings.');}
      else if(section==='assessment'){if(!SOAP_RX.ass.test(s)){fb.push('Assessment: add nursing diagnosis/impression.');sc-=20;}else st.push('Assessment synthesizes data.');}
      else if(section==='plan'){if(!SOAP_RX.plan.test(s)){fb.push('Plan: add interventions and monitoring.');sc-=25;}else st.push('Plan has concrete actions.');}
      return [Math.max(0,Math.min(100,Math.round(sc*10)/10)),fb,st];
    },
    async validateSoap(eid,sub,obj,ass,plan) {
      const ex=await Assessment.soapExercise(eid); if(!ex) return {valid:false,error:'Exercise not found',exercise_id:eid};
      const tokens=Assessment.findingTokens(ex.findings||{}); const secs={subjective:sub,objective:obj,assessment:ass,plan:plan};
      const scores={},allFb=[],allSt=[],rubric=[]; Object.entries(secs).forEach(([n,t])=>{const[sc,fb,st]=Assessment.scoreSoapSection(t,n,tokens); scores[n]=sc; allFb.push(...fb); allSt.push(...st); rubric.push({section:n,score:sc});});
      const overall=Math.round(Object.values(scores).reduce((a,b)=>a+b,0)/4*10)/10; const passed=overall>=70;
      return {valid:true,exercise_id:eid,exercise_title:ex.title,overall_score:overall,passed,pass_threshold:70,section_scores:scores,feedback:allFb,strengths:allSt,rubric,documentation_tips:ex.documentation_tips||[],model_soap:passed?ex.model_soap:null};
    },
    async summary() { const d=await Assessment.data(); return {sequence_steps:(d.head_to_toe_sequence||[]).length,body_systems:(d.body_systems||[]).length,red_flags:(d.red_flags_master||[]).length,skills:(d.skills||[]).length,practice_total:(d.practice_questions||[]).length,interview_techniques:(d.interview_techniques||[]).length,special_populations:(d.special_populations||[]).length,checklists:(d.assessment_checklists||[]).length,soap_exercises:(d.soap_exercises||[]).length,sbar_exercises:(d.sbar_exercises||[]).length,flashcards:(d.flashcards||[]).length,assess_next_scenarios:(d.assess_next_scenarios||[]).length,items_total:132}; },
    async manifest() { const m=await loadContent('assessment_manifest.json'); return {manifest:m,topic_outline:m.topic_outline||[],planned_tabs:(m.tabs||[]).filter((t)=>t.status==='planned'),interactive_roadmap:m.interactive_elements||[],source:await Assessment.source()}; },
    async buildStatus() { const [m,live,sc]=await Promise.all([loadContent('assessment_manifest.json'),Assessment.summary(),loadContent('assessment_scaffold.json')]); const inv=m.content_inventory||{}; const map={head_to_toe_sequence:'sequence_steps',body_systems:'body_systems',red_flags_master:'red_flags',practice_questions:'practice_total',assessment_checklists:'checklists',soap_exercises:'soap_exercises',assess_next_scenarios:'assess_next_scenarios',special_populations:'special_populations',skills:'skills',interview_techniques:'interview_techniques',flashcards:'flashcards',sbar_exercises:'sbar_exercises'};
      const sections=Object.entries(inv).filter(([,v])=>typeof v==='object').map(([k,spec])=>({section:k,current:map[k]?(live[map[k]]||0):0,target:spec.target||0,gap:0,scaffold_queued:Array.isArray(sc[k])?sc[k].length:0,phase:spec.phase||1,status:spec.status||'unknown'}));
      const tabs=m.tabs||[]; return {module_id:m.module_id||'assessment',version:m.version,module_status:m.status,sections,tabs:{implemented:tabs.filter((t)=>t.status==='implemented').length,planned:tabs.filter((t)=>t.status==='planned').length},build_phases:m.build_phases||[],scaffold_meta:sc._meta||{},totals:{live_items:live.items_total||0,scaffold_entries:0}}; },
    async exportHeadToToeHtml() { const [steps,vitals,src]=await Promise.all([Assessment.headToToe(),Assessment.data().then((d)=>d.vital_signs||{}),Assessment.source()]); const sr=steps.map((s)=>`<tr><td>${s.order}</td><td><strong>${escHtml(s.step)}</strong><br>${escHtml(s.description)}</td><td>${escHtml(s.rationale)}</td></tr>`).join(''); const vr=(vitals.norms||[]).map((n)=>`<tr><td>${escHtml(n.parameter)}</td><td>${escHtml(n.normal)}</td><td>${escHtml(n.notes)}</td></tr>`).join(''); return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Head-to-Toe Sheet</title><style>body{font-family:Georgia,serif;margin:2cm}table{width:100%;border-collapse:collapse;font-size:11px}th{background:#4c1d95;color:#fff;padding:8px}td{padding:6px 8px;border-bottom:1px solid #ddd}</style></head><body><h1>The Ward — Head-to-Toe</h1><p>Source: ${escHtml(src.citation)}</p><table><thead><tr><th>#</th><th>Step</th><th>Rationale</th></tr></thead><tbody>${sr}</tbody></table><h2>Vital Norms</h2><table><thead><tr><th>Parameter</th><th>Normal</th><th>Notes</th></tr></thead><tbody>${vr}</tbody></table></body></html>`; },
    async exportRedFlagsHtml() { const [flags,src]=await Promise.all([Assessment.redFlags(),Assessment.source()]); const by={}; flags.forEach((f)=>{const s=f.system||'general';(by[s]=by[s]||[]).push(f);}); const sec=Object.keys(by).sort().map((sys)=>`<h2>${escHtml(sys)}</h2>${by[sys].map((f)=>`<div class="card ${f.priority}"><strong>${escHtml(f.finding)}</strong><p>${escHtml(f.action)}</p></div>`).join('')}`).join(''); return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Red Flags</title><style>body{font-family:Georgia,serif;margin:2cm}.card{border:1px solid #ccc;padding:8px;margin:6px 0}.immediate{border-left:4px solid red}</style></head><body><h1>Red Flag Quick Reference</h1><p>${flags.length} findings · ${escHtml(src.citation)}</p>${sec}</body></html>`; },
    async exportChecklistsHtml() { const [cls,src]=await Promise.all([Assessment.checklists(),Assessment.source()]); let ti=0; const sec=cls.map((cl)=>`<h2>${escHtml(cl.title)}</h2><p>${escHtml(cl.description||'')}</p>${(cl.items||[]).map((it)=>{ti++;return `<div>☐ ${escHtml(it.text)}</div>`;}).join('')}`).join(''); return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Checklists</title><style>body{font-family:Georgia,serif;margin:2cm}</style></head><body><h1>Assessment Checklists</h1><p>${cls.length} checklists · ${ti} items · ${escHtml(src.citation)}</p>${sec}</body></html>`; },
    async exportFlashcardsMarkdown(sys) { let cards=await Assessment.flashcards(); if(sys) cards=cards.filter((c)=>c.system===sys); const lines=['# The Ward — Health Assessment Flashcards\n']; cards.forEach((c,i)=>lines.push(`## Card ${i+1} — ${c.system_name||c.system}`,`**Front:** ${c.front}`,`**Normal:** ${c.normal}`,`**Abnormal:** ${c.abnormal}`,`**Action:** ${c.abnormal_action}`,`**Clinical:** ${c.clinical_why}`,'')); return lines.join('\n'); },
  };

  const MentalHealth = {
    data: () => loadContent('mental_health.json'), source: () => getSource('mental_health'),
    async summary() { const d=await this.data(); const c={communication_count:(d.therapeutic_communication||[]).length,barrier_count:(d.communication_barriers||[]).length,communication_scenario_count:(d.communication_scenarios||[]).length,safety_flag_count:(d.safety_risk_flags||[]).length,screening_tool_count:(d.screening_tools||[]).length,safety_drill_count:(d.safety_drill||[]).length,disorder_count:(d.disorders||[]).length,de_escalation_count:(d.de_escalation||[]).length,practice_count:(d.practice_questions||[]).length}; c.items_total=Object.values(c).reduce((a,b)=>a+b,0); return c; },
    async manifest() { const m=await loadContent('mental_health_manifest.json'); const live=await MentalHealth.summary(); const inv=m.content_inventory||{}; const sections={}; Object.entries(inv).forEach(([k,spec])=>{const lk=spec.live_key||'';const cur=lk?live[lk]||0:0;const tgt=spec.target||0;sections[k]={current:cur,target:tgt,complete_pct:tgt?Math.round(cur/tgt*100):0};}); const tabs=m.tabs||[]; return {manifest:m,build_status:{module_id:m.module_id,version:m.version,status:m.status,tabs_total:tabs.length,tabs_implemented:tabs.filter((t)=>t.status==='implemented').length,sections,live_summary:live,build_phases:m.build_phases||[]}}; },
    safetyDrill: (n) => MentalHealth.data().then((d)=>safeSample(d.safety_drill||[],n).map((q)=>({id:q.id,finding:q.finding,category:q.category,options:q.options}))),
    practice: (n) => MentalHealth.data().then((d)=>safeSample(d.practice_questions||[],n).map((q)=>({id:q.id,question:q.question,options:q.options,correct_index:q.correct_index,explanation:q.explanation||'',nclex_category:q.nclex_category,topic:q.topic,source:q.source}))),
    checkSafety: (id,idx,opt) => MentalHealth.data().then((d)=>checkScenarioAnswer(d.safety_drill||[],id,idx,opt,{correct:'Correct — priority action identified.',incorrect:'Review priority nursing action.'})),
    checkComm: (id,idx,opt) => MentalHealth.data().then((d)=>checkScenarioAnswer(d.communication_scenarios||[],id,idx,opt,{correct:'Correct — therapeutic response identified.',incorrect:'Review therapeutic communication.'})),
    checkDeesc: (id,idx,opt) => MentalHealth.data().then((d)=>checkScenarioAnswer((d.de_escalation||[]).filter((i)=>i.type==='scenario'),id,idx,opt,{correct:'Correct — de-escalation priority identified.',incorrect:'Review de-escalation steps.'})),
  };

  const Pathophysiology = {
    data: () => loadContent('pathophysiology.json'), source: () => getSource('pathophysiology'),
    async summary() { const d=await this.data(); return {concepts_count:(d.core_concepts||[]).length,disease_count:(d.disease_processes||[]).length,compare_count:(d.compare_contrast_pairs||[]).length,scenario_count:(d.what_breaks_down_scenarios||[]).length,flashcard_count:(d.flashcards||[]).length,practice_count:(d.practice_questions||[]).length,items_total:76}; },
    async manifest() { const m=await loadContent('pathophysiology_manifest.json'); const live=await Pathophysiology.summary(); const inv=m.content_inventory||{}; const sections={}; Object.entries(inv).forEach(([k,spec])=>{const lk=spec.live_key||'';sections[k]={current:lk?live[lk]||0:0,target:spec.target||0,complete_pct:spec.target?Math.round((live[spec.live_key]||0)/spec.target*100):0};}); const tabs=m.tabs||[]; return {manifest:m,build_status:{module_id:m.module_id,version:m.version,status:m.status,tabs_total:tabs.length,tabs_implemented:tabs.filter((t)=>t.status==='implemented').length,sections,live_summary:live,build_phases:m.build_phases||[]}}; },
    breakdownScenarios: (n) => Pathophysiology.data().then((d)=>safeSample(d.what_breaks_down_scenarios||[],n).map((s)=>({id:s.id,title:s.title,trigger:s.trigger,normal_function:s.normal_function,breakdown:s.breakdown,cascade:s.cascade||[],clinical_signs:s.clinical_signs||[],nursing_response:s.nursing_response,question:s.question,options:s.options,source_ref:s.source_ref}))),
    async checkBreakdown(sid,idx,opt) { const s=(await this.data()).what_breaks_down_scenarios?.find((x)=>x.id===sid); if(!s) return {correct:false,feedback:'Scenario not found.',explanation:'',clinical_why:''}; const ci=s.correct_index??-1; let ok=idx===ci; if(opt!=null&&!ok) ok=String(opt).trim()===String(s.options[ci]).trim(); return {correct:ok,correct_index:ci,correct_answer:s.options[ci],explanation:s.explanation||'',clinical_why:s.nursing_response||'',feedback:ok?'Correct — mechanism identified.':'Review the pathophysiologic cascade.'}; },
    flashcards: (n) => Pathophysiology.data().then((d)=>{let c=[...(d.flashcards||[])];shuffleArray(c);return n!=null?c.slice(0,Math.min(n,c.length)):c;}),
    practice: (n) => Pathophysiology.data().then((d)=>safeSample(d.practice_questions||[],n).map((q)=>{const item={...q};if(item.options)Object.assign(item,shuffleMcOptions(item.options,item.correct_index));return item;})),
    async exportFlashcardsMarkdown() { const d=await this.data(); const lines=['# The Ward — Pathophysiology Flashcards\n']; (d.flashcards||[]).forEach((c,i)=>lines.push(`## Card ${i+1}`,`**Front:** ${c.front}`,`**Back:** ${c.back}`,`**Category:** ${c.category||''}`,`**Clinical:** ${c.clinical_why||''}`,'')); return lines.join('\n'); },
  };

  const MaternalChild = {
    data: () => loadContent('maternal_child.json'), source: () => getSource('maternal_child'),
    async summary() { const d=await this.data(); const c={pregnancy_count:(d.pregnancy_stages||[]).length,labor_count:(d.labor_delivery||[]).length,postpartum_count:(d.postpartum_newborn||[]).length,pediatric_count:(d.pediatric_essentials||[]).length,safety_flag_count:(d.safety_red_flags||[]).length,drill_count:(d.complications_drill||[]).length,flashcard_count:(d.flashcards||[]).length,practice_count:(d.practice_questions||[]).length}; c.items_total=Object.values(c).reduce((a,b)=>a+b,0); return c; },
    async manifest() { const m=await loadContent('maternal_child_manifest.json'); const live=await MaternalChild.summary(); const inv=m.content_inventory||{}; const sections={}; Object.entries(inv).forEach(([k,spec])=>{const lk=spec.live_key||'';sections[k]={current:lk?live[lk]||0:0,target:spec.target||0,complete_pct:spec.target?Math.round((live[spec.live_key]||0)/spec.target*100):0};}); const tabs=m.tabs||[]; return {manifest:m,build_status:{module_id:m.module_id,version:m.version,status:m.status,tabs_total:tabs.length,tabs_implemented:tabs.filter((t)=>t.status==='implemented').length,sections,live_summary:live,build_phases:m.build_phases||[]}}; },
    complicationsDrill: (n) => MaternalChild.data().then((d)=>safeSample(d.complications_drill||[],n).map((q)=>({id:q.id,finding:q.finding,category:q.category,options:q.options}))),
    async checkComplications(id,idx,opt) { const q=(await this.data()).complications_drill?.find((x)=>x.id===id); if(!q) return {correct:false,feedback:'Question not found.',explanation:'',clinical_why:''}; const ci=q.correct_index??-1; let ok=idx===ci; if(opt!=null&&!ok) ok=String(opt).trim()===String(q.options[ci]).trim(); return {correct:ok,correct_index:ci,correct_answer:q.options[ci],explanation:q.explanation||'',clinical_why:q.clinical_why||'',feedback:ok?'Correct — priority action identified.':'Review priority nursing action for this complication.'}; },
    flashcards: (n) => MaternalChild.data().then((d)=>{let c=[...(d.flashcards||[])];shuffleArray(c);return n!=null?c.slice(0,n):c;}),
    practice: (n) => MaternalChild.data().then((d)=>safeSample(d.practice_questions||[],n).map((q)=>({id:q.id,question:q.question,options:q.options,correct_index:q.correct_index,explanation:q.explanation||'',nclex_category:q.nclex_category,source_ref:q.source_ref||'maternal_child'}))),
    async exportFlashcardsMarkdown() { const d=await this.data(); const lines=['# The Ward — Maternal-Child Flashcards\n']; (d.flashcards||[]).forEach((c,i)=>lines.push(`## Card ${i+1}`,`**Front:** ${c.front}`,`**Back:** ${c.back}`,`**Category:** ${c.category||'OB/Peds'}`,'')); return lines.join('\n'); },
  };

  const Verify = {
    allSources: async () => { const r=await loadContent('sources.json'); const sources=Object.entries(r).map(([k,v])=>enrichSource(k,v)); return {sources,count:sources.length,module_map:MODULE_SOURCE_KEYS,reference_types:Object.keys(REFERENCE_TYPE_STYLES)}; },
    moduleSources: async (mid) => { let d=await getModuleSources(mid); if(!d.sources.length&&mid!=='general'){d=await getModuleSources('general');d.module_id=mid;d.note=`No dedicated sources for '${mid}'; showing general references.`;} return d; },
    lookup: async (id) => { const r=await loadContent('sources.json'); return r[id]?enrichSource(id,r[id]):null; },
  };

  function auditSlug(t) { return String(t).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''); }
  function auditItem(mid,key,type,title,sub) { return {module_id:mid,item_key:key,item_type:type,title,subtitle:sub||null,status:'unreviewed',verified_date:null,source_note:null,review_note:null,updated_at:null}; }
  async function buildAuditCatalog() {
    const items=[]; (await Terminology.getAllTerms()).forEach((t)=>items.push(auditItem('terminology',`term:${auditSlug(t.term)}`,'concept',t.term,(t.definition||'').slice(0,120))));
    const micro=await loadContent('microbiology.json'); (micro.healthcare_pathogens||[]).forEach((p)=>items.push(auditItem('microbiology',`pathogen:${auditSlug(p.name)}`,'concept',p.name,p.full_name)));
    const dosage=await loadContent('dosage.json'); (dosage.practice_problems||[]).forEach((p)=>items.push(auditItem('dosage',`practice:${p.id}`,'practice',(p.question||'').slice(0,80),p.calc_type)));
    const assess=await loadContent('assessment.json'); (assess.red_flags_master||[]).forEach((rf)=>items.push(auditItem('assessment',`redflag:${auditSlug((rf.finding||'').slice(0,50))}`,'concept',(rf.finding||'').slice(0,80),rf.system)));
    const mh=await loadContent('mental_health.json'); (mh.disorders||[]).forEach((d)=>items.push(auditItem('mental_health',`disorder:${d.id||auditSlug(d.name)}`,'concept',d.name,d.category)));
    const patho=await loadContent('pathophysiology.json'); (patho.disease_processes||[]).forEach((d)=>items.push(auditItem('pathophysiology',`disease:${d.id||auditSlug(d.name)}`,'concept',d.name,d.category)));
    const mc=await loadContent('maternal_child.json'); (mc.safety_red_flags||[]).forEach((f)=>items.push(auditItem('maternal_child',`redflag:${f.id||auditSlug((f.finding||'').slice(0,50))}`,'concept',(f.finding||'').slice(0,80),f.category)));
    return items;
  }
  const Audit = {
    mergeItem(item) { const rec=lsGet(LS_AUDIT,{})[`${item.module_id}:${item.item_key}`]; return rec?{...item,...rec}:item; },
    catalogStats: async () => { const cat=await buildAuditCatalog(); const by={}; cat.forEach((i)=>{by[i.module_id]=(by[i.module_id]||0)+1;}); return {total_catalog:cat.length,by_module:by,modules:AUDIT_MODULE_LABELS,assessment_summary:await Assessment.summary(),maternal_child_summary:await MaternalChild.summary()}; },
    summary: async () => { const cat=await buildAuditCatalog(); const counts={verified:0,needs_review:0,unreviewed:0}; const by={}; cat.forEach((i)=>{const m=Audit.mergeItem(i);const st=m.status||'unreviewed';counts[st]++;const mod=by[m.module_id]||{verified:0,needs_review:0,unreviewed:0,total:0};mod.total++;mod[st]++;by[m.module_id]=mod;}); return {total:cat.length,...counts,by_module:by,modules:AUDIT_MODULE_LABELS}; },
    items: async (params) => { let cat=(await buildAuditCatalog()).map((i)=>Audit.mergeItem(i)); const mid=params.get('module_id'),st=params.get('status'),typ=params.get('item_type'),srch=params.get('search'),lim=qInt(params,'limit',100),off=qInt(params,'offset',0); if(mid)cat=cat.filter((i)=>i.module_id===mid); if(st)cat=cat.filter((i)=>i.status===st); if(typ)cat=cat.filter((i)=>i.item_type===typ); if(srch){const q=srch.toLowerCase();cat=cat.filter((i)=>i.title.toLowerCase().includes(q)||(i.subtitle||'').toLowerCase().includes(q)||i.item_key.includes(q));} return {items:cat.slice(off,off+lim),total:cat.length,limit:lim,offset:off,statuses:['unreviewed','verified','needs_review'],modules:AUDIT_MODULE_LABELS}; },
    saveRecord(mid,key,patch) { const all=lsGet(LS_AUDIT,{}); const k=`${mid}:${key}`; all[k]={...all[k],...patch,updated_at:new Date().toISOString()}; lsSet(LS_AUDIT,all); return all[k]; },
  };

  async function handleApiRequest(pathWithQuery, init = {}) {
    const method = (init.method || 'GET').toUpperCase();
    const parsed = new URL(pathWithQuery, 'http://localhost');
    const pathname = parsed.pathname;
    const params = parsed.searchParams;
    const body = parseBody(init);
    try {
      if (pathname.startsWith('/api/socratic/')) return notFound('Socratic tutor not available in static mode');
      if (pathname.startsWith('/api/pharmacy/')) return notFound('Pharmacy module removed');

      if (pathname === '/api/progress/sync' && method === 'POST') {
        const modules = Object.entries(MODULES).map(([module_id, m]) => ({ module_id, module_name: m.name, percentage: 0, items_completed: 0, items_total: m.total, last_practiced: null, streak_days: 0 }));
        return jsonResponse({ status: 'ok', message: 'Progress synced (static mode)', user: { display_name: 'Student', program: 'ADN', overall_percentage: 0, streak_days: 0, last_studied: null }, modules, synced_at: new Date().toISOString() });
      }
      if (pathname === '/api/progress/dashboard') return jsonResponse({ overall_percentage: 0, streak_days: 0, modules_studied: 0, total_modules: Object.keys(MODULES).length });
      if (pathname === '/api/progress/modules') return jsonResponse(Object.entries(MODULES).map(([module_id, m]) => ({ module_id, module_name: m.name, percentage: 0, items_completed: 0, items_total: m.total, streak_days: 0 })));
      if (pathname === '/api/progress/update' && method === 'POST') return jsonResponse(noopProgress());

      if (pathname === '/api/verify/sources') return jsonResponse(await Verify.allSources());
      let m = pathname.match(/^\/api\/verify\/sources\/([^/]+)$/); if (m) return jsonResponse(await Verify.moduleSources(decodeURIComponent(m[1])));
      m = pathname.match(/^\/api\/verify\/source\/([^/]+)$/); if (m) { const s = await Verify.lookup(decodeURIComponent(m[1])); return s ? jsonResponse(s) : notFound(); }

      if (pathname === '/api/audit/summary') return jsonResponse(await Audit.summary());
      if (pathname === '/api/audit/catalog-stats') return jsonResponse(await Audit.catalogStats());
      if (pathname === '/api/audit/items') return jsonResponse(await Audit.items(params));
      m = pathname.match(/^\/api\/audit\/items\/([^/]+)\/([^/]+)\/verify$/);
      if (m && method === 'POST') { const [,mod,key]=m; Audit.saveRecord(decodeURIComponent(mod),decodeURIComponent(key),{status:'verified',verified_date:body?.verified_date||'2026-06',source_note:body?.source_note||null,review_note:null}); const cat=await buildAuditCatalog(); const item=cat.find((i)=>i.module_id===decodeURIComponent(mod)&&i.item_key===decodeURIComponent(key)); return jsonResponse(Audit.mergeItem({...item,status:'verified'})); }
      m = pathname.match(/^\/api\/audit\/items\/([^/]+)\/([^/]+)\/flag$/);
      if (m && method === 'POST') { const [,mod,key]=m; Audit.saveRecord(decodeURIComponent(mod),decodeURIComponent(key),{status:'needs_review',review_note:body?.review_note||''}); const cat=await buildAuditCatalog(); const item=cat.find((i)=>i.module_id===decodeURIComponent(mod)&&i.item_key===decodeURIComponent(key)); return jsonResponse(Audit.mergeItem({...item,status:'needs_review'})); }
      m = pathname.match(/^\/api\/audit\/items\/([^/]+)\/([^/]+)$/);
      if (m && method === 'DELETE') { const [,mod,key]=m; const all=lsGet(LS_AUDIT,{}); delete all[`${decodeURIComponent(mod)}:${decodeURIComponent(key)}`]; lsSet(LS_AUDIT,all); return jsonResponse({status:'cleared'}); }

      // Microbiology
      if (pathname === '/api/microbiology/stats') return jsonResponse(noopStats('microbiology',{summary:await Microbiology.summary()}));
      if (pathname === '/api/microbiology/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/microbiology/infection-chain') return jsonResponse(await Microbiology.infectionChain());
      if (pathname === '/api/microbiology/chain-break' && method === 'POST') return jsonResponse({...await Microbiology.evaluateChainBreak(body.link_id,body.intervention_id),source:await getSource('microbiology')});
      if (pathname === '/api/microbiology/classification') return jsonResponse(await Microbiology.classification());
      if (pathname === '/api/microbiology/pathogens') return jsonResponse(await Microbiology.pathogens());
      if (pathname === '/api/microbiology/concepts') return jsonResponse(await Microbiology.concepts());
      if (pathname === '/api/microbiology/gram-stain') return jsonResponse(await Microbiology.gramStain());
      if (pathname === '/api/microbiology/clinical') return jsonResponse(await Microbiology.clinical());
      if (pathname === '/api/microbiology/scenarios/break-chain') return jsonResponse({scenarios:await Microbiology.breakChainScenarios(qInt(params,'count',4))});
      if (pathname === '/api/microbiology/scenarios/what-if') return jsonResponse({scenarios:await Microbiology.whatIfScenarios(qInt(params,'count',3))});
      if (pathname === '/api/microbiology/practice') { const qs=await Microbiology.practice(qInt(params,'count',10),qStr(params,'mode')||'mixed'); return jsonResponse({questions:qs,count:qs.length,mode:qStr(params,'mode')||'mixed'}); }
      if (pathname === '/api/microbiology/break-points') return jsonResponse(await Microbiology.breakPoints());
      if (pathname === '/api/microbiology/flashcards') return jsonResponse(await Microbiology.flashcards(params.has('count')?qInt(params,'count',20):null));
      if (pathname === '/api/microbiology/export/clipboard') return jsonResponse(await Microbiology.buildClipboard());
      if (pathname === '/api/microbiology/export/study-sheet') return textResponse(await Microbiology.buildStudySheetHtml());
      if (pathname === '/api/microbiology/export/flashcards') return jsonResponse(await Microbiology.buildFlashcardsMarkdown());

      // Terminology
      if (pathname === '/api/terminology/stats') return jsonResponse(noopStats('terminology',{flashcards:await Terminology.flashcardStats(),term_count:(await Terminology.getAllTerms()).length}));
      if (pathname === '/api/terminology/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/terminology/components') return jsonResponse({...(await Terminology.getComponents()),source:await Terminology.defaultSource()});
      if (pathname === '/api/terminology/build' && method === 'POST') return jsonResponse(await Terminology.buildWord(body));
      if (pathname === '/api/terminology/terms') { const [terms,total]=await Terminology.searchTerms(qStr(params,'q'),qStr(params,'category'),qInt(params,'limit',50)); const custom=Terminology.getCustomTerms(); custom.forEach((c)=>{if(terms.length<qInt(params,'limit',50))terms.push({term:c.term,definition:c.definition,prefix:c.prefix,root:c.root,suffix:c.suffix,clinical_relevance:c.clinical_note,category:'custom',source:{title:'User-added',citation:'Personal notes'}});}); return jsonResponse({terms,total:total+custom.length,source:await Terminology.defaultSource()}); }
      m = pathname.match(/^\/api\/terminology\/term\/(.+)$/); if (m) { const known=Object.fromEntries((await Terminology.getAllTerms()).map((t)=>[t.term.toLowerCase(),t])); const term=known[decodeURIComponent(m[1]).toLowerCase()]; return term?jsonResponse({term,source:term.source||await Terminology.defaultSource()}):jsonResponse({error:'Term not found'}); }
      if (pathname === '/api/terminology/practice') { const count=qInt(params,'count',10),mode=qStr(params,'mode')||'mixed'; const qs=mode==='mc'?await Terminology.generateMc(count):mode==='type'?await Terminology.generateType(count):await Terminology.generateMixed(Math.floor(count/2),count-Math.floor(count/2)); return jsonResponse({questions:qs,count:qs.length,mode}); }
      if (pathname === '/api/terminology/flashcards') { const cards=await Terminology.getDueFlashcards(qInt(params,'count',20),qBool(params,'due_only')); return jsonResponse({cards,count:cards.length,stats:await Terminology.flashcardStats()}); }
      if (pathname === '/api/terminology/flashcards/review' && method === 'POST') return jsonResponse(recordSrsReview(LS_TERMINOLOGY_SRS,body.card_key,body.quality));
      if (pathname === '/api/terminology/custom' && method === 'GET') return jsonResponse(Terminology.getCustomTerms());
      if (pathname === '/api/terminology/custom' && method === 'POST') return jsonResponse(Terminology.saveCustomTerm(body));
      m = pathname.match(/^\/api\/terminology\/custom\/(\d+)$/); if (m && method === 'PATCH') { const items=Terminology.getCustomTerms(); const e=items.find((t)=>t.id===Number(m[1])); if(!e)return notFound(); e.is_favorite=body.is_favorite; lsSet(LS_CUSTOM_TERMS,items); return jsonResponse(e); }
      if (pathname === '/api/terminology/export/clipboard') { const [terms]=await Terminology.searchTerms(null,null,qInt(params,'count',50)); return jsonResponse({format:'text',content:Terminology.buildClipboardText(terms),count:terms.length}); }
      if (pathname === '/api/terminology/export/study-sheet') { const [terms]=await Terminology.searchTerms(null,qStr(params,'category'),qInt(params,'count',50)); return textResponse(Terminology.buildStudySheetHtml(terms)); }
      if (pathname === '/api/terminology/export/flashcards') { const [terms]=await Terminology.searchTerms(null,null,qInt(params,'count',50)); const lines=['# Terminology Flashcards\n']; terms.forEach((t,i)=>lines.push(`## Card ${i+1}`,`**Front:** ${t.term}`,`**Back:** ${t.definition}`,'')); return jsonResponse({format:'markdown',content:lines.join('\n'),count:terms.length}); }
      if (pathname === '/api/terminology/export/json') { const terms=await Terminology.getAllTerms(); return jsonResponse({format:'json',module:'terminology',total:terms.length,source:'Ehrlich & Schroeder, 8th Ed.',terms}); }

      // Dosage
      if (pathname === '/api/dosage/stats') { const d=await Dosage.data(); return jsonResponse(noopStats('dosage',{practice_count:(d.practice_problems||[]).length,favorites_count:Dosage.getFavorites().length})); }
      if (pathname === '/api/dosage/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/dosage/calculate' && method === 'POST') return jsonResponse(await Dosage.calculate(body));
      m = pathname.match(/^\/api\/dosage\/first-principles\/([^/]+)$/); if (m) return jsonResponse({calc_type:m[1],principles:await Dosage.getFirstPrinciples(m[1]),source:await getSource('dosage')});
      if (pathname === '/api/dosage/content') return jsonResponse(await Dosage.content());
      m = pathname.match(/^\/api\/dosage\/pharm\/([^/]+)$/); if (m) { const dc=await Dosage.getDrugClass(m[1]); return dc?jsonResponse({drug_class:dc,source:await getSource('dosage')}):jsonResponse({error:'Drug class not found',class_id:m[1]}); }
      if (pathname === '/api/dosage/practice') { const d=await Dosage.data(); return jsonResponse({problems:(d.practice_problems||[]).map((p)=>({id:p.id,calc_type:p.calc_type||'',question:p.question,options:p.options})),source:await getSource('dosage')}); }
      if (pathname === '/api/dosage/practice/check' && method === 'POST') return jsonResponse({...(await Dosage.checkPractice(body.problem_id,body.selected_index)),source:await getSource('dosage')});
      if (pathname === '/api/dosage/favorites' && method === 'GET') return jsonResponse(Dosage.getFavorites());
      if (pathname === '/api/dosage/favorites' && method === 'POST') return jsonResponse(Dosage.saveFavorite(body));
      m = pathname.match(/^\/api\/dosage\/favorites\/(\d+)$/); if (m && method === 'DELETE') return jsonResponse(Dosage.deleteFavorite(m[1]));

      // Assessment
      if (pathname === '/api/assessment/manifest') return jsonResponse(await Assessment.manifest());
      if (pathname === '/api/assessment/scaffold') { const sc=await loadContent('assessment_scaffold.json'); return jsonResponse({meta:sc._meta||{},scaffold:Object.fromEntries(Object.entries(sc).filter(([k])=>!k.startsWith('_'))),schemas:sc._schemas||{}}); }
      if (pathname === '/api/assessment/build-status') return jsonResponse(await Assessment.buildStatus());
      if (pathname === '/api/assessment/stats') return jsonResponse(noopStats('assessment',{summary:await Assessment.summary(),flashcards:await Assessment.flashcardStats()}));
      if (pathname === '/api/assessment/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/assessment/content') { const d=await Assessment.data(); return jsonResponse({vital_signs:d.vital_signs||{},pain_assessment:d.pain_assessment||{},interview_techniques:d.interview_techniques||[],skills:d.skills||[],source:await getSource('assessment')}); }
      if (pathname === '/api/assessment/head-to-toe') return jsonResponse({sequence:await Assessment.headToToe(),source:await getSource('assessment')});
      if (pathname === '/api/assessment/systems') return jsonResponse({systems:await Assessment.bodySystems(),source:await getSource('assessment')});
      m = pathname.match(/^\/api\/assessment\/systems\/([^/]+)$/); if (m) { const sys=await Assessment.bodySystem(m[1]); return sys?jsonResponse({system:sys,source:await getSource('assessment')}):jsonResponse({error:'System not found',system_id:m[1]}); }
      if (pathname === '/api/assessment/red-flags') return jsonResponse({red_flags:await Assessment.redFlags(),source:await getSource('assessment')});
      if (pathname === '/api/assessment/red-flag-drill') { const qs=await Assessment.redFlagDrill(qInt(params,'count',5),qStr(params,'system')); return jsonResponse({questions:qs,count:qs.length,source:await getSource('assessment')}); }
      if (pathname === '/api/assessment/red-flag-drill/check' && method === 'POST') return jsonResponse({...(await Assessment.checkRedFlagDrill(body.flag_id,body.selected_index,body.selected_option)),source:await getSource('assessment')});
      if (pathname === '/api/assessment/practice') { const qs=await Assessment.practice(qInt(params,'count',10),qStr(params,'mode')||'mixed',qStr(params,'system')); return jsonResponse({questions:qs.map((q)=>({id:q.id,question:q.question,options:q.options,system:q.system,nclex_category:q.nclex_category})),count:qs.length,mode:qStr(params,'mode')||'mixed',source:await getSource('assessment')}); }
      if (pathname === '/api/assessment/practice/check' && method === 'POST') return jsonResponse({...(await Assessment.checkPractice(body.question_id,body.selected_index,body.selected_option)),source:await getSource('assessment')});
      if (pathname === '/api/assessment/special-populations') return jsonResponse({populations:await Assessment.specialPopulations(),source:await getSource('assessment')});
      m = pathname.match(/^\/api\/assessment\/special-populations\/([^/]+)$/); if (m) { const pop=await Assessment.specialPopulation(m[1]); return pop?jsonResponse({population:pop,source:await getSource('assessment')}):jsonResponse({error:'Population not found'}); }
      if (pathname === '/api/assessment/checklists') { const cls=await Assessment.checklists(); return jsonResponse({checklists:cls.map((c)=>({id:c.id,title:c.title,category:c.category,description:c.description,item_count:(c.items||[]).length})),source:await getSource('assessment')}); }
      m = pathname.match(/^\/api\/assessment\/checklists\/([^/]+)$/); if (m) { const cl=await Assessment.checklist(m[1]); return cl?jsonResponse({checklist:cl,source:await getSource('assessment')}):jsonResponse({error:'Checklist not found'}); }
      if (pathname === '/api/assessment/soap') { const ex=await Assessment.soapExercises(); return jsonResponse({exercises:ex.map((e)=>({id:e.id,title:e.title,patient_context:e.patient_context})),source:await getSource('assessment')}); }
      m = pathname.match(/^\/api\/assessment\/soap\/([^/]+)$/); if (m && m[1] !== 'validate') { const ex=await Assessment.soapExercise(m[1]); return ex?jsonResponse({exercise:ex,source:await getSource('assessment')}):jsonResponse({error:'Exercise not found'}); }
      if (pathname === '/api/assessment/soap/validate' && method === 'POST') return jsonResponse({...(await Assessment.validateSoap(body.exercise_id,body.subjective,body.objective,body.assessment,body.plan)),source:await getSource('assessment')});
      if (pathname === '/api/assessment/sbar') { const ex=await Assessment.sbarExercises(); return jsonResponse({exercises:ex.map((e)=>({id:e.id,title:e.title,situation:e.situation})),source:await getSource('assessment')}); }
      m = pathname.match(/^\/api\/assessment\/sbar\/([^/]+)$/); if (m) { const ex=await Assessment.sbarExercise(m[1]); return ex?jsonResponse({exercise:ex,source:await getSource('assessment')}):jsonResponse({error:'Exercise not found'}); }
      if (pathname === '/api/assessment/flashcards') { const cards=await Assessment.getDueFlashcards(qInt(params,'count',20),qStr(params,'system'),qBool(params,'due_only')); return jsonResponse({cards,count:cards.length,stats:await Assessment.flashcardStats(),source:await getSource('assessment')}); }
      if (pathname === '/api/assessment/flashcards/review' && method === 'POST') return jsonResponse({...(await Assessment.recordFlashcardReview(body.card_id,body.quality)),source:await getSource('assessment')});
      if (pathname === '/api/assessment/export/flashcards') return jsonResponse({format:'markdown',content:await Assessment.exportFlashcardsMarkdown(qStr(params,'system')),count:(await Assessment.summary()).flashcards});
      if (pathname === '/api/assessment/export/head-to-toe') return textResponse(await Assessment.exportHeadToToeHtml());
      if (pathname === '/api/assessment/export/red-flags') return textResponse(await Assessment.exportRedFlagsHtml());
      if (pathname === '/api/assessment/export/checklist') return textResponse(await Assessment.exportChecklistsHtml());
      if (pathname === '/api/assessment/scenarios/assess-next') { const sc=await Assessment.assessNextScenarios(qInt(params,'count',4)); return jsonResponse({scenarios:sc.map((s)=>({id:s.id,title:s.title,setup:s.setup,findings_so_far:s.findings_so_far||[],question:s.question,options:s.options})),count:sc.length,source:await getSource('assessment')}); }
      if (pathname === '/api/assessment/scenarios/check' && method === 'POST') return jsonResponse({...(await Assessment.checkAssessNext(body.scenario_id,body.selected_index,body.selected_option)),source:await getSource('assessment')});

      // Mental Health
      if (pathname === '/api/mental-health/stats') return jsonResponse(noopStats('mental_health',{summary:await MentalHealth.summary()}));
      if (pathname === '/api/mental-health/manifest') return jsonResponse(await MentalHealth.manifest());
      if (pathname === '/api/mental-health/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/mental-health/communication') { const d=await MentalHealth.data(); return jsonResponse({techniques:d.therapeutic_communication||[],barriers:d.communication_barriers||[],source:await getSource('mental_health')}); }
      if (pathname === '/api/mental-health/safety-risk') { const d=await MentalHealth.data(); return jsonResponse({flags:d.safety_risk_flags||[],screening_tools:d.screening_tools||[],source:await getSource('mental_health')}); }
      if (pathname === '/api/mental-health/safety-drill') return jsonResponse({questions:await MentalHealth.safetyDrill(qInt(params,'count',5)),source:await getSource('mental_health')});
      if (pathname === '/api/mental-health/safety-drill/check' && method === 'POST') return jsonResponse({...(await MentalHealth.checkSafety(body.question_id,body.selected_index,body.selected_option)),source:await getSource('mental_health')});
      if (pathname === '/api/mental-health/communication-scenarios') { const d=await MentalHealth.data(); return jsonResponse({scenarios:d.communication_scenarios||[],source:await getSource('mental_health')}); }
      if (pathname === '/api/mental-health/communication-scenarios/check' && method === 'POST') return jsonResponse({...(await MentalHealth.checkComm(body.question_id,body.selected_index,body.selected_option)),source:await getSource('mental_health')});
      if (pathname === '/api/mental-health/disorders') { const d=await MentalHealth.data(); return jsonResponse({disorders:d.disorders||[],source:await getSource('mental_health')}); }
      if (pathname === '/api/mental-health/de-escalation') { const d=await MentalHealth.data(); return jsonResponse({items:d.de_escalation||[],source:await getSource('mental_health')}); }
      if (pathname === '/api/mental-health/de-escalation/check' && method === 'POST') return jsonResponse({...(await MentalHealth.checkDeesc(body.question_id,body.selected_index,body.selected_option)),source:await getSource('mental_health')});
      if (pathname === '/api/mental-health/practice') return jsonResponse({questions:await MentalHealth.practice(qInt(params,'count',10)),source:await getSource('mental_health')});

      // Pathophysiology
      if (pathname === '/api/pathophysiology/stats') return jsonResponse(noopStats('pathophysiology',{summary:await Pathophysiology.summary()}));
      if (pathname === '/api/pathophysiology/manifest') return jsonResponse(await Pathophysiology.manifest());
      if (pathname === '/api/pathophysiology/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/pathophysiology/concepts') { const d=await Pathophysiology.data(); return jsonResponse({concepts:d.core_concepts||[],source:await getSource('pathophysiology')}); }
      if (pathname === '/api/pathophysiology/diseases') { const d=await Pathophysiology.data(); return jsonResponse({diseases:d.disease_processes||[],source:await getSource('pathophysiology')}); }
      if (pathname === '/api/pathophysiology/compare') { const d=await Pathophysiology.data(); return jsonResponse({pairs:d.compare_contrast_pairs||[],source:await getSource('pathophysiology')}); }
      if (pathname === '/api/pathophysiology/scenarios/breakdown') return jsonResponse({scenarios:await Pathophysiology.breakdownScenarios(qInt(params,'count',5)),source:await getSource('pathophysiology')});
      if (pathname === '/api/pathophysiology/scenarios/check' && method === 'POST') return jsonResponse({...(await Pathophysiology.checkBreakdown(body.scenario_id,body.selected_index,body.selected_option)),source:await getSource('pathophysiology')});
      if (pathname === '/api/pathophysiology/flashcards') { const cards=await Pathophysiology.flashcards(params.has('count')?qInt(params,'count',20):null); return jsonResponse({cards,count:cards.length,source:await getSource('pathophysiology')}); }
      if (pathname === '/api/pathophysiology/export/flashcards') return jsonResponse({format:'markdown',content:await Pathophysiology.exportFlashcardsMarkdown()});
      if (pathname === '/api/pathophysiology/practice') { const qs=await Pathophysiology.practice(qInt(params,'count',10)); return jsonResponse({questions:qs,count:qs.length}); }

      // Maternal-Child
      if (pathname === '/api/maternal-child/stats') return jsonResponse(noopStats('maternal_child',{summary:await MaternalChild.summary()}));
      if (pathname === '/api/maternal-child/manifest') return jsonResponse(await MaternalChild.manifest());
      if (pathname === '/api/maternal-child/progress' && method === 'POST') return jsonResponse(noopProgress());
      if (pathname === '/api/maternal-child/antepartum') { const d=await MaternalChild.data(); return jsonResponse({topics:d.pregnancy_stages||[],source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/intrapartum') { const d=await MaternalChild.data(); return jsonResponse({topics:d.labor_delivery||[],source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/postpartum-newborn') { const d=await MaternalChild.data(); return jsonResponse({topics:d.postpartum_newborn||[],source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/pediatrics') { const d=await MaternalChild.data(); return jsonResponse({topics:d.pediatric_essentials||[],source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/safety') { const d=await MaternalChild.data(); return jsonResponse({flags:d.safety_red_flags||[],source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/complications-drill') return jsonResponse({questions:await MaternalChild.complicationsDrill(qInt(params,'count',5)),source:await getSource('maternal_child')});
      if (pathname === '/api/maternal-child/complications-drill/check' && method === 'POST') return jsonResponse({...(await MaternalChild.checkComplications(body.question_id,body.selected_index,body.selected_option)),source:await getSource('maternal_child')});
      if (pathname === '/api/maternal-child/flashcards') { const cards=await MaternalChild.flashcards(params.has('count')?qInt(params,'count',20):null); return jsonResponse({cards,count:cards.length,source:await getSource('maternal_child')}); }
      if (pathname === '/api/maternal-child/export/flashcards') return jsonResponse({format:'markdown',content:await MaternalChild.exportFlashcardsMarkdown()});
      if (pathname === '/api/maternal-child/practice') { const qs=await MaternalChild.practice(qInt(params,'count',10)); return jsonResponse({questions:qs,count:qs.length,source:await getSource('maternal_child')}); }

      // Med-Surg
      if (pathname === '/api/med-surg/content') { const d=await loadContent('med_surg.json'); return jsonResponse(d); }
      if (pathname === '/api/med-surg/practice') { const d=await loadContent('med_surg.json'); const qs=safeSample(d.practice_questions||[],qInt(params,'count',10)); return jsonResponse({questions:qs,count:qs.length,source:await getSource('assessment')}); }

      // NCLEX Prep
      if (pathname === '/api/nclex-prep/content') { const d=await loadContent('nclex_prep.json'); return jsonResponse(d); }

      // Generic module progress/stats
      m = pathname.match(/^\/api\/([^/]+)\/progress$/); if (m && method === 'POST') return jsonResponse(noopProgress());
      m = pathname.match(/^\/api\/([^/]+)\/stats$/); if (m) { const mid=m[1].replace(/-/g,'_'); if(MODULES[mid]) return jsonResponse(noopStats(mid)); }

      return notFound(`No handler for ${method} ${pathname}`);
    } catch (err) {
      console.error('[WardData] API error:', err);
      return jsonResponse({ error: String(err.message || err) }, 500);
    }
  }

  const WardData = {
    loadContent,
    preloadContent,
    safeSample,
    shuffleArray,
    jsonResponse,
    textResponse,
    MODULES,
    Microbiology,
    Terminology,
    Dosage,
    Assessment,
    MentalHealth,
    Pathophysiology,
    MaternalChild,
    Verify,
    Audit,
    handleApiRequest,
  };

  function installFetchInterceptor() {
    _nativeFetch = global.fetch.bind(global);
    global.fetch = async function wardFetch(input, init = {}) {
      const url = typeof input === 'string' ? input : input.url;
      try {
        const parsed = new URL(url, global.location?.origin || 'http://localhost');
        if (parsed.pathname.startsWith('/api/')) {
          return WardData.handleApiRequest(parsed.pathname + parsed.search, init);
        }
      } catch { /* relative or opaque URL — fall through to native fetch */ }
      return _nativeFetch(input, init);
    };
  }

  global.WardData = WardData;
  installFetchInterceptor();
})(typeof window !== 'undefined' ? window : globalThis);