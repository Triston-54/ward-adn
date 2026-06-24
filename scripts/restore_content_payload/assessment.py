"""Build assessment.json."""
from __future__ import annotations

from typing import Any

from scripts.restore_content_payload.common import mcq, src

# Flashcard specs reused from generate_assessment_flashcards.py patterns
SYSTEM_CARD_SPECS: dict[str, list[tuple]] = {
    "neurological": [
        ("GCS 15, oriented ×4, speech clear", "Alert, oriented, coherent speech", "Confusion, slurred speech, word-finding difficulty", "Full neuro assessment; stroke protocol if focal deficit", "Acute neuro change requires immediate escalation."),
        ("Strength 5/5 all extremities bilaterally", "Equal strength 5/5", "Unilateral weakness or numbness", "FAST screen; notify provider", "Unilateral weakness suggests stroke until ruled out."),
        ("Steady gait, no assistive device needed", "Steady coordinated gait", "Unsteady gait, inability to move extremity", "Fall precautions; neuro checks", "Gait change may reflect weakness or orthostasis."),
        ("No seizure activity observed", "No seizure activity", "Active seizure or post-ictal confusion", "Protect airway, time seizure, notify provider", "Seizure = airway and safety priority."),
    ],
    "cardiovascular": [
        ("Apical pulse regular 78/min, S1/S2 without extra sounds", "Regular rate 60–100; S1/S2 only", "Irregular rhythm, murmur, gallop S3/S4", "ECG if symptomatic; continuous monitoring if ordered", "New arrhythmia may reduce cardiac output."),
        ("No pitting edema; JVD not visible at 45°", "No edema; no JVD", "Pitting edema, JVD at 45°", "Daily weights, strict I&O, notify provider", "Edema + JVD suggest fluid overload/heart failure."),
        ("BP 118/72, HR 72, warm pink extremities", "Stable vitals; good perfusion", "SBP <90 with symptoms, HR <40 or >150", "IV fluids per order; notify provider", "Hypotension with symptoms = perfusion emergency."),
        ("Chest pain absent; denies SOB", "No chest pain", "Chest pain + diaphoresis + SOB", "12-lead ECG, notify provider immediately", "ACS requires time-sensitive intervention."),
    ],
    "respiratory": [
        ("Symmetric chest rise; clear breath sounds", "Symmetric expansion; clear lungs", "Accessory muscle use, asymmetric expansion", "Position upright, O₂, notify provider", "Increased work of breathing signals distress."),
        ("SpO₂ 97% on room air, RR 16", "SpO₂ ≥94% RA; RR 12–20", "SpO₂ <94%, tachypnea", "Apply O₂, reassess, notify if not improving", "Hypoxemia needs correction before routine care."),
        ("No cough; sputum clear/white if present", "No productive cough", "Productive cough with colored sputum, hemoptysis", "Culture per order; notify provider", "Purulent sputum suggests infection."),
        ("No wheezes; good air entry all fields", "Clear breath sounds", "Wheezes, diminished sounds, silent chest", "Bronchodilator per order; prepare for escalation", "Silent chest in asthma = impending failure."),
    ],
    "gastrointestinal": [
        ("Abdomen soft, non-tender; active BS ×4", "Soft, non-tender; active bowel sounds", "Distension, absent/hyperactive BS, guarding", "NPO if surgical concern; notify provider", "Absent BS + distension suggests obstruction."),
        ("Regular BM pattern; no nausea", "Regular elimination; no NV", "Diarrhea, melena, hematochezia", "Monitor H&H; GI bleed protocol if indicated", "GI bleeding can cause hemodynamic collapse."),
        ("No rebound tenderness or rigidity", "Non-tender abdomen", "Rebound tenderness, rigid abdomen", "NPO, IV access, notify surgeon", "Rigid abdomen = surgical emergency."),
        ("Last BM yesterday, soft brown stool", "Normal elimination", "Projectile vomiting, coffee-ground emesis", "NPO, NG decompression per order", "Coffee-ground emesis suggests upper GI bleed."),
    ],
    "genitourinary": [
        ("Voiding without difficulty; urine clear yellow", "Normal voiding pattern", "Oliguria, dysuria, hematuria", "Strict I&O; notify provider", "Oliguria may signal AKI."),
        ("No suprapubic fullness", "No bladder distension", "Palpable distended bladder", "Bladder scan; catheter per order", "Retention can cause AKI."),
        ("Urine output 50 mL/hr", "Adequate urine output", "Anuria or <30 mL/hr", "Assess hydration; notify provider", "Anuria with pain suggests obstruction."),
        ("No flank pain or fever", "No GU pain", "Flank pain + fever + CVA tenderness", "Urine culture; notify provider", "Pyelonephritis requires prompt treatment."),
    ],
    "musculoskeletal": [
        ("Full ROM all joints without pain", "Full painless ROM", "Limited ROM, pain with movement", "Immobilize if trauma; pain management", "Pain-limited ROM after injury needs evaluation."),
        ("Strength 5/5 major muscle groups", "Strength 5/5", "Weakness grade <5", "Compare bilaterally; neuro checks", "New weakness may be neuro emergency."),
        ("Steady gait, independent ambulation", "Steady gait", "Unable to bear weight after fall", "Fall precautions; imaging per protocol", "Hip fracture common in older adult falls."),
        ("No swelling or deformity at joints", "No joint deformity", "Hot swollen joint with fever", "Notify provider; infection workup", "Septic arthritis is emergency."),
    ],
    "integumentary": [
        ("Skin warm, dry, intact; turgor elastic", "Intact skin; turgor <2 sec", "Poor turgor, tenting", "Encourage fluids; monitor I&O", "Poor turgor signals dehydration."),
        ("Even skin color; no open areas", "Even coloration; intact skin", "Pallor, cyanosis, jaundice, mottling", "Assess perfusion and O₂", "Acute cyanosis = oxygenation problem."),
        ("No pressure injury present", "Intact skin over bony prominences", "Stageable pressure injury", "Reposition q2h; wound consult", "Pressure injuries worsen quickly."),
        ("Small bruise 1 cm, non-tender", "Expected minor ecchymosis", "Rapidly spreading petechiae + fever", "Notify provider; monitor LOC", "Purpura + fever may indicate serious infection."),
    ],
    "heent": [
        ("PERRLA; conjunctiva pink; sclera white", "PERRLA; pink conjunctiva", "Unequal pupils, sluggish reactivity", "Neuro check; notify provider", "New anisocoria with LOC change = neuro emergency."),
        ("Moist pink oral mucosa", "Moist mucous membranes", "Dry cracked lips, thrush", "Oral care; hydration", "Dry mucosa reflects hydration status."),
        ("Face symmetric at rest and with smile", "Facial symmetry", "Unilateral facial droop", "FAST stroke screen; notify provider", "Facial droop is stroke sign."),
        ("Nares patent bilaterally; no drainage", "Patent nares", "Purulent drainage, uncontrolled epistaxis", "Notify provider; airway watch", "Uncontrolled epistaxis threatens airway."),
    ],
    "psychosocial": [
        ("Mood appropriate; denies SI/HI", "Appropriate affect; denies self-harm", "Hopelessness, SI with plan", "Suicide screening; 1:1 per protocol", "Active SI with plan requires immediate safety."),
        ("Coherent thought process; engaged", "Coherent, goal-directed", "Disorganized thought, hallucinations", "Therapeutic communication; notify provider", "Psychosis may impair participation in care."),
        ("Identifies support persons", "Support system identified", "Signs of neglect or abuse", "Mandatory reporting per state law", "Abuse disclosure triggers legal obligations."),
        ("Calm, cooperative with care", "Calm cooperative behavior", "Severe agitation with violence risk", "De-escalation; 1:1 observation", "Agitation threatens safety."),
    ],
    "endocrine-immune": [
        ("Thyroid non-palpable; no tremor", "Non-palpable smooth thyroid", "Goiter, exophthalmos, tremor", "Vitals; TSH per order; notify provider", "Thyroid storm/myxedema are emergencies."),
        ("Lymph nodes small, mobile, non-tender", "Small mobile nodes", "Hard fixed nodes", "Document; notify provider", "Fixed supraclavicular node suggests malignancy."),
        ("Skin intact; wounds healing normally", "Intact healing skin", "Frequent infections, poor healing", "Infection precautions; glucose if diabetic", "Immunocompromise blunts inflammation signs."),
        ("Fingerstick glucose 110 mg/dL, alert", "Euglycemia with normal LOC", "Glucose <70 or >400 with altered LOC", "Hypoglycemia protocol; notify for crisis", "Hypoglycemia causes confusion and falls."),
    ],
}


