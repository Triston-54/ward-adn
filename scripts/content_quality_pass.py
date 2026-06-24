#!/usr/bin/env python3
"""Content quality pass — expand rationales, fix scaffold duplicates, add clinical_why."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data" / "content"
SOURCE = {
    "title": "Open RN — Health Assessment",
    "citation": "Open RN OER Assessment Techniques",
    "verified_date": "2026-06",
}
MC_SOURCE = {
    "title": "Open RN — Maternal-Newborn Nursing",
    "citation": "Open RN OER — Maternal-Newborn; NCSBN Health Promotion",
    "verified_date": "2026-06",
}

# --- Assessment: fix aq-01..05 rationales ---
ASSESSMENT_FIRST_FIVE = {
    "aq-01": {
        "explanation": "SpO₂ 88% with tachypnea and accessory muscle use signals respiratory compromise — assess airway, position for breathing, apply O₂ per protocol, and notify the provider immediately.",
        "clinical_why": "Hypoxemia with increased work of breathing is an ABC priority that can progress to respiratory failure within minutes.",
    },
    "aq-02": {
        "explanation": "Inspect, auscultate, percuss, then palpate (IAPPA). Auscultate bowel sounds before palpation so palpation does not alter sound quality.",
        "clinical_why": "Altered bowel sounds from palpation can mask true peristaltic activity and delay recognition of ileus or obstruction.",
    },
    "aq-03": {
        "explanation": "Orthostatic hypotension is defined as a drop in SBP ≥20 mmHg or DBP ≥10 mmHg within 3 minutes of standing, often with dizziness or syncope.",
        "clinical_why": "Orthostatic changes identify volume depletion, autonomic dysfunction, and fall risk — especially in older adults on antihypertensives.",
    },
    "aq-04": {
        "explanation": "Chronic CO₂ retainers depend on hypoxic drive; target SpO₂ 88–92% to avoid suppressing ventilation and causing CO₂ narcosis.",
        "clinical_why": "Over-oxygenating COPD patients can precipitate respiratory acidosis, somnolence, and need for mechanical ventilation.",
    },
    "aq-05": {
        "explanation": "FAST (Face drooping, Arm weakness, Speech difficulty, Time to call) is a community and bedside stroke screening tool — time last known well is critical for thrombolytic eligibility.",
        "clinical_why": "Every minute of untreated stroke loses ~1.9 million neurons; rapid recognition drives door-to-needle times.",
    },
}

# --- Assessment: replace scaffold aq-06..40 ---
ASSESSMENT_REPLACEMENTS = [
    {
        "id": "aq-06",
        "question": "During head-to-toe assessment, which sequence is correct?",
        "options": ["Head-to-toe general survey, then focused systems", "Random order by patient preference", "Pain assessment last only", "Vitals after discharge teaching"],
        "correct_index": 0,
        "explanation": "Begin with a general survey (appearance, ABCs), then proceed systematically head-to-toe or by priority when instability is present.",
        "clinical_why": "A structured sequence ensures no system is skipped and unstable findings are caught early.",
        "system": "general",
    },
    {
        "id": "aq-07",
        "question": "A patient has unequal pupils with a fixed dilated right pupil after head trauma. Priority action?",
        "options": ["Notify provider immediately; continue neuro checks", "Document and recheck next shift", "Apply warm compress to eye", "Dim lights and discharge"],
        "correct_index": 0,
        "explanation": "Unilateral fixed dilated pupil (blown pupil) after trauma suggests expanding intracranial pressure or herniation — escalate immediately.",
        "clinical_why": "Pupil changes may be the earliest sign of uncal herniation before altered LOC.",
        "system": "neurological",
    },
    {
        "id": "aq-08",
        "question": "When auscultating heart sounds, the nurse should:",
        "options": ["Use the diaphragm at four primary valve areas with patient supine and left lateral", "Auscultate only over the apex", "Use bell only at the carotid", "Skip auscultation if pulse is regular"],
        "correct_index": 0,
        "explanation": "Systematic auscultation at aortic, pulmonic, tricuspid, and mitral areas (and Erb's point) with appropriate patient positions improves murmur detection.",
        "clinical_why": "Murmurs and extra heart sounds are location-specific; incomplete auscultation misses valvular pathology.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-09",
        "question": "Crackles heard on lung auscultation most often indicate:",
        "options": ["Fluid in alveoli or small airways", "Large airway obstruction only", "Pneumothorax", "Normal finding in all adults"],
        "correct_index": 0,
        "explanation": "Fine crackles (rales) suggest alveolar fluid — CHF, pneumonia, or atelectasis; assess O₂ saturation and work of breathing.",
        "clinical_why": "Crackles plus hypoxemia may signal pulmonary edema requiring diuretics and O₂ before cardiac arrest.",
        "system": "respiratory",
    },
    {
        "id": "aq-10",
        "question": "The best pain assessment approach for a nonverbal intubated ICU patient is:",
        "options": ["Behavioral scale (CPOT or BPS)", "Assume no pain if patient cannot speak", "Numeric 0–10 scale only", "Wait until extubation"],
        "correct_index": 0,
        "explanation": "Critical-Care Pain Observation Tool (CPOT) and Behavioral Pain Scale use facial expression, body movement, and ventilator compliance.",
        "clinical_why": "Untreated pain increases sympathetic drive, delirium, and ventilator days in ICU patients.",
        "system": "general",
    },
    {
        "id": "aq-11",
        "question": "Capillary refill >3 seconds in an adult with cool extremities suggests:",
        "options": ["Decreased peripheral perfusion", "Normal variant", "Hypervolemia", "Fever response"],
        "correct_index": 0,
        "explanation": "Delayed cap refill with cool skin indicates poor peripheral perfusion — shock, dehydration, or peripheral vascular disease.",
        "clinical_why": "Perfusion assessment complements vital signs when hypotension is not yet present.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-12",
        "question": "Pitting edema rated 3+ means:",
        "options": ["Indentation 4–6 mm, rebounds in 10–30 seconds", "No indentation", "Indentation 2 mm only", "Non-pitting hard swelling"],
        "correct_index": 0,
        "explanation": "3+ pitting is moderate — 4–6 mm depth; 4+ is severe (>6 mm, >30 sec rebound). Document location and bilateral comparison.",
        "clinical_why": "Quantified edema tracks fluid overload in heart failure, renal disease, and liver failure.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-13",
        "question": "A Glasgow Coma Scale score of 8 indicates:",
        "options": ["Severe brain injury — airway protection priority", "Mild concussion", "Normal alert state", "Moderate injury only"],
        "correct_index": 0,
        "explanation": "GCS ≤8 is severe TBI — intubation may be needed to protect airway; trend GCS q1h or per protocol.",
        "clinical_why": "Declining GCS by ≥2 points warrants repeat imaging and neurosurgical consult.",
        "system": "neurological",
    },
    {
        "id": "aq-14",
        "question": "When assessing jugular venous distension (JVD), the nurse should:",
        "options": ["Elevate HOB 30–45° and measure vertical distance above sternal angle", "Assess with patient flat only", "Press firmly over carotid", "Ignore if BP normal"],
        "correct_index": 0,
        "explanation": "JVD >3–4 cm above sternal angle at 45° suggests increased central venous pressure — right heart failure or fluid overload.",
        "clinical_why": "JVD distinguishes right-sided heart failure from isolated peripheral edema.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-15",
        "question": "Bowel sounds absent for 5 minutes in a post-op abdomen may indicate:",
        "options": ["Ileus or obstruction — correlate with nausea, distension, flatus", "Always normal after surgery", "Diarrhea", "Appendicitis only"],
        "correct_index": 0,
        "explanation": "Absent sounds plus distension, pain, or no flatus warrant provider notification; post-op ileus is common but must be monitored.",
        "clinical_why": "Complete obstruction or paralytic ileus can cause bowel ischemia and perforation if unrecognized.",
        "system": "gastrointestinal",
    },
    {
        "id": "aq-16",
        "question": "The correct technique for palpating the thyroid is:",
        "options": ["Stand behind patient, displace trachea, palpate lobes during swallow", "Palpate only from anterior without swallow", "Auscultate thyroid for bruits first always", "Skip if patient has no symptoms"],
        "correct_index": 0,
        "explanation": "Posterior approach with swallowing helps distinguish thyroid nodules from other neck masses.",
        "clinical_why": "Thyromegaly, nodules, and tenderness guide hyper/hypothyroid and thyroiditis workup.",
        "system": "endocrine",
    },
    {
        "id": "aq-17",
        "question": "A positive Homans sign (calf pain on dorsiflexion) is:",
        "options": ["Not reliable alone for DVT — use Wells criteria and ultrasound", "Definitive DVT diagnosis", "Normal in all post-op patients", "Contraindication to ambulation"],
        "correct_index": 0,
        "explanation": "Homans sign has low sensitivity and specificity; assess unilateral swelling, warmth, Homan's only as one cue.",
        "clinical_why": "Missed DVT leads to pulmonary embolism — the leading preventable cause of hospital death.",
        "system": "musculoskeletal",
    },
    {
        "id": "aq-18",
        "question": "When assessing skin turgor in an older adult, the nurse knows:",
        "options": ["Turgor is less reliable — check mucous membranes and axillae", "Turgor always accurate", "Pinch forehead only", "Turgor replaces I&O"],
        "correct_index": 0,
        "explanation": "Aging reduces skin elasticity; assess tongue, mucosa, and recent weight/I&O for hydration in elders.",
        "clinical_why": "Dehydration in older adults causes confusion, orthostasis, and AKI.",
        "system": "integumentary",
    },
    {
        "id": "aq-19",
        "question": "Korotkoff phase V (disappearance of sound) is used for:",
        "options": ["Diastolic blood pressure in adults", "Systolic only", "Pediatric BP always", "MAP calculation only"],
        "correct_index": 0,
        "explanation": "In adults, diastolic is the point sounds disappear (phase V); in children, phase IV (muffling) may be used per policy.",
        "clinical_why": "Consistent technique prevents false hypertension diagnosis and unnecessary treatment.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-20",
        "question": "The most accurate core temperature route in critical care is:",
        "options": ["Pulmonary artery or urinary bladder (continuous)", "Tympanic after exercise", "Axillary after cold drink", "Forehead scanner only"],
        "correct_index": 0,
        "explanation": "Core temps reflect hypothalamic set point; pulmonary artery is gold standard; bladder acceptable with good urine flow.",
        "clinical_why": "Fever in neutropenia or post-op sepsis requires accurate trending for antibiotic timing.",
        "system": "general",
    },
    {
        "id": "aq-21",
        "question": "During abdominal palpation, the nurse should:",
        "options": ["Start light palpation away from painful quadrant, then deep if tolerated", "Deep palpate painful area first", "Skip palpation if patient ate", "Use one finger maximum pressure always"],
        "correct_index": 0,
        "explanation": "Light palpation first; guard against pain by starting away from tenderness; note rebound and rigidity as peritoneal signs.",
        "clinical_why": "Rebound tenderness and rigidity suggest surgical abdomen — NPO and surgical consult.",
        "system": "gastrointestinal",
    },
    {
        "id": "aq-22",
        "question": "A patient with new unilateral leg swelling and erythema — priority assessment includes:",
        "options": ["Measure calf circumference, pulse, cap refill, and pain", "Apply heat and massage", "Ignore if ambulating", "Discharge with NSAIDs only"],
        "correct_index": 0,
        "explanation": "Unilateral swelling suggests DVT, cellulitis, or compartment syndrome — compare limbs and check pulses.",
        "clinical_why": "DVT prophylaxis failure and PE risk require prompt diagnostic imaging.",
        "system": "musculoskeletal",
    },
    {
        "id": "aq-23",
        "question": "When using the ophthalmoscope, the nurse assesses:",
        "options": ["Red reflex, optic disc, vessels, and macula", "Tympanic membrane", "Nasal turbinates", "Carotid bruit"],
        "correct_index": 0,
        "explanation": "Fundoscopic exam detects papilledema, hemorrhages, and diabetic retinopathy changes.",
        "clinical_why": "Papilledema indicates increased ICP — pair with headache and neuro exam.",
        "system": "neurological",
    },
    {
        "id": "aq-24",
        "question": "The Weber test lateralizes sound to the deaf ear in:",
        "options": ["Conductive hearing loss", "Sensorineural loss only", "Normal hearing", "Bilateral deafness always"],
        "correct_index": 0,
        "explanation": "Weber: conductive loss lateralizes to affected ear; sensorineural lateralizes to better ear.",
        "clinical_why": "Differentiating conductive vs sensorineural loss guides cerumen impaction vs acoustic neuroma workup.",
        "system": "neurological",
    },
    {
        "id": "aq-25",
        "question": "A respiratory rate of 28 with shallow breathing and use of accessory muscles indicates:",
        "options": ["Increased work of breathing — assess SpO₂ and airway", "Normal anxiety only", "Bradypnea", "Hyperventilation always alkalotic"],
        "correct_index": 0,
        "explanation": "Tachypnea with accessory use signals respiratory distress — position upright, assess patency, apply O₂, prepare for escalation.",
        "clinical_why": "Fatigue from increased work leads to CO₂ retention and respiratory arrest.",
        "system": "respiratory",
    },
    {
        "id": "aq-26",
        "question": "When assessing an older adult's cognition, the nurse should:",
        "options": ["Use validated screen (Mini-Cog, MMSE) and compare baseline", "Assume confusion is normal aging", "Skip if family present", "Test only at discharge"],
        "correct_index": 0,
        "explanation": "Acute confusion differs from dementia — screen for delirium triggers: infection, meds, hypoxia, pain, constipation.",
        "clinical_why": "Delirium increases falls, length of stay, and mortality — treat cause, not only symptom.",
        "system": "neurological",
    },
    {
        "id": "aq-27",
        "question": "Pediatric apical pulse is best counted:",
        "options": ["At apex with stethoscope for full 60 seconds (1 min)", "Radial for 15 seconds ×4", "Carotid during crying", "Femoral only"],
        "correct_index": 0,
        "explanation": "Apical count for full minute in infants/children — radial is inaccurate with tachycardia and arrhythmias.",
        "clinical_why": "Undetected tachycardia in dehydration or fever can precede shock in infants.",
        "system": "pediatric",
    },
    {
        "id": "aq-28",
        "question": "A Braden score of 14 indicates:",
        "options": ["Moderate pressure injury risk — implement turning schedule", "No risk", "Only nutrition problem", "Risk only if incontinent"],
        "correct_index": 0,
        "explanation": "Braden ≤18 is at risk; 15–18 mild, 13–14 moderate, 10–12 high, ≤9 very high — initiate prevention bundle.",
        "clinical_why": "Hospital-acquired pressure injuries are largely preventable with repositioning and moisture management.",
        "system": "integumentary",
    },
    {
        "id": "aq-29",
        "question": "During breast examination, the nurse teaches:",
        "options": ["Monthly self-exam after menses; report new lumps, discharge, skin changes", "No self-exam needed", "Exam only if family history", "Mammogram replaces clinical exam"],
        "correct_index": 0,
        "explanation": "Clinical breast exam complements mammography; teach BSE timing and what changes to report.",
        "clinical_why": "Early breast cancer detection improves survival — patient education extends assessment beyond the hospital.",
        "system": "general",
    },
    {
        "id": "aq-30",
        "question": "When documenting assessment findings, the nurse should:",
        "options": ["Record objective data separately from subjective quotes", "Chart only abnormal findings", "Use vague terms like 'good' without specifics", "Document before assessment"],
        "correct_index": 0,
        "explanation": "Objective (measurable) vs subjective (patient report) supports legal defensibility and care continuity.",
        "clinical_why": "Accurate documentation is communication — vague notes delay treatment and increase liability.",
        "system": "general",
    },
    {
        "id": "aq-31",
        "question": "A patient reports chest pain 8/10. Before giving nitroglycerin, the nurse assesses:",
        "options": ["Blood pressure and recent PDE-5 inhibitor use", "Bowel sounds only", "Deep tendon reflexes", "Gag reflex only"],
        "correct_index": 0,
        "explanation": "Nitroglycerin contraindicated if SBP <90 or sildenafil/tadalafil within 24–48 hr — can cause severe hypotension.",
        "clinical_why": "ACS assessment includes 12-lead ECG, aspirin per protocol, and serial troponins — not pain med alone.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-32",
        "question": "The nurse hears a systolic murmur loudest at the apex radiating to the axilla. This suggests:",
        "options": ["Mitral regurgitation", "Aortic stenosis only", "Normal physiologic murmur always", "Tricuspid stenosis only"],
        "correct_index": 0,
        "explanation": "Mitral regurgitation: holosystolic murmur at apex → axilla; assess for CHF symptoms and history of rheumatic fever.",
        "clinical_why": "New murmur with fever may indicate endocarditis — blood cultures before antibiotics.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-33",
        "question": "When assessing peripheral pulses, absent dorsalis pedis bilaterally with cool feet requires:",
        "options": ["Compare to baseline, check cap refill, notify if acute change", "Immediate amputation prep", "Ignore if posterior tibial present", "Heat packs only"],
        "correct_index": 0,
        "explanation": "Absent DP pulses may be chronic (PVD) or acute (embolus) — compare sides, skin color, temperature, pain.",
        "clinical_why": "Acute limb ischemia (6 P's) is a surgical emergency within 6 hours.",
        "system": "cardiovascular",
    },
    {
        "id": "aq-34",
        "question": "A patient with COPD has barrel chest and prolonged expiration. The nurse expects:",
        "options": ["Decreased breath sounds and pursed-lip breathing", "Kussmaul respirations", "Stridor at rest normally", "Crackles only on expiration never"],
        "correct_index": 0,
        "explanation": "COPD hyperinflation causes barrel chest, wheezes, diminished air movement, and pursed-lip breathing to prolong expiratory phase.",
        "clinical_why": "Baseline differs from acute exacerbation — sudden change in sputum or SpO₂ needs treatment escalation.",
        "system": "respiratory",
    },
    {
        "id": "aq-35",
        "question": "During mental status exam, the nurse assesses orientation by asking:",
        "options": ["Person, place, time, and situation", "Only name", "Medication names only", "Insurance provider"],
        "correct_index": 0,
        "explanation": "Orientation ×4 is standard; also assess attention, memory, mood, and thought content.",
        "clinical_why": "Acute disorientation suggests delirium, stroke, hypoglycemia, or hypoxia — not always dementia.",
        "system": "neurological",
    },
    {
        "id": "aq-36",
        "question": "The nurse notes clubbing of fingers. This is associated with:",
        "options": ["Chronic hypoxemia (COPD, CF, lung cancer)", "Acute allergic reaction", "Hypoglycemia", "UTI"],
        "correct_index": 0,
        "explanation": "Digital clubbing (increased nail angle) develops over months with chronic hypoxia or inflammatory conditions.",
        "clinical_why": "New clubbing warrants chest imaging — may be first sign of lung malignancy.",
        "system": "respiratory",
    },
    {
        "id": "aq-37",
        "question": "When measuring a wound, the nurse documents:",
        "options": ["Length × width × depth, tunneling, odor, drainage type", "Only 'small wound'", "Color of patient gown", "Dressing brand only"],
        "correct_index": 0,
        "explanation": "Standard wound measurement in cm; note undermining, sinus tracts, periwound skin, and infection signs.",
        "clinical_why": "Trending wound size guides dressing selection and surgical vs conservative management.",
        "system": "integumentary",
    },
    {
        "id": "aq-38",
        "question": "A pregnant patient at 28 weeks — appropriate fundal height expectation is:",
        "options": ["Approximately 28 cm (±2–3 cm) from symphysis to fundus", "Always 10 cm", "Fundal height not measured", "50 cm standard"],
        "correct_index": 0,
        "explanation": "After 20 weeks, fundal height in cm roughly equals gestational age — discrepancy suggests IUGR, twins, or polyhydramnios.",
        "clinical_why": "Fundal height discordance triggers ultrasound for fetal growth assessment.",
        "system": "obstetric",
    },
    {
        "id": "aq-39",
        "question": "The nurse performing a focused musculoskeletal exam after fall assesses:",
        "options": ["Range of motion, strength, alignment, and neurovascular status distal to injury", "Only ask if pain present", "X-ray before any touch", "Heat to joint immediately"],
        "correct_index": 0,
        "explanation": "Compare bilateral limbs; check pulses, sensation, movement before and after splinting.",
        "clinical_why": "Compartment syndrome and neurovascular compromise are time-sensitive complications of fractures.",
        "system": "musculoskeletal",
    },
    {
        "id": "aq-40",
        "question": "Which finding during shift handoff requires the receiving nurse to assess first?",
        "options": ["New oxygen requirement with SpO₂ 90% on room air", "Scheduled bath at 1400", "Discharge paperwork pending", "Visitor waiting in lobby"],
        "correct_index": 0,
        "explanation": "Handoff prioritization follows ABCs — new hypoxemia indicates potential deterioration requiring immediate assessment.",
        "clinical_why": "SBAR handoff must highlight unstable trends so the oncoming nurse can intervene before decompensation.",
        "system": "general",
    },
]

# --- Maternal-child replacements mc-q11..21 ---
MATERNAL_CHILD_REPLACEMENTS = [
    {
        "id": "mc-q11",
        "question": "Variable decelerations on FHR tracing — first nursing action?",
        "options": ["Change maternal position, stop oxytocin if running, O₂, IV fluid bolus if ordered", "Immediate cesarean without assessment", "Turn off monitor", "Increase oxytocin"],
        "correct_index": 0,
        "explanation": "Variable decels suggest cord compression — intrauterine resuscitation: position change (side-lying), O₂, fluids, amnioinfusion if ordered.",
        "clinical_why": "Repetitive severe variables with late decels indicate nonreassuring tracing requiring provider escalation.",
    },
    {
        "id": "mc-q12",
        "question": "Eclamptic seizure in labor — priority after ensuring safety?",
        "options": ["Magnesium sulfate per protocol and notify provider", "Phenobarbital first line always", "Immediate delivery without stabilization", "Hold all medications"],
        "correct_index": 0,
        "explanation": "Magnesium sulfate is anticonvulsant of choice in eclampsia — monitor RR, reflexes, urine output for toxicity.",
        "clinical_why": "Recurrent seizures cause maternal hypoxia and fetal bradycardia — magnesium prevents recurrence.",
    },
    {
        "id": "mc-q13",
        "question": "Placenta previa is suspected when a pregnant patient has:",
        "options": ["Painless bright red bleeding in third trimester", "Painful rigid abdomen with bleeding", "Foul lochia only", "No bleeding ever"],
        "correct_index": 0,
        "explanation": "Placenta previa: painless bleeding — no vaginal exams; ultrasound confirms; prepare for cesarean if complete previa.",
        "clinical_why": "Digital cervical exam can cause catastrophic hemorrhage in previa.",
    },
    {
        "id": "mc-q14",
        "question": "A newborn has acrocyanosis (blue hands/feet) with pink trunk. The nurse:",
        "options": ["Documents as common transitional finding if breathing and tone normal", "Starts chest compressions", "Applies heat lamp to trunk only", "Discharges immediately"],
        "correct_index": 0,
        "explanation": "Acrocyanosis is normal transition in first hours — assess respiratory effort, heart rate, and central color.",
        "clinical_why": "Central cyanosis (trunk/mucosa) is abnormal and requires immediate intervention.",
    },
    {
        "id": "mc-q15",
        "question": "Breastfeeding mother reports cracked nipples and engorgement on day 3. Best teaching?",
        "options": ["Ensure deep latch, frequent feeding, hand express for relief", "Stop breastfeeding permanently", "Use bottle exclusively", "Apply ice only between all feeds"],
        "correct_index": 0,
        "explanation": "Latch correction prevents further trauma; frequent emptying reduces engorgement; lanolin or breast milk on nipples.",
        "clinical_why": "Poor latch leads to mastitis, inadequate infant intake, and early weaning.",
    },
    {
        "id": "mc-q16",
        "question": "A 2-month-old receives first routine vaccines per CDC schedule. The nurse documents:",
        "options": ["Lot number, site, route, VIS date, patient reaction", "Only 'vaccines given'", "No documentation needed", "Parent refusal without discussion"],
        "correct_index": 0,
        "explanation": "Document each vaccine with lot, expiration, site (vastus lateralis IM for infants), and Vaccine Information Statement provided.",
        "clinical_why": "Accurate immunization records prevent duplicate doses and support public health tracking.",
    },
    {
        "id": "mc-q17",
        "question": "Postpartum patient with foul-smelling lochia, temp 38.5°C, uterine tenderness — suspect:",
        "options": ["Endometritis — notify provider, cultures, antibiotics per order", "Normal lochia", "Breast engorgement only", "Urinary retention only"],
        "correct_index": 0,
        "explanation": "Endometritis: fever, fundal tenderness, foul lochia — usually after cesarean or prolonged labor; broad-spectrum antibiotics.",
        "clinical_why": "Untreated endometritis progresses to sepsis — early recognition reduces ICU admission.",
    },
    {
        "id": "mc-q18",
        "question": "Toddler (18 months) developmental milestone expected:",
        "options": ["Walks independently, 10–25 word vocabulary", "Rides bicycle", "Reads sentences", "Full toilet training always complete"],
        "correct_index": 0,
        "explanation": "18-month toddler walks well, may run, uses simple words, feeds self — assess safety (gates, poison control).",
        "clinical_why": "Delayed walking or speech warrants early intervention referral.",
    },
    {
        "id": "mc-q19",
        "question": "Gestational diabetes screening with 1-hour glucose challenge 165 mg/dL — next step?",
        "options": ["3-hour oral glucose tolerance test per protocol", "Diagnose GDM immediately", "No follow-up needed", "Start insulin today"],
        "correct_index": 0,
        "explanation": "Abnormal 50-g screen (typically ≥140 mg/dL) requires 100-g 3-hour OGTT for GDM diagnosis.",
        "clinical_why": "Untreated GDM increases macrosomia, shoulder dystocia, and neonatal hypoglycemia risk.",
    },
    {
        "id": "mc-q20",
        "question": "Newborn of mother with active genital HSV lesions at delivery requires:",
        "options": ["Cesarean delivery to reduce neonatal herpes transmission", "Vaginal delivery always", "No precautions", "Hepatitis B vaccine only"],
        "correct_index": 0,
        "explanation": "Active genital HSV at delivery — cesarean recommended; neonatal herpes has high mortality even with treatment.",
        "clinical_why": "Neonatal herpes causes encephalitis — prevention is critical when lesions present.",
    },
    {
        "id": "mc-q21",
        "question": "A school-age child with asthma reports daily symptoms and nighttime cough twice weekly. Classification is:",
        "options": ["Moderate persistent — step-up therapy per NAEPP guidelines", "Mild intermittent", "No asthma", "Exercise-induced only"],
        "correct_index": 0,
        "explanation": "Moderate persistent: daily symptoms, nighttime >1×/week but not nightly, FEV1 60–80% — needs daily controller.",
        "clinical_why": "Under-treated persistent asthma causes missed school and status asthmaticus.",
    },
]

MATERNAL_CHILD_FIRST_TEN = {
    "mc-q01": {
        "explanation": "Late decelerations are uniform, gradual decreases below baseline after contraction peak — uteroplacental insufficiency. Stop oxytocin, left lateral position, O₂, IV fluids, notify provider.",
        "clinical_why": "Persistent late decels with absent variability require fetal scalp stimulation or scalp pH/lactate and possible expedited delivery.",
    },
    "mc-q02": {
        "explanation": "Boggy uterus indicates atony — massage fundus firmly until firm, then assess lochia and VS. Prepare uterotonics (oxytocin, methylergonovine, carboprost) per order.",
        "clinical_why": "Postpartum hemorrhage from atony is leading cause of maternal mortality — first minutes determine blood loss.",
    },
    "mc-q03": {
        "explanation": "Severe preeclampsia features: BP ≥160/110, platelets <100k, creatinine >1.1, pulmonary edema, RUQ/epigastric pain (liver capsule distension), cerebral symptoms.",
        "clinical_why": "RUQ pain may signal HELLP syndrome — hepatic rupture and DIC risk require magnesium and delivery planning.",
    },
    "mc-q04": {
        "explanation": "McRoberts (hyperflex hips) and suprapubic pressure free the anterior shoulder; fundal pressure worsens impaction and is contraindicated.",
        "clinical_why": "Shoulder dystocia causes brachial plexus injury and asphyxia — mnemonic HELPERR guides sequential maneuvers.",
    },
    "mc-q05": {
        "explanation": "APGAR 4 at 1 minute indicates moderate depression — continue PPV, stimulation, and NRP algorithm; reassess at 5 and 10 minutes.",
        "clinical_why": "Low 5-minute APGAR correlates with neonatal encephalopathy — document interventions for NICU handoff.",
    },
    "mc-q06": {
        "explanation": "Magnesium toxicity: absent DTRs (first sign), RR <12, urine output <30 mL/hr, flushing — stop Mg, give calcium gluconate, support respirations.",
        "clinical_why": "Magnesium is antidote for eclampsia but narrow margin — therapeutic level 4–7 mEq/L; >10 can arrest breathing.",
    },
    "mc-q07": {
        "explanation": "Fever ≥38°C (100.4°F) in infant ≤28 days requires full sepsis workup: blood culture, UA/UCx, LP, empiric IV antibiotics — never outpatient management alone.",
        "clinical_why": "Neonatal sepsis progresses rapidly — E. coli and GBS are common pathogens with high mortality if delayed.",
    },
    "mc-q08": {
        "explanation": "Cord prolapse: call for help, knee-chest or exaggerated Trendelenburg, elevate presenting part off cord with sterile gloved hand, O₂, prepare emergency cesarean.",
        "clinical_why": "Fetal bradycardia from cord compression causes hypoxic-ischemic injury within minutes.",
    },
    "mc-q09": {
        "explanation": "Physiologic jaundice peaks days 2–3 in term infants from immature hepatic conjugation; pathologic if <24 hr, rapid rise, or bilirubin crosses exchange transfusion thresholds.",
        "clinical_why": "Kernicterus from untreated hyperbilirubinemia causes permanent neurologic damage.",
    },
    "mc-q10": {
        "explanation": "Postpartum psychosis (days to 4 weeks): delusions, hallucinations, bizarre behavior — psychiatric emergency; never leave mother alone with infant.",
        "clinical_why": "Infanticide and suicide risk are elevated — inpatient psychiatric care with infant safety planning.",
    },
}

MED_SURG_RATIONALES = {
    "ms-q1": {
        "rationale": "Left-sided HF reduces LV output, causing blood to back up into pulmonary circulation — crackles, orthopnea, pink frothy sputum, and S₃ gallop. JVD and peripheral edema suggest right-sided failure.",
        "clinical_why": "Differentiating left vs right HF guides diuretic use, positioning (high Fowler's), and monitoring (daily weights, I&O).",
    },
    "ms-q2": {
        "rationale": "COPD patients are chronic CO₂ retainers; hypoxic drive maintains ventilation. Target SpO₂ 88–92% to prevent CO₂ narcosis while treating exacerbation.",
        "clinical_why": "Titrate O₂ to lowest saturation meeting target — ABG confirms pH and PaCO₂ trends.",
    },
    "ms-q3": {
        "rationale": "Stroke protocol: establish last known well, ABCs, IV access, blood glucose (hypoglycemia mimics stroke), CT head, then consider tPA if ischemic and within window.",
        "clinical_why": "Giving tPA before ruling out hemorrhage or hypoglycemia causes catastrophic harm.",
    },
    "ms-q4": {
        "rationale": "Hepatic encephalopathy from ammonia accumulation — lactulose acidifies colon, traps ammonia, increases bowel movements. Protein restriction is temporary, not permanent.",
        "clinical_why": "Asterixis and confusion can progress to coma — monitor mental status and hold sedatives that worsen encephalopathy.",
    },
    "ms-q5": {
        "rationale": "Severe hyperkalemia (K⁺ >6.5 with ECG changes): calcium gluconate IV first to stabilize myocardium — does not lower K⁺ but protects against arrhythmia while insulin/D50, kayexalate, or dialysis are prepared.",
        "clinical_why": "Peaked T waves progress to widened QRS and sine wave arrest — continuous tele required.",
    },
    "ms-q6": {
        "rationale": "Conscious hypoglycemia (Rule of 15): 15 g fast carbohydrate (4 oz juice, glucose tabs), recheck in 15 min, repeat if still <70; glucagon or IV dextrose if unable to swallow.",
        "clinical_why": "Never give insulin to hypoglycemic patient — seizure and death risk within minutes.",
    },
    "ms-q7": {
        "rationale": "Sudden SOB and tachycardia after orthopedic surgery suggests pulmonary embolism — immobilization and hypercoagulability. Assess SpO₂, prepare heparin/CT angiography per order.",
        "clinical_why": "PE is a leading cause of post-op death — don't attribute SOB to pain alone.",
    },
    "ms-q8": {
        "rationale": "Febrile neutropenia (ANC <500 with temp ≥38.3°C): medical emergency — blood cultures ×2, broad-spectrum antibiotics within 1 hour, avoid rectal temps and fresh flowers.",
        "clinical_why": "Neutropenic patients lack inflammatory response — fever may be only sign of sepsis.",
    },
    "ms-q9": {
        "rationale": "Prioritize unstable over stable: new dyspnea with SpO₂ 89% in CHF patient risks respiratory failure; post-op pain 5/10 and routine tasks can wait.",
        "clinical_why": "NCLEX and clinical practice use ABCs and acute vs chronic/unstable vs stable frameworks.",
    },
    "ms-q10": {
        "rationale": "DKA: total body K⁺ depleted despite serum level — insulin drives K⁺ intracellularly. Replace K⁺ to ≥3.3 mEq/L before insulin infusion to prevent life-threatening hypokalemia.",
        "clinical_why": "Insulin without K⁺ replacement can cause cardiac arrest from hypokalemia.",
    },
    "ms-q11": {
        "rationale": "Compartment syndrome: pain out of proportion, pain with passive stretch of toes, paresthesia, pallor, pulselessness (late). Elevate cast to heart level, bivalve cast, notify surgeon immediately.",
        "clinical_why": "Fasciotomy within 6 hours prevents permanent nerve and muscle necrosis.",
    },
    "ms-q12": {
        "rationale": "Warfarin inhibits vitamin K-dependent clotting factors — consistent dietary vitamin K prevents INR swings; teach bleeding precautions and avoid NSAIDs without provider approval.",
        "clinical_why": "Supratherapeutic INR causes GI and intracranial bleeding — subtherapeutic INR fails anticoagulation.",
    },
    "ms-q13": {
        "rationale": "Silent chest in asthma means minimal air movement despite obstruction — exhaustion and impending respiratory failure, not improvement. Prepare epinephrine, assisted ventilation.",
        "clinical_why": "Wheezing may decrease as patient fatigues — worsening obstruction, not resolution.",
    },
    "ms-q14": {
        "rationale": "Autonomic dysreflexia (T6 and above): pounding headache, hypertension, bradycardia — sit upright, loosen constrictive clothing, identify trigger (full bladder, fecal impaction), notify provider.",
        "clinical_why": "BP can exceed 300 mmHg causing stroke — never place flat (increases cerebral perfusion pressure).",
    },
    "ms-q15": {
        "rationale": "Acute pancreatitis: NPO to rest pancreas, aggressive IV fluids (third-spacing), pain control, monitor for ARDS and hypocalcemia. Oral intake resumes when lipase trends down and pain resolves.",
        "clinical_why": "Early feeding in severe pancreatitis can worsen inflammation — follow enteral protocol when stable.",
    },
    "ms-q16": {
        "rationale": "Hemodialysis fistula requires thrill (palpable vibration) and bruit (audible whoosh) — absent both suggests thrombosis. Never BP or venipuncture on fistula arm.",
        "clinical_why": "Clotted fistula loses dialysis access — surgical thrombectomy time-sensitive.",
    },
    "ms-q17": {
        "rationale": "C. difficile spores resist alcohol-based hand rub — soap and water with friction removes spores. Contact precautions, dedicated equipment, bleach cleaning.",
        "clinical_why": "Alcohol gel gives false security — spores spread room-to-room causing outbreaks.",
    },
    "ms-q18": {
        "rationale": "Acute chest syndrome in sickle cell: new pulmonary infiltrate, chest pain, fever, hypoxia — O₂, fluids, antibiotics, exchange transfusion may be needed. Mimics pneumonia.",
        "clinical_why": "Leading cause of death in sickle cell adults — early recognition reduces respiratory failure.",
    },
    "ms-q19": {
        "rationale": "Oliguria (<30 mL/hr) with hypotension and tachycardia post-op indicates hypovolemia — assess bleeding, IV access, fluid bolus per order, trend hemoglobin.",
        "clinical_why": "Undetected hemorrhage leads to shock and cardiac arrest — I&O and VS every 15 min early post-op.",
    },
    "ms-q20": {
        "rationale": "Metformin with IV iodinated contrast increases lactic acidosis risk — hold metformin 48 hr before and after contrast, verify renal function (eGFR).",
        "clinical_why": "Contrast-induced nephropathy plus metformin accumulation causes lethal lactic acidosis.",
    },
    "ms-q21": {
        "rationale": "Acute hemolytic transfusion reaction: fever, chills, flank/back pain, hypotension during transfusion — stop immediately, keep IV open with NS, return blood to lab, notify provider.",
        "clinical_why": "Continuing transfusion causes DIC, renal failure, and death — verify patient ID and blood unit at bedside.",
    },
    "ms-q22": {
        "rationale": "Delegate stable, routine tasks with clear parameters to UAP — ambulation after PT clearance. Never delegate assessment, teaching, evaluation, or unstable patients.",
        "clinical_why": "RN retains accountability — inappropriate delegation is a leading cause of nursing malpractice.",
    },
    "pd-1": {
        "rationale": "Opioid respiratory depression: RR <12, hypoxemia, sedation — naloxone per protocol, stimulate, airway support, reduce/stop opioid. Morphine peak effect may be delayed.",
        "clinical_why": "Post-op opioid oversedation is preventable with sedation scales and capnography when available.",
    },
    "pd-2": {
        "rationale": "Hyperkalemia K⁺ 6.2 with widened QRS: calcium gluconate first for cardiac protection, then insulin/D50, kayexalate, dialysis if refractory. Furosemide alone insufficient acutely.",
        "clinical_why": "CHF patient may be on ACEi/spironolactone worsening hyperkalemia — continuous monitoring essential.",
    },
    "pd-3": {
        "rationale": "Alert hypoglycemia BG 48: Rule of 15 — oral fast carbs, recheck 15 min. IV dextrose if NPO or altered; glucagon IM if no IV.",
        "clinical_why": "Treating with insulin would be fatal — always verify glucose before insulin administration.",
    },
    "pd-4": {
        "rationale": "Post-thyroidectomy neck swelling with stridor: expanding hematoma compressing airway — open incision at bedside to evacuate clot while calling for surgical airway support.",
        "clinical_why": "Minutes to airway loss — this is one of few times nurse opens surgical wound at bedside.",
    },
    "pd-5": {
        "rationale": "Platelets 18,000 with active bleeding: bleeding precautions (no IM, soft toothbrush), platelet transfusion per order, monitor for intracranial bleed. No aspirin or heparin.",
        "clinical_why": "Spontaneous bleeding risk increases below 20,000 — intracranial hemorrhage is life-threatening.",
    },
}

DOSAGE_CLINICAL_WHY = {
    "dos-p01": "Digoxin has narrow therapeutic index — double-check calculation and hold if apical pulse <60.",
    "dos-p02": "Acetaminophen overdose causes hepatotoxicity — verify total daily dose from all sources.",
    "dos-p03": "IV rate errors cause fluid overload or line clotting — always convert hours to minutes for gtt/min.",
    "dos-p04": "Pump programming errors are high-alert — independent double-check mL/hr with second nurse.",
    "dos-p05": "Pediatric weight-based dosing requires kg conversion — using pounds as kg causes 2.2× overdose.",
    "dos-p06": "Small-volume high-potency drugs (opioids, digoxin) need calibrated syringes — decimal errors are lethal.",
    "dos-p07": "Multiple nurses giving PRN acetaminophen can exceed 4 g/day — coordinate with team.",
    "dos-p08": "Microdrip (60 gtt/mL) is standard for precise pediatric and critical infusions.",
    "dos-p09": "Heparin is ISMP high-alert — weight-based bolus errors cause bleeding or failed anticoagulation.",
    "dos-p10": "Older adults have reduced clearance — start low, go slow to prevent falls and delirium.",
    "dos-p11": "Liquid formulations vary in concentration — always read label mg/mL before calculating.",
    "dos-p12": "IV infiltration risk rises with prolonged infusions — assess site every 1–2 hours.",
    "dos-p13": "Partial tablet doses must be scored or available — document exact amount given.",
    "dos-p14": "Pediatric antibiotics dosed per day divided by frequency — giving daily total as one dose overdoses.",
    "dos-p15": "Manual IV rate requires full-minute drop count — distractions cause dangerous rate errors.",
}

MENTAL_HEALTH_EXPANSIONS = {
    "mh-q01": {
        "explanation": "Direct, nonjudgmental suicide inquiry ('Are you thinking of killing yourself right now?') is evidence-based and does not plant the idea.",
        "clinical_why": "Columbia Suicide Severity Rating Scale and Joint Commission require direct assessment — ambiguous responses miss imminent risk.",
    },
    "mh-q02": {
        "explanation": "False reassurance ('Everything will be fine') dismisses emotion and shuts down communication — non-therapeutic per Peplau.",
        "clinical_why": "Patients stop sharing suicidal thoughts when minimized — increases completed suicide risk.",
    },
    "mh-q03": {
        "explanation": "CIWA-Ar ≥20 indicates severe alcohol withdrawal — initiate benzodiazepine protocol (lorazepam/diazepam), thiamine, monitor for seizures and DTs.",
        "clinical_why": "Delirium tremens mortality reaches 15% without treatment — CIWA guides symptom-triggered dosing.",
    },
    "mh-q04": {
        "explanation": "Command hallucinations directing harm require immediate safety assessment: intent, ability to resist, access to weapons, 1:1 observation, notify provider.",
        "clinical_why": "Command hallucinations to harm others carry higher violence completion rate than passive ideation.",
    },
    "mh-q05": {
        "explanation": "PHQ-9 item 9 asks about suicidal thoughts — any positive score requires immediate risk assessment, safety plan, and possible 1:1.",
        "clinical_why": "Screening tools are not substitutes for clinical interview but trigger mandatory follow-up.",
    },
    "mh-q06": {
        "explanation": "Serotonin syndrome: agitation, hyperreflexia, clonus, hyperthermia, autonomic instability — often from SSRI + MAOI or linezolid. Stop serotonergic drugs, supportive care, cyproheptadine.",
        "clinical_why": "Can progress to rhabdomyolysis and death within hours — often mistaken for infection.",
    },
    "mh-q07": {
        "explanation": "Least restrictive environment: verbal de-escalation, milieu changes, PRN medications before restraint/seclusion — CMS Conditions of Participation.",
        "clinical_why": "Restraint causes trauma, positional asphyxia, and death — document alternatives attempted.",
    },
    "mh-q08": {
        "explanation": "Lithium is renally cleared — maintain consistent sodium and fluid intake; dehydration, NSAIDs, and ACE inhibitors raise levels.",
        "clinical_why": "Therapeutic index narrow (0.6–1.2 mEq/L) — toxicity causes tremor, confusion, seizures.",
    },
    "mh-q09": {
        "explanation": "Trauma-informed care: safety, trustworthiness, choice, collaboration, empowerment — avoid retraumatization from restraint or forced detail of trauma.",
        "clinical_why": "Retraumatization worsens PTSD symptoms and treatment engagement.",
    },
    "mh-q10": {
        "explanation": "Second-generation antipsychotics cause metabolic syndrome — monitor weight, waist circumference, fasting glucose, lipids at baseline and ongoing.",
        "clinical_why": "Patients with SMI die 25 years earlier — cardiovascular disease from untreated metabolic effects.",
    },
    "mh-q11": {
        "explanation": "Restraint/seclusion: physician/provider order within 1 hour, face-to-face evaluation, continuous monitoring, release at earliest safe moment, debrief with patient.",
        "clinical_why": "CMS and state regulations limit duration — failure to comply is reportable violation.",
    },
}

TERMINOLOGY_CLINICAL_WHY = {
    "term-q02": "Recognizing -itis prompts inflammation workup — fever workup, WBC, source control.",
    "term-q04": "Nephro- terms guide renal labs (BUN, creatinine, urinalysis) when kidney disease suspected.",
    "term-q06": "Understanding antibiotic etymology reinforces spectrum and resistance teaching in pharmacology.",
}

FLASHCARD_CLINICAL_WHY = {
    "Cardiovascular System": {
        "emergency": "Left-sided failure causes pulmonary edema — crackles and hypoxemia precede cardiogenic shock.",
        "safety": "Nitroglycerin vasodilation in hypotension causes syncope and MI extension — verify SBP and PDE-5 use.",
    },
    "Respiratory System": {
        "emergency": "Airway always first — hypoxemia with AMS may need assisted ventilation before full workup.",
        "safety": "COPD retainers need titrated O₂ — monitor ABG for rising PaCO₂ and acidosis.",
    },
    "Neurological System": {
        "emergency": "Thunderclap headache suggests SAH — non-contrast CT, then LP if CT negative per protocol.",
        "safety": "Aspiration pneumonia is leading killer after stroke — speech-language pathology swallow eval before oral intake.",
    },
    "Gastrointestinal System": {
        "emergency": "Upper GI bleed with hypotension needs two large-bore IVs, type & screen, PPI, possible endoscopy.",
        "safety": "Aspiration during procedures causes pneumonia — verify NPO status and sedation level.",
    },
    "Renal & Genitourinary System": {
        "emergency": "Hyperkalemia with ECG changes is treated before dialysis — calcium first, then K⁺ lowering.",
        "safety": "Contrast nephropathy preventable with hydration — hold nephrotoxic meds, monitor creatinine 48–72 hr.",
    },
    "Endocrine System": {
        "emergency": "Severe hypoglycemia (<54) with AMS needs IV dextrose or IM glucagon — cannot rely on oral if unconscious.",
        "safety": "Insulin name/dose errors are ISMP top hazard — independent double-check with second nurse.",
    },
    "Musculoskeletal System": {
        "emergency": "5 P's of compartment syndrome — pain with passive stretch is earliest reliable sign.",
        "safety": "Compartment syndrome is surgical emergency — fasciotomy within 6 hours saves limb function.",
    },
    "Hematologic & Immunologic System": {
        "emergency": "Febrile neutropenia needs empiric antibiotics within 60 minutes — fever may be only sign of bacteremia.",
        "safety": "Hemolytic transfusion reaction — stop blood, maintain IV access, support BP, return unit to blood bank.",
    },
}


def load_json(name):
    path = BASE / name
    with path.open(encoding="utf-8") as f:
        return json.load(f), path


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fix_assessment():
    data, path = load_json("assessment.json")
    for q in data["practice_questions"]:
        qid = q["id"]
        if qid in ASSESSMENT_FIRST_FIVE:
            q.update(ASSESSMENT_FIRST_FIVE[qid])
    # Replace scaffold questions aq-06..40
    kept = [q for q in data["practice_questions"] if int(q["id"].split("-")[1]) <= 5]
    for rep in ASSESSMENT_REPLACEMENTS:
        kept.append({
            **rep,
            "nclex_category": "Physiological Integrity",
            "source": SOURCE,
        })
    data["practice_questions"] = kept
    save_json(path, data)
    return len(ASSESSMENT_FIRST_FIVE) + len(ASSESSMENT_REPLACEMENTS)


def fix_maternal_child():
    data, path = load_json("maternal_child.json")
    for q in data["practice_questions"]:
        if q["id"] in MATERNAL_CHILD_FIRST_TEN:
            q.update(MATERNAL_CHILD_FIRST_TEN[q["id"]])
    kept = [q for q in data["practice_questions"] if int(q["id"].split("-")[1][1:]) <= 10]
    for rep in MATERNAL_CHILD_REPLACEMENTS:
        kept.append({
            **rep,
            "nclex_category": "Physiological Integrity",
            "source": MC_SOURCE,
        })
    data["practice_questions"] = kept
    save_json(path, data)
    return len(MATERNAL_CHILD_FIRST_TEN) + len(MATERNAL_CHILD_REPLACEMENTS)


def fix_med_surg():
    data, path = load_json("med_surg.json")
    count = 0
    for section in ("practice_questions", "priority_drill"):
        for q in data[section]:
            qid = q["id"]
            if qid in MED_SURG_RATIONALES:
                q["rationale"] = MED_SURG_RATIONALES[qid]["rationale"]
                q["clinical_why"] = MED_SURG_RATIONALES[qid]["clinical_why"]
                count += 1
    for fc in data["flashcards"]:
        cat = fc.get("category", "")
        front = fc.get("front", "")
        if cat in FLASHCARD_CLINICAL_WHY:
            if "emergency" in front.lower():
                fc["clinical_why"] = FLASHCARD_CLINICAL_WHY[cat]["emergency"]
            elif "safety" in front.lower():
                fc["clinical_why"] = FLASHCARD_CLINICAL_WHY[cat]["safety"]
            count += 1
    save_json(path, data)
    return count


def fix_nclex_prep(med_surg_rationales):
    data, path = load_json("nclex_prep.json")
    count = 0

    def update_q(q):
        nonlocal count
        qid = q.get("id")
        if qid in med_surg_rationales:
            q["rationale"] = med_surg_rationales[qid]["rationale"]
            q["clinical_why"] = med_surg_rationales[qid]["clinical_why"]
            count += 1

    for cat_questions in data.get("questions_by_category", {}).values():
        for q in cat_questions:
            update_q(q)
    for q in data.get("all_questions", []):
        update_q(q)
    save_json(path, data)
    return count


def fix_dosage():
    data, path = load_json("dosage.json")
    count = 0
    for p in data["practice_problems"]:
        pid = p["id"]
        if pid in DOSAGE_CLINICAL_WHY:
            p["clinical_why"] = DOSAGE_CLINICAL_WHY[pid]
            count += 1
    save_json(path, data)
    return count


def fix_mental_health():
    data, path = load_json("mental_health.json")
    count = 0
    for q in data["practice_questions"]:
        if q["id"] in MENTAL_HEALTH_EXPANSIONS:
            q.update(MENTAL_HEALTH_EXPANSIONS[q["id"]])
            count += 1
    save_json(path, data)
    return count


def fix_terminology():
    data, path = load_json("terminology.json")
    count = 0
    for q in data["practice_questions"]:
        if q["id"] in TERMINOLOGY_CLINICAL_WHY:
            q["clinical_why"] = TERMINOLOGY_CLINICAL_WHY[q["id"]]
            count += 1
    save_json(path, data)
    return count


def fix_pathophysiology():
    data, path = load_json("pathophysiology.json")
    expansions = {
        "patho-q11": (
            "DKA (type 1): insulin deficiency → ketogenesis and metabolic acidosis. HHNS (type 2): profound hyperglycemia >600 mg/dL with osmotic diuresis but minimal ketones.",
            "DKA needs insulin urgently after fluids and K⁺ check; HHNS needs aggressive fluids first — both are emergencies.",
        ),
        "patho-q12": (
            "Berlin ARDS definition: P/F ratio <300 with bilateral infiltrates not fully explained by cardiac failure, on PEEP ≥5 cm H₂O within 7 days of insult.",
            "ARDS management is lung-protective ventilation — low tidal volume 6 mL/kg IBW and plateau pressure <30.",
        ),
        "patho-q13": (
            "Heparin-induced thrombocytopenia (HIT): platelets drop 30–50% on heparin with paradoxical thrombosis — stop all heparin including flushes, start alternative anticoagulant.",
            "Continuing heparin in HIT causes limb loss and PE — 4T score guides suspicion before antibody testing.",
        ),
        "patho-q14": (
            "Left ventricular failure backs blood into pulmonary circulation — crackles, S₃, orthopnea, paroxysmal nocturnal dyspnea, pink frothy sputum in acute pulmonary edema.",
            "Right-sided failure shows JVD and peripheral edema — many patients have biventricular failure.",
        ),
        "patho-q15": (
            "Metabolic acidosis triggers compensatory hyperventilation (Kussmaul respirations) to blow off CO₂ and raise pH — check ABG for pH, PaCO₂, HCO₃⁻.",
            "DKA and sepsis cause metabolic acidosis — treat underlying cause, not only compensation.",
        ),
        "patho-q16": (
            "Sepsis-3 defines sepsis as suspected infection plus acute organ dysfunction (SOFA/qSOFA score change) — SIRS alone is insufficient.",
            "Hour-1 bundle: lactate, blood cultures, broad antibiotics, fluids 30 mL/kg if hypotensive.",
        ),
        "patho-q17": (
            "Ischemic penumbra surrounds infarct core — hypoperfused but viable tissue salvageable with reperfusion (tPA, thrombectomy) within time windows.",
            "Every 15-minute delay in stroke treatment worsens disability — 'time is brain.'",
        ),
        "patho-q18": (
            "K⁺ 6.8 mEq/L is life-threatening — continuous tele, notify provider, prepare calcium gluconate for ECG changes; never IV K⁺ push.",
            "ECG changes precede arrest — peaked T, widened QRS, sine wave pattern requires immediate treatment.",
        ),
        "patho-q1": ("Septic shock begins with vasodilation and warm periphery; cold shock and hypotension follow as compensation fails.", "Early recognition drives sepsis hour-1 bundle: cultures, antibiotics, fluids, lactate."),
        "patho-q2": ("JVD reflects elevated CVP; crackles indicate pulmonary edema from left-sided backup — diurese cautiously and monitor output.", "Giving rapid fluids worsens pulmonary edema in cardiogenic shock."),
        "patho-q3": ("DKA causes profound dehydration from osmotic diuresis — isotonic fluids restore perfusion before insulin lowers glucose and shifts K⁺.", "Fluids reduce mortality; insulin without volume resuscitation worsens hypotension."),
        "patho-q4": ("Insulin drives K⁺ into cells — starting insulin when K⁺ <3.3 mEq/L can cause fatal arrhythmia.", "Total body K⁺ is depleted in DKA despite normal/high serum levels."),
        "patho-q5": ("Chronic CO₂ retention leads kidneys to retain HCO₃⁻ compensating metabolic component — pH may be near normal.", "Acute O₂ overdose can unmask uncompensated respiratory acidosis."),
        "patho-q6": ("After 30 mL/kg crystalloid, persistent hypotension needs vasopressors — norepinephrine first-line for septic shock per Surviving Sepsis.", "Delaying vasopressors prolongs organ hypoperfusion and lactate elevation."),
        "patho-q7": ("Prerenal azotemia from hypoperfusion concentrates BUN disproportionately — improves with fluid resuscitation.", "BUN:Cr >20:1 with low urine Na⁺ supports prerenal cause before starting nephrotoxins."),
        "patho-q8": ("Non-contrast CT head rules out hemorrhage before thrombolytics — IV tPA contraindicated in bleed.", "Time from symptom onset determines tPA eligibility — CT must not delay unnecessarily."),
        "patho-q9": ("Hyperkalemia ECG progression: peaked T → flattened P → wide QRS → sine wave → VF/asystole.", "Calcium stabilizes membrane while K⁺ lowering therapies take effect."),
        "patho-q10": ("2–3 lb weight gain in 24–48 hr equals ~1–1.5 L fluid retention — notify before crackles and orthopnea worsen.", "Daily weights are more sensitive than single lung auscultation for early CHF decompensation."),
    }
    count = 0
    for q in data["practice_questions"]:
        if q["id"] in expansions:
            exp, cw = expansions[q["id"]]
            q["explanation"] = exp
            q["clinical_why"] = cw
            count += 1
    wb_expansions = {
        "wb-na-k-pump": "Hyperkalemia depolarizes cardiac cells — peaked T waves are earliest tele sign before lethal arrhythmias.",
        "wb-insulin-deficiency": "Acidosis drives H⁺ into cells exchanging K⁺ out — serum K⁺ falsely normal until insulin and correction of acidosis.",
        "wb-capillary-permeability": "Septic shock is distributive — fluid leaks to interstitium despite adequate volume resuscitation.",
        "wb-raas-chf": "Daily weight detects 1–2 L fluid gain before pulmonary symptoms — cornerstone of CHF self-management teaching.",
        "wb-copd-co2": "Titrate O₂ to SpO₂ 88–92% — prevents CO₂ narcosis from blunted hypoxic ventilatory drive.",
        "wb-aki-prerenal": "Prerenal AKI reverses with perfusion restoration — BUN:Cr >20:1 and concentrated urine support diagnosis.",
    }
    for s in data["what_breaks_down_scenarios"]:
        if s["id"] in wb_expansions:
            s["clinical_why"] = wb_expansions[s["id"]]
            count += 1
    save_json(path, data)
    return count


NCLEX_STANDALONE = {
    "nclex-mh-1": {
        "rationale": "Reflection ('You feel alone right now') validates emotion without arguing or minimizing — builds trust for further suicide and depression assessment.",
        "clinical_why": "Correcting or dismissing feelings shuts down disclosure of suicidal ideation.",
        "clinical_judgment_focus": "Therapeutic communication prioritizes patient feelings over correction.",
    },
    "nclex-ob-1": {
        "rationale": "Sudden headache and visual changes at 32 weeks suggest severe preeclampsia — assess BP, proteinuria, reflexes; magnesium and delivery planning may be needed.",
        "clinical_why": "Eclampsia risk rises with severe features — maternal seizure and placental abruption threaten both lives.",
        "clinical_judgment_focus": "Maternal and fetal safety — preeclampsia is life-threatening.",
    },
    "nclex-peds-1": {
        "rationale": "At 4 months, infants roll back to side, hold head steady, reach for objects, and social smile — walking (12 mo) and two-word phrases (18–24 mo) are much later.",
        "clinical_why": "Developmental delay screening at well-child visits triggers early intervention for motor and cognitive deficits.",
        "clinical_judgment_focus": "Age-appropriate expectations guide assessment and parent teaching.",
    },
    "nclex-pharm-1": {
        "rationale": "Digoxin has narrow therapeutic index — hold if apical pulse <60 bpm (adult) or per facility policy, assess for toxicity (nausea, vision changes, arrhythmias), notify provider.",
        "clinical_why": "Bradycardia may worsen to heart block — hypokalemia increases digoxin toxicity risk.",
        "clinical_judgment_focus": "Medication safety requires assessment before administration.",
    },
    "nclex-safe-1": {
        "rationale": "RACE protocol: Rescue patients in immediate danger first, then pull Alarm, Contain fire/smoke by closing doors, Extinguish if trained and fire is small, Evacuate vertically per facility plan.",
        "clinical_why": "Horizontal evacuation may be impossible — rescue prevents smoke inhalation deaths before fire spreads.",
        "clinical_judgment_focus": "Life safety protocols prioritize human rescue.",
    },
}


def fix_nclex_standalone():
    data, path = load_json("nclex_prep.json")
    count = 0

    def update_q(q):
        nonlocal count
        qid = q.get("id")
        if qid in NCLEX_STANDALONE:
            q.update(NCLEX_STANDALONE[qid])
            count += 1

    for cat_questions in data.get("questions_by_category", {}).values():
        for q in cat_questions:
            update_q(q)
    for q in data.get("all_questions", []):
        update_q(q)
    save_json(path, data)
    return count


def main():
    results = {
        "assessment": fix_assessment(),
        "maternal_child": fix_maternal_child(),
        "med_surg": fix_med_surg(),
        "nclex_prep": fix_nclex_prep(MED_SURG_RATIONALES),
        "nclex_standalone": fix_nclex_standalone(),
        "dosage": fix_dosage(),
        "mental_health": fix_mental_health(),
        "terminology": fix_terminology(),
        "pathophysiology": fix_pathophysiology(),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()