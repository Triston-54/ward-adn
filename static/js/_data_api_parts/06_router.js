
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