def _body_systems() -> list[dict[str, Any]]:
    systems = [
        ("neurological", "Neurological", ["Mental status and level of consciousness", "Cranial nerves II–XII", "Motor strength and sensation", "Cerebellar function and gait", "Pupils PERRLA"]),
        ("cardiovascular", "Cardiovascular", ["Apical pulse rate and rhythm", "Heart sounds S1/S2", "Peripheral pulses and cap refill", "JVD and edema assessment", "Blood pressure both arms if indicated"]),
        ("respiratory", "Respiratory", ["Inspect chest symmetry and effort", "Palpate expansion and fremitus", "Auscultate all lung fields", "Percussion for dullness/hyperresonance", "SpO₂ and respiratory rate"]),
        ("gastrointestinal", "Gastrointestinal", ["Inspect abdomen contour", "Auscultate bowel sounds all quadrants", "Palpate light then deep", "Assess last BM and nausea", "Liver/spleen span if indicated"]),
        ("genitourinary", "Genitourinary", ["Inspect external genitalia per policy", "Bladder scan or suprapubic palpation", "Urine color, odor, clarity", "Flank/CVA tenderness", "Strict I&O"]),
        ("musculoskeletal", "Musculoskeletal", ["Inspect joints and posture", "ROM active then passive", "Muscle strength 0–5 scale", "Gait and balance", "Spine alignment"]),
        ("integumentary", "Integumentary (Skin)", ["Inspect color, turgor, lesions", "Palpate temperature and moisture", "Pressure injury risk (Braden)", "Nail and hair assessment", "Document wounds with measurements"]),
        ("heent", "HEENT", ["Head/scalp inspection", "Eyes: acuity, pupils, conjunctiva", "Ears: canal and tympanic membrane", "Nose and sinuses", "Throat, oral mucosa, dentition"]),
        ("psychosocial", "Psychosocial", ["Mood and affect", "Thought process and content", "Suicide/homicide screening", "Coping and support systems", "Cultural/spiritual preferences"]),
        ("endocrine-immune", "Endocrine & Immune", ["Thyroid palpation", "Lymph node survey", "Blood glucose if indicated", "Signs of infection/inflammation", "Fatigue and weight change history"]),
    ]
    out = []
    for sid, name, steps in systems:
        specs = SYSTEM_CARD_SPECS.get(sid, [])
        abnormal = [s[2] for s in specs[:3]]
        normal = [s[1] for s in specs[:3]]
        out.append({
            "id": sid, "name": name,
            "overview": f"Systematic {name.lower()} assessment integrates inspection, palpation, auscultation, and patient-reported data.",
            "assessment_steps": steps,
            "normal_findings": normal,
            "abnormal_findings": abnormal,
            "red_flags": [specs[0][3]] if specs else ["Notify provider for acute change from baseline"],
            "nursing_implications": [f"Document objective {name.lower()} findings in flowsheet.", "Compare to baseline and report changes."],
            "source_ref": "assessment",
        })
    return out


