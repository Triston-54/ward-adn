"""Generate module + router sections for data-api.js"""
from pathlib import Path

OUT = Path(__file__).parent.parent / "static" / "js" / "_data_api_modules.js"

# This file is generated inline - the Python script writes JS module code
MODULES_JS = r'''
  // ── Microbiology ────────────────────────────────────────────────────────────

  const Microbiology = {
    async data() { return loadContent('microbiology.json'); },
    async source() { return getSource('microbiology'); },
    async infectionChain() {
      const d = await this.data();
      const src = await this.source();
      return { links: d.infection_chain || [], interventions: d.chain_interventions || {}, source: src };
    },
    evaluateChainBreak(linkId, interventionId) {
      return this.data().then(async (d) => {
        const interventions = (d.chain_interventions || {})[linkId] || [];
        const chosen = interventions.find((i) => i.id === interventionId);
        if (!chosen) {
          return { correct: false, feedback: 'Invalid selection. Choose a chain link and intervention.', clinical_why: '' };
        }
        const chain = Object.fromEntries((d.infection_chain || []).map((c) => [c.id, c]));
        const linkName = chain[linkId]?.name || linkId;
        if (chosen.correct) {
          return {
            correct: true,
            feedback: chosen.explanation,
            clinical_why: chosen.clinical_why || `Breaking the ${linkName} link prevents pathogen spread — core RN practice.`,
            link: linkName,
            intervention: chosen.label,
          };
        }
        return {
          correct: false,
          feedback: chosen.explanation,
          clinical_why: chosen.clinical_why || `This action does not primarily break the ${linkName} link. Review the chain of infection.`,
          link: linkName,
          intervention: chosen.label,
        };
      });
    },
    async classification() {
      const d = await this.data();
      return { types: d.microbe_classification || [], source: await this.source() };
    },
    async pathogens() {
      const d = await this.data();
      return { pathogens: d.healthcare_pathogens || [], source: await this.source() };
    },
    async concepts() {
      const d = await this.data();
      return { concepts: d.concepts || [], source: await this.source() };
    },
    async gramStain() {
      const d = await this.data();
      return { procedure: d.gram_stain_procedure || [], interpretation: d.gram_stain_interpretation || {}, source: await this.source() };
    },
    async clinical() {
      const d = await this.data();
      return {
        hand_hygiene: d.hand_hygiene || {},
        ppe: d.ppe_guide || {},
        hai_types: d.hai_types || [],
        source: await this.source(),
      };
    },
    async breakChainScenarios(count) {
      const d = await this.data();
      return safeSample(d.break_chain_scenarios || [], count);
    },
    async whatIfScenarios(count) {
      const d = await this.data();
      return safeSample(d.what_if_scenarios || [], count);
    },
    async practice(count, mode) {
      const d = await this.data();
      const nclex = d.practice_questions || [];
      const application = d.application_questions || [];
      let pool = mode === 'nclex' ? nclex : mode === 'application' ? application : [...nclex, ...application];
      const selected = safeSample(pool, count);
      const appSet = new Set(application);
      return selected.map((q) => {
        const item = { ...q };
        item.type = appSet.has(q) ? 'application' : 'nclex';
        if (item.options && item.correct_index != null) {
          const sh = shuffleMcOptions(item.options, item.correct_index);
          item.options = sh.options;
          item.correct_index = sh.correct_index;
        }
        return item;
      });
    },
    async breakPoints() {
      const d = await this.data();
      return { break_points: d.break_points || [], source: await this.source() };
    },
    async flashcards(count) {
      const d = await this.data();
      let pathogens = [...(d.healthcare_pathogens || [])];
      shuffleArray(pathogens);
      if (count != null) pathogens = pathogens.slice(0, Math.min(count, pathogens.length));
      const cards = pathogens.map((p) => ({
        id: p.name.toLowerCase().replace(/ /g, '-'),
        front: p.name,
        back: p.full_name || '',
        precautions: p.precautions || '',
        nursing_action: p.nursing_action || '',
        clinical_why: p.clinical_why || '',
        type: p.type || '',
        source: p.source,
      }));
      return { cards, count: cards.length, source: await this.source() };
    },
    async buildClipboard() {
      const d = await this.data();
      const src = await this.source();
      const lines = ['THE WARD — MICROBIOLOGY STUDY SHEET', '='.repeat(50), '', 'CHAIN OF INFECTION', '-'.repeat(30)];
      (d.infection_chain || []).forEach((link, i) => {
        lines.push(`${i + 1}. ${link.name}`, `   ${link.description}`, `   Break it: ${link.intervention}`, '');
      });
      lines.push('KEY BREAK POINTS', '-'.repeat(30));
      (d.break_points || []).forEach((bp) => lines.push(`• ${bp}`));
      lines.push('', 'HEALTHCARE PATHOGENS', '-'.repeat(30));
      (d.healthcare_pathogens || []).forEach((p, i) => {
        lines.push(`${i + 1}. ${p.name} (${p.type || ''})`, `   Precautions: ${p.precautions || ''}`, `   Nursing: ${p.nursing_action || ''}`, `   Clinical: ${p.clinical_why || ''}`, '');
      });
      lines.push(`Source: ${src.citation} · ${src.verified_date}`);
      return { format: 'text', content: lines.join('\n') };
    },
    async buildStudySheetHtml() {
      const d = await this.data();
      const src = await this.source();
      const title = 'Microbiology Study Sheet';
      let chainRows = '';
      (d.infection_chain || []).forEach((link, i) => {
        chainRows += `<tr><td>${i + 1}</td><td><strong>${escHtml(link.name)}</strong></td><td>${escHtml(link.description)}</td><td class="intervention">${escHtml(link.intervention)}</td></tr>`;
      });
      const breakItems = (d.break_points || []).map((bp) => `<li>${escHtml(bp)}</li>`).join('');
      let pathogenRows = '';
      (d.healthcare_pathogens || []).forEach((p, i) => {
        pathogenRows += `<tr><td>${i + 1}</td><td><strong>${escHtml(p.name)}</strong><br><span class="sub">${escHtml(p.full_name || '')}</span></td><td>${escHtml(p.type || '')}</td><td>${escHtml(p.precautions || '')}</td><td class="clinical">${escHtml(p.nursing_action || '')}</td></tr>`;
      });
      return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>The Ward — ${title}</title><style>
  body { font-family: Georgia, serif; margin: 2cm; color: #111; }
  h1 { color: #0f172a; border-bottom: 2px solid #34d399; padding-bottom: 8px; }
  h2 { color: #065f46; font-size: 14px; margin-top: 28px; border-bottom: 1px solid #a7f3d0; padding-bottom: 4px; }
  .meta { color: #666; font-size: 12px; margin-bottom: 24px; }
  .break-points { background: #ecfdf5; border-left: 3px solid #34d399; padding: 12px 16px; margin: 16px 0; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 16px; }
  th { background: #064e3b; color: white; padding: 8px; text-align: left; }
  td { padding: 6px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) { background: #f0fdf4; }
  .clinical { color: #475569; font-size: 10px; }
  .intervention { color: #047857; font-size: 10px; }
  .sub { color: #64748b; font-size: 9px; }
</style></head><body>
<h1>The Ward — Microbiology</h1>
<p class="meta">${title} · ${(d.infection_chain || []).length} chain links · ${(d.healthcare_pathogens || []).length} pathogens · Source: ${escHtml(src.citation)} · New River CTC ADN</p>
<h2>Chain of Infection</h2><table><thead><tr><th>#</th><th>Link</th><th>Description</th><th>Break It</th></tr></thead><tbody>${chainRows}</tbody></table>
<h2>Key Break Points</h2><div class="break-points"><ul>${breakItems}</ul></div>
<h2>Healthcare Pathogens</h2><table><thead><tr><th>#</th><th>Pathogen</th><th>Type</th><th>Precautions</th><th>Nursing Action</th></tr></thead><tbody>${pathogenRows}</tbody></table>
<p class="meta">Generated by The Ward — local-first nursing study suite</p></body></html>`;
    },
    async buildFlashcardsMarkdown() {
      const d = await this.data();
      const lines = ['# The Ward — Microbiology Pathogen Flashcards\n'];
      (d.healthcare_pathogens || []).forEach((p, i) => {
        lines.push(`## Card ${i + 1}`, `**Front:** ${p.name}`, `**Back:** ${p.full_name || ''}`, `**Precautions:** ${p.precautions || ''}`, `**Nursing:** ${p.nursing_action || ''}`, `**Clinical:** ${p.clinical_why || ''}`, '');
      });
      return { format: 'markdown', content: lines.join('\n') };
    },
    async summary() {
      const d = await this.data();
      return {
        chain_links: (d.infection_chain || []).length,
        pathogens: (d.healthcare_pathogens || []).length,
        concepts: (d.concepts || []).length,
        practice_total: (d.practice_questions || []).length + (d.application_questions || []).length,
        scenarios: (d.break_chain_scenarios || []).length + (d.what_if_scenarios || []).length,
        break_points: (d.break_points || []).length,
        items_total: 47,
      };
    },
  };

'''

OUT.write_text(MODULES_JS, encoding='utf-8')
print('Wrote', OUT, 'lines', len(MODULES_JS.splitlines()))