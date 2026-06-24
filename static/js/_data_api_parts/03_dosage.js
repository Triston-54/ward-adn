
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