def _generate_flashcards(body_systems: list[dict]) -> list[dict]:
    cards = [
        {"id": "fc-neuro-01", "system": "neurological", "system_name": "Neurological", "type": "normal_vs_abnormal",
         "front": "Neurological — Pupils 3 mm bilaterally, equal, briskly reactive. Normal or abnormal?",
         "normal": "PERRLA — pupils 2–6 mm, equal, reactive.", "abnormal": "Unequal or non-reactive pupils, new anisocoria.",
         "abnormal_action": "Full neuro check; stroke protocol if focal deficit.", "clinical_why": "Pupil changes may signal ICP or stroke."},
        {"id": "fc-cardio-01", "system": "cardiovascular", "system_name": "Cardiovascular", "type": "normal_vs_abnormal",
         "front": "Cardiovascular — Cap refill 4 sec, cool pale toes, weak pedal pulses. Normal or abnormal?",
         "normal": "Cap refill <2 sec; strong equal pulses.", "abnormal": "Delayed refill, weak pulses — perfusion concern.",
         "abnormal_action": "Vitals, IV access per order; do NOT Trendelenburg for CHF.", "clinical_why": "Perfusion reflects cardiac output."},
        {"id": "fc-resp-01", "system": "respiratory", "system_name": "Respiratory", "type": "normal_vs_abnormal",
         "front": "Respiratory — Crackles at bases, SpO₂ 89%, RR 28. Normal or abnormal?",
         "normal": "Clear lungs; SpO₂ ≥94% RA; RR 12–20.", "abnormal": "Crackles + hypoxemia + tachypnea.",
         "abnormal_action": "High Fowler's, O₂, notify provider.", "clinical_why": "Hypoxemia is priority — ABCs first."},
    ]
    seen = {c["id"] for c in cards}
    for sys in body_systems:
        sid, name = sys["id"], sys["name"]
        for i, spec in enumerate(SYSTEM_CARD_SPECS.get(sid, []), 1):
            front_stem, normal, abnormal, action, why = spec
            cid = f"fc-{sid[:4]}-{i:02d}"
            if cid in seen:
                cid = f"fc-{sid}-{i:02d}"
            cards.append({
                "id": cid, "system": sid, "system_name": name, "type": "normal_vs_abnormal",
                "front": f"{name} — {front_stem}. Normal or abnormal?",
                "normal": normal, "abnormal": abnormal, "abnormal_action": action, "clinical_why": why,
            })
            seen.add(cid)
    red_flag_ids = [
        ("fc-rf-01", "neurological", "Sudden worst headache + stiff neck + fever", "Thunderclap headache — meningitis/SAH concern.", "Neuro/vitals stat; notify provider."),
        ("fc-rf-02", "cardiovascular", "Sudden unilateral leg swelling, warmth, pain", "DVT until ruled out.", "Do not massage; notify provider."),
        ("fc-rf-03", "respiratory", "Stridor at rest, SpO₂ 90%", "Upper airway narrowing.", "Airway equipment; notify rapid response."),
        ("fc-rf-04", "gastrointestinal", "Rigid board-like abdomen with rebound", "Peritoneal signs.", "NPO, IV access, notify surgeon."),
        ("fc-rf-05", "genitourinary", "Post-op anuric 10 hr, suprapubic distension", "Acute retention.", "Bladder scan; catheter per order."),
        ("fc-rf-06", "musculoskeletal", "Cast pain with passive toe extension, cool toes", "Compartment syndrome.", "Notify immediately; do not elevate leg."),
        ("fc-rf-07", "integumentary", "Wound with exposed bone on coccyx", "Stage 4 pressure injury.", "Wound consult; pressure redistribution."),
        ("fc-rf-08", "heent", "Battle sign + clear fluid from nose post trauma", "Basilar skull fracture.", "C-spine precautions; NPO."),
        ("fc-rf-09", "psychosocial", "Suicide plan with pills in room", "Imminent suicide risk.", "1:1; remove means; notify provider."),
        ("fc-rf-10", "endocrine-immune", "Glucose 42 mg/dL, diaphoresis, confusion", "Symptomatic hypoglycemia.", "15 g fast carb if able; recheck 15 min."),
        ("fc-rf-11", "respiratory", "Asthma: silent chest, exhausted, SpO₂ 88%", "Impending respiratory failure.", "Rapid response; continuous nebs per order."),
        ("fc-rf-12", "cardiovascular", "HR 168 irregular, BP 86/50, dizzy", "Unstable tachyarrhythmia.", "Monitor; notify provider; ACLS per protocol."),
        ("fc-rf-13", "gastrointestinal", "Absent BS, distension, feculent vomiting", "Obstruction/ileus.", "NPO, NG per order, notify surgeon."),
        ("fc-rf-14", "neurological", "GCS 15→12 over 2 hr post head injury", "Expanding intracranial lesion.", "Neuro checks q15min; CT per protocol."),
        ("fc-rf-15", "vital_signs", "Infant RR 65, nasal flaring, retractions, SpO₂ 91%", "Respiratory distress.", "Position; O₂; notify provider."),
    ]
    for rid, sys, front, abnormal, action in red_flag_ids:
        if rid not in seen:
            cards.append({
                "id": rid, "system": sys, "system_name": sys.replace("_", " ").title(), "type": "red_flag",
                "front": f"RED FLAG — {front}. Priority action?",
                "normal": "Context-dependent stable baseline.", "abnormal": abnormal,
                "abnormal_action": action, "clinical_why": "Immediate escalation protects patient safety.",
            })
            seen.add(rid)
    cards.extend([
        {"id": "fc-vitals-01", "system": "vital_signs", "system_name": "Vital Signs", "type": "normal_vs_abnormal",
         "front": "Temp 101.8°F, HR 112, BP 102/64. Normal or abnormal?",
         "normal": "Afebrile; HR 60–100; stable BP.", "abnormal": "Fever + tachycardia + relative hypotension.",
         "abnormal_action": "Sepsis screening; cultures; notify provider.", "clinical_why": "Early sepsis recognition saves lives."},
        {"id": "fc-vitals-02", "system": "vital_signs", "system_name": "Vital Signs", "type": "normal_vs_abnormal",
         "front": "Orthostatics: lying 120/80 → standing 100/70 with dizziness.",
         "normal": "SBP drop <20 mmHg without symptoms.", "abnormal": "Orthostatic hypotension ≥20 SBP drop with symptoms.",
         "abnormal_action": "Fall precautions; fluids per order.", "clinical_why": "Orthostasis increases fall risk."},
    ])
    return cards


def build() -> dict[str, Any]:
    s = src("assessment")
    body_systems = _body_systems()
    head_to_toe_sequence = [
        {"order": 1, "step": "General Survey", "description": "Observe appearance, hygiene, distress, and ABCs from doorway.", "technique": "Inspection", "tips": ["Note work of breathing before approaching", "Introduce self and verify identity"]},
        {"order": 2, "step": "Vital Signs", "description": "Temperature, pulse, respirations, BP, SpO₂, pain score.", "technique": "Measurement", "tips": ["Orthostatics if fall risk or diuretics", "Pain is fifth vital sign"]},
        {"order": 3, "step": "HEENT", "description": "Head, eyes, ears, nose, throat systematic exam.", "technique": "Inspection, palpation, auscultation", "tips": ["PERRLA", "Oral mucosa and dentition"]},
        {"order": 4, "step": "Neck", "description": "Trachea midline, thyroid, lymph nodes, JVD, carotid bruits.", "technique": "Palpation, auscultation", "tips": ["JVD assessed at 45°"]},
        {"order": 5, "step": "Chest & Lungs", "description": "Respiratory inspection, palpation, percussion, auscultation.", "technique": "Full respiratory exam", "tips": ["Compare apical to basal sounds", "Note SpO₂ with exertion if ordered"]},
        {"order": 6, "step": "Cardiovascular", "description": "Apical pulse, heart sounds, peripheral perfusion.", "technique": "Auscultation, palpation", "tips": ["Apical pulse 1 full minute if irregular"]},
        {"order": 7, "step": "Abdomen", "description": "Inspect, auscultate bowel sounds, palpate quadrants.", "technique": "Auscultate before palpate", "tips": ["Light palpation first", "Note last BM"]},
        {"order": 8, "step": "Musculoskeletal", "description": "ROM, strength, gait, spine.", "technique": "Active/passive ROM", "tips": ["Compare bilaterally", "Fall risk screening"]},
        {"order": 9, "step": "Neurological", "description": "LOC, cranial nerves, motor/sensory, reflexes as indicated.", "technique": "Serial neuro checks", "tips": ["Baseline for comparison", "Stroke protocol if acute deficit"]},
        {"order": 10, "step": "Skin & Psychosocial", "description": "Integument, pressure injury risk, mental status, safety screening.", "technique": "Inspection, therapeutic communication", "tips": ["Braden scale", "Suicide screening when indicated"]},
    ]
    red_flags_master = [
        {"finding": "Sudden unilateral weakness and slurred speech", "system": "neurological", "priority": "immediate", "action": "Activate stroke protocol; note last known well; notify provider; NPO until swallow eval"},
        {"finding": "GCS decrease ≥2 points", "system": "neurological", "priority": "immediate", "action": "Neuro checks q15min; notify provider; prepare for imaging"},
        {"finding": "Chest pain with diaphoresis and ST elevation on monitor", "system": "cardiovascular", "priority": "immediate", "action": "12-lead ECG; aspirin per protocol; notify provider; continuous monitoring"},
        {"finding": "SBP <90 mmHg with altered mental status", "system": "cardiovascular", "priority": "immediate", "action": "IV access; fluids per order; notify provider; assess perfusion"},
        {"finding": "SpO₂ <90% with increased work of breathing", "system": "respiratory", "priority": "immediate", "action": "Airway assessment; O₂; high Fowler's; notify provider"},
        {"finding": "Stridor at rest", "system": "respiratory", "priority": "immediate", "action": "Airway equipment to bedside; notify provider/rapid response"},
        {"finding": "Silent chest in asthma with exhaustion", "system": "respiratory", "priority": "immediate", "action": "Rapid response; continuous bronchodilator per order; prepare for escalation"},
        {"finding": "Rigid abdomen with rebound tenderness", "system": "gastrointestinal", "priority": "immediate", "action": "NPO; IV access; notify surgeon/provider; vitals q15min"},
        {"finding": "Hematemesis or melena with hypotension", "system": "gastrointestinal", "priority": "immediate", "action": "IV access; fluids; type and crossmatch per order; notify provider"},
        {"finding": "Oliguria <30 mL/hr in adult with hypotension", "system": "genitourinary", "priority": "urgent", "action": "Assess volume status; notify provider; strict I&O"},
        {"finding": "Temperature >38.3°C (101°F) in neutropenic patient", "system": "endocrine-immune", "priority": "immediate", "action": "Blood cultures per order; broad-spectrum antibiotics per protocol; notify provider"},
        {"finding": "Active suicidal ideation with plan and means", "system": "psychosocial", "priority": "immediate", "action": "1:1 observation; remove means; notify provider/charge nurse; document quotes"},
        {"finding": "New onset confusion with fever and stiff neck", "system": "neurological", "priority": "immediate", "action": "Sepsis/meningitis workup; notify provider; prepare for LP/CT per order"},
        {"finding": "Exophthalmos, fever, tachycardia in hyperthyroid patient", "system": "endocrine-immune", "priority": "immediate", "action": "Notify provider — thyroid storm concern; cooling, beta-blocker per order"},
        {"finding": "Epigastric pain radiating to back, rigid abdomen (pancreatitis concern)", "system": "gastrointestinal", "priority": "immediate", "action": "NPO; IV fluids; pain management per order; notify provider"},
        {"finding": "COPD patient SpO₂ 98% on high-flow O₂ with somnolence", "system": "respiratory", "priority": "urgent", "action": "Titrate O₂ to target SpO₂ 88–92%; ABG per order; notify provider"},
        {"finding": "Orthostatic SBP drop ≥20 mmHg with fall", "system": "cardiovascular", "priority": "urgent", "action": "Fall precautions; fluids per order; medication review"},
        {"finding": "Unilateral calf swelling, warmth, Homan sign unreliable", "system": "cardiovascular", "priority": "urgent", "action": "Do not massage; notify provider; anticoagulation/imaging per order"},
        {"finding": "Purpura + fever in immunocompromised patient", "system": "integumentary", "priority": "immediate", "action": "Blood cultures; notify provider; sepsis protocol"},
        {"finding": "Infant <28 days with rectal temp ≥38°C (100.4°F)", "system": "vital_signs", "priority": "immediate", "action": "Full sepsis workup per protocol; notify provider; NPO for procedures"},
    ]
    skills = [
        {"id": "skill-vitals", "title": "Vital Signs Measurement", "steps": ["Verify patient identity", "Temperature route per policy", "Pulse apical/radial 1 min if irregular", "RR count full minute", "BP proper cuff size", "SpO₂ and pain score"], "clinical_why": "Baseline for all clinical decisions.", "source": s},
        {"id": "skill-orthostatic_vitals", "title": "Orthostatic Vital Signs", "steps": ["Supine 2 min — BP and HR", "Stand 1 min — repeat", "Stand 3 min — repeat", "Note symptoms", "Criteria: SBP drop ≥20 or DBP ≥10 with symptoms"], "clinical_why": "Detects volume depletion and medication effects.", "source": s},
        {"id": "skill-lung_auscultation", "title": "Lung Auscultation", "steps": ["Anterior/posterior/lateral fields", "Compare side to side", "Note adventitious sounds", "Assess after cough/deep breath"], "clinical_why": "Crackles/wheezes guide oxygen and bronchodilator therapy.", "source": s},
        {"id": "skill-abdominal_assessment", "title": "Abdominal Assessment", "steps": ["Inspect contour", "Auscultate BS four quadrants", "Light palpation all quadrants", "Deep palpation if tolerated", "Document tenderness/guarding"], "clinical_why": "Auscultate before palpate to avoid altering bowel sounds.", "source": s},
        {"id": "skill-neuro_check", "title": "Focused Neurological Check", "steps": ["LOC/GCS", "Pupils", "Motor strength", "Speech", "Compare to baseline"], "clinical_why": "Serial checks detect deterioration in stroke/TBI.", "source": s},
        {"id": "skill-fast_stroke", "title": "FAST Stroke Screening", "steps": ["Face droop", "Arm drift", "Speech slurred", "Time last known well", "Inpatient: notify provider/stroke team per protocol"], "clinical_why": "Time is brain — thrombolysis windows are limited.", "source": s},
        {"id": "skill-pain_assessment", "title": "Pain Assessment (PQRST)", "steps": ["Provocation/palliation", "Quality", "Region/radiation", "Severity 0–10", "Timing"], "clinical_why": "Pain is subjective — believe the patient.", "source": s},
        {"id": "skill-skin_inspection", "title": "Skin & Pressure Injury Inspection", "steps": ["Inspect bony prominences", "Stage pressure injuries", "Measure wounds", "Braden scale", "Reposition q2h"], "clinical_why": "Prevention is easier than treatment of Stage 3–4 injuries.", "source": s},
        {"id": "skill-iv_site", "title": "Peripheral IV Site Assessment", "steps": ["Inspect for redness, swelling, pain", "Palpate for warmth", "Check patency and dressing", "Rotate sites per policy"], "clinical_why": "Early phlebitis detection prevents infiltration.", "source": s},
        {"id": "skill-suicide_screen", "title": "Suicide Risk Screening", "steps": ["Ask directly about SI", "Assess plan and means", "Prior attempts", "Protective factors", "Escalate per protocol"], "clinical_why": "Asking does not increase risk — it enables safety planning.", "source": s},
        {"id": "skill-pediatric_vitals", "title": "Pediatric Vital Signs", "steps": ["Use age-appropriate norms", "Count RR on infant 1 full minute", "Axillary temp infants", "Pain scale by developmental age"], "clinical_why": "Pediatric decompensation is rapid — assess work of breathing.", "source": s},
        {"id": "skill-sbar", "title": "SBAR Handoff Communication", "steps": ["Situation", "Background", "Assessment", "Recommendation"], "clinical_why": "Structured communication reduces errors during transitions.", "source": s},
    ]
    interview_techniques = [
        {"id": "open-ended", "technique": "Open-Ended Questions", "example": "Tell me what brought you in today.", "purpose": "Elicits patient narrative without leading.", "source": s},
        {"id": "closed", "technique": "Closed-Ended Questions", "example": "Is the pain worse at night?", "purpose": "Clarifies specific yes/no data.", "source": s},
        {"id": "reflection", "technique": "Reflection", "example": "You sound frustrated about the wait.", "purpose": "Validates feelings and builds rapport.", "source": s},
        {"id": "clarification", "technique": "Clarification", "example": "When you say dizzy, do you mean the room spins?", "purpose": "Ensures accurate understanding.", "source": s},
        {"id": "summarization", "technique": "Summarization", "example": "So your pain started 2 days ago after lifting...", "purpose": "Confirms data before documentation.", "source": s},
        {"id": "silence", "technique": "Therapeutic Silence", "example": "Pause after emotional statement.", "purpose": "Allows patient time to process and continue.", "source": s},
    ]
    special_populations = [
        {"id": "older-adult", "name": "Older Adults", "age_range": "≥65 years", "considerations": ["Polypharmacy and Beers Criteria", "Fall risk and orthostatics", "Atypical MI presentation", "Sensory deficits affect teaching"], "assessment_modifications": ["Allow extra time", "Ensure hearing aids/glasses", "Include caregiver in teaching when appropriate"], "source": s},
        {"id": "pediatric", "name": "Pediatric Patients", "age_range": "Infancy through adolescence", "considerations": ["Developmental milestones", "Family-centered care", "Weight-based dosing", "Parental consent"], "assessment_modifications": ["Use age-appropriate pain scales", "Observe parent-child interaction", "Axillary temp in infants"], "source": s},
        {"id": "pregnancy", "name": "Pregnant Patients", "age_range": "Antepartum", "considerations": ["Supine hypotension after 20 weeks — left lateral tilt", "FHR monitoring when indicated", "Avoid teratogenic exposures"], "assessment_modifications": ["Include fundal height and FHR when appropriate", "Assess for preeclampsia symptoms"], "source": s},
        {"id": "mental-health", "name": "Behavioral Health", "age_range": "All ages", "considerations": ["Trauma-informed approach", "Suicide/homicide screening", "CIWA-Ar for alcohol withdrawal (scores ≥20 severe)"], "assessment_modifications": ["Low stimulation environment", "Clear simple questions", "1:1 if acute risk"], "source": s},
        {"id": "non-english", "name": "Limited English Proficiency", "age_range": "All ages", "considerations": ["Professional interpreter — not family for clinical consent", "Teach-back method", "Cultural humility"], "assessment_modifications": ["Interpreter present before sensitive questions", "Document language preference"], "source": s},
        {"id": "newborn", "name": "Newborn", "age_range": "0–28 days", "considerations": ["Thermoregulation — axillary temp", "Fever ≥38°C is emergency", "APGAR at 1 and 5 minutes"], "assessment_modifications": ["Keep warm during exam", "Assess feeding and voiding/stooling"], "source": s},
    ]
    assessment_checklists = [
        {"id": "chk-admission", "title": "Admission Assessment Checklist", "items": ["Identity verification", "Allergies", "Vital signs", "Pain score", "Fall risk", "Skin inspection", "Medication reconciliation", "Advance directives"], "source": s},
        {"id": "chk-shift", "title": "Shift Assessment Checklist", "items": ["Compare to prior shift report", "Focused systems per acuity", "Lines and drains", "Safety precautions", "Patient goals for shift"], "source": s},
        {"id": "chk-neuro", "title": "Neurological Serial Checklist", "items": ["GCS/LOC", "Pupils", "Motor/speech", "Headache/vomiting", "Notify threshold documented"], "source": s},
        {"id": "chk-respiratory", "title": "Respiratory Distress Checklist", "items": ["RR and effort", "SpO₂", "Lung sounds", "O₂ device and flow", "Positioning", "Notify provider criteria"], "source": s},
        {"id": "chk-gi", "title": "GI Assessment Checklist", "items": ["Bowel sounds", "Last BM", "Abdominal tenderness", "Nausea/vomiting", "NG tube placement verified"], "source": s},
        {"id": "chk-pain", "title": "Pain Reassessment Checklist", "items": ["Pain score before/after intervention", "Non-pharm and pharm measures", "Sedation/respiratory rate if opioids", "Patient goal for pain"], "source": s},
        {"id": "chk-discharge", "title": "Discharge Teaching Checklist", "items": ["Medications explained", "Follow-up appointments", "Red flags to report", "Teach-back completed", "Written instructions provided"], "source": s},
        {"id": "chk-pediatric", "title": "Pediatric Admission Checklist", "items": ["Weight in kg", "Immunization status", "Caregiver presence", "Developmental assessment", "Pain scale by age"], "source": s},
    ]
    soap_exercises = []
    soap_cases = [
        ("soap-01", "Dyspnea with Crackles", {"subjective": "Patient reports worsening shortness of breath x2 days, worse lying flat.", "objective": "RR 28, SpO₂ 89% RA, bilateral crackles bases, BP 158/92, HR 104.", "assessment": "Impaired gas exchange r/t pulmonary edema secondary to fluid overload.", "plan": "High Fowler's, O₂ 2L NC titrate, daily weight, I&O, notify provider, reassess SpO₂ q1h."}),
        ("soap-02", "Post-op Pain", {"subjective": "Patient rates incision pain 7/10, sharp, worse with movement.", "objective": "Abdominal incision clean/dry/intact, mild guarding, BP 118/76, HR 88.", "assessment": "Acute pain r/t surgical incision.", "plan": "Analgesic per order, reposition, splint incision, reassess pain 30 min post med."}),
        ("soap-03", "Confusion in Older Adult", {"subjective": "Family states patient more confused since last night.", "objective": "Oriented ×1 person only, temp 38.4°C, WBC elevated per chart.", "assessment": "Acute confusion r/t possible infection (UTI/pneumonia).", "plan": "Urinalysis and CXR per order, fall precautions, orient frequently, notify provider."}),
        ("soap-04", "Hypoglycemia", {"subjective": "Patient reports shakiness and sweating before lunch.", "objective": "Fingerstick 54 mg/dL, diaphoretic, alert but tremulous.", "assessment": "Risk for injury r/t hypoglycemia.", "plan": "15 g fast carb, recheck 15 min, notify provider if <70 persists, educate on s/s."}),
        ("soap-05", "Chest Pain", {"subjective": "Patient describes substernal pressure 8/10 started 30 min ago.", "objective": "Diaphoretic, BP 148/90, HR 96, 12-lead ST depression V4–V6 per monitor.", "assessment": "Acute pain r/t myocardial ischemia.", "plan": "Continuous monitoring, aspirin/nitro per protocol, IV access, notify provider, NPO."}),
        ("soap-06", "Fall with Head Strike", {"subjective": "Patient fell getting out of bed, hit head on floor.", "objective": "2 cm scalp laceration, GCS 14 (confused), pupils equal reactive.", "assessment": "Risk for injury r/t fall; altered LOC r/t head trauma.", "plan": "Neuro checks q15min, CT head per trauma protocol, wound care, fall precautions."}),
        ("soap-07", "UTI Symptoms", {"subjective": "Dysuria and urgency x3 days.", "objective": "Temp 37.9°C, suprapubic tenderness, urine cloudy and odorous.", "assessment": "Impaired urinary elimination r/t UTI.", "plan": "Urine culture, antibiotics per order, fluids, pain management, hygiene teaching."}),
        ("soap-08", "Anxiety Pre-Procedure", {"subjective": "Patient states 'I'm terrified something bad will happen' before colonoscopy.", "objective": "HR 108, BP 142/88, tremulous hands, tearful.", "assessment": "Anxiety r/t unfamiliar procedure.", "plan": "Therapeutic communication, explain steps, anxiolytic per order, NPO verified."}),
        ("soap-09", "Wound Infection", {"subjective": "Increased drainage and odor from surgical wound.", "objective": "Wound erythema 2 cm, purulent drainage, temp 38.1°C.", "assessment": "Risk for infection r/t surgical site.", "plan": "Wound culture, antibiotics per order, dressing change per protocol, notify surgeon."}),
        ("soap-10", "Hypertensive Urgency", {"subjective": "Headache 6/10, denies chest pain.", "objective": "BP 198/112, HR 82, neuro intact, lungs clear.", "assessment": "Ineffective health maintenance r/t uncontrolled hypertension.", "plan": "Recheck BP both arms, antihypertensive per order, neuro checks, notify provider, education."}),
    ]
    for sid, title, model in soap_cases:
        soap_exercises.append({
            "id": sid, "title": title,
            "chief_complaint": title,
            "findings": model,
            "model_soap": model,
            "documentation_tips": ["Separate subjective quotes from objective measurements", "Link assessment to NANDA-I style diagnosis", "Plan includes independent nursing actions and provider notification"],
            "source": s,
        })
    sbar_exercises = [
        {"id": "sbar-01", "title": "Rapid Response — Hypoxemia", "situation": "Mr. Lee, room 412, SpO₂ dropped to 84% on 2L NC.", "background": "Admitted 2 days ago for pneumonia, history COPD.", "assessment": "RR 32, accessory muscle use, diminished bases, anxious.", "recommendation": "Request provider evaluation, increase O₂ per protocol, possible transfer to higher acuity.", "source": s},
        {"id": "sbar-02", "title": "Handoff — New Confusion", "situation": "Mrs. Brown became acutely confused this shift.", "background": "88 y/o, hip repair yesterday, opioid analgesia.", "assessment": "Oriented ×1, new compared to morning, pupils equal, vitals stable.", "recommendation": "Suggest pain regimen review, UA, neuro checks q4h, fall precautions.", "source": s},
    ]
    assess_next_scenarios = []
    an_specs = [
        ("an-01", "New Tracheostomy", "You note thick secretions and decreased breath sounds right lung.", ["Suction tracheostomy per protocol", "Complete dressing change only", "Discharge teaching"], 0, "Airway patency first — suction when secretions impair ventilation."),
        ("an-02", "Chemotherapy Infusion", "Patient develops flushing, wheezing, BP 86/50 during infusion.", ["Stop infusion, notify provider, epinephrine per anaphylaxis protocol", "Slow infusion rate", "Apply warm blanket only"], 0, "Anaphylaxis — stop infusion and treat immediately."),
        ("an-03", "Diabetic Patient NPO", "Morning surgery — glucose 220 mg/dL.", ["Notify provider and verify insulin/IV fluid orders", "Give routine breakfast insulin", "Ignore — NPO covers it"], 0, "Perioperative glucose management requires provider orders."),
        ("an-04", "Post-op Day 1", "Patient has not voided 10 hours, bladder scan 450 mL.", ["Perform straight catheter per order", "Encourage more oral fluids only", "Wait until tomorrow"], 0, "Retention requires intervention to prevent AKI."),
        ("an-05", "Chest Tube", "Sudden increase in bright red drainage 200 mL/hr.", ["Notify provider immediately, vitals, monitor output", "Clamp chest tube", "Document and continue routine care"], 0, "Hemorrhage concern — notify provider, never clamp without order."),
    ]
    for i in range(16):
        if i < len(an_specs):
            aid, title, cue, opts, correct, expl = an_specs[i]
        else:
            aid, title = f"an-{i+1:02d}", f"Clinical Scenario {i+1}"
            cue = "Patient develops acute shortness of breath and SpO₂ 88%."
            opts = ["Assess airway and apply O₂ per protocol", "Complete scheduled bath", "Document and reassess next shift"]
            correct, expl = 0, "ABCs first — respiratory compromise takes priority."
        assess_next_scenarios.append({
            "id": aid, "title": title, "scenario": cue, "options": opts,
            "correct_index": correct, "explanation": expl,
            "clinical_why": "NCLEX prioritization: unstable before stable, acute before chronic.",
            "source": s,
        })
    practice_questions = []
    pq_specs = [
        ("aq-01", "Which finding requires immediate notification?", ["BP 142/88", "SpO₂ 88% with RR 32 and accessory use", "Pain 4/10", "Temp 37.2°C"], 1, "respiratory"),
        ("aq-02", "Best technique order for abdominal assessment?", ["Palpate then auscultate", "Auscultate then palpate", "Percuss then palpate only", "Inspect last"], 1, "gastrointestinal"),
        ("aq-03", "Orthostatic hypotension is defined as:", ["SBP drop ≥20 mmHg or DBP ≥10 mmHg with symptoms on standing", "Any BP change lying to standing", "HR increase only", "SBP increase 20 mmHg"], 0, "cardiovascular"),
        ("aq-04", "COPD patient O₂ target SpO₂ is typically:", ["100%", "88–92%", "70%", "95–100%"], 1, "respiratory"),
        ("aq-05", "FAST assessment includes:", ["Face, Arm, Speech, Time", "Fever, Airway, Skin, Temperature", "Fluid, Activity, Strength, Tone", "Focus, Assess, Support, Treat"], 0, "neurological"),
    ]
    for i in range(40):
        if i < len(pq_specs):
            pid, q, opts, correct, sys = pq_specs[i]
        else:
            pid, sys = f"aq-{i+1:02d}", "general"
            q = f"Priority question {i+1}: Which action should the nurse take first for an unstable finding?"
            opts = ["Assess ABCs and notify provider for acute change", "Complete routine paperwork", "Reassess at end of shift", "Delegate to unlicensed assistive personnel"]
            correct = 0
        practice_questions.append(mcq(pid, q, opts, correct, "Prioritize airway, breathing, circulation, and acute changes.", system=sys, source_key="assessment"))
    flashcards = _generate_flashcards(body_systems)
    return {
        "module_id": "assessment",
        "title": "NURS 146 — Health Assessment",
        "head_to_toe_sequence": head_to_toe_sequence,
        "body_systems": body_systems,
        "red_flags_master": red_flags_master,
        "vital_signs": {
            "adult_norms": {"temp": "97.8–99°F (36.5–37.2°C)", "hr": "60–100 bpm", "rr": "12–20/min", "bp": "~120/80 mmHg (varies)", "spo2": "≥94% on room air"},
            "pediatric_note": "Pediatric norms vary by age — always use age-specific charts.",
            "orthostatic_criteria": "SBP decrease ≥20 mmHg or DBP ≥10 mmHg within 3 min of standing with symptoms.",
            "source": s,
        },
        "pain_assessment": {
            "scales": ["0–10 numeric (adults)", "FACES (pediatric)", "FLACC (infants)", "PQRST interview"],
            "nursing_priority": "Assess respiratory rate and sedation before additional opioids.",
            "source": s,
        },
        "skills": skills,
        "interview_techniques": interview_techniques,
        "special_populations": special_populations,
        "assessment_checklists": assessment_checklists,
        "soap_exercises": soap_exercises,
        "sbar_exercises": sbar_exercises,
        "assess_next_scenarios": assess_next_scenarios,
        "flashcards": flashcards,
        "practice_questions": practice_questions,
        "source": s,
    }