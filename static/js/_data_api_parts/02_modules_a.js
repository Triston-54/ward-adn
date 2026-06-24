
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