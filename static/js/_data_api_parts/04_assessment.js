
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