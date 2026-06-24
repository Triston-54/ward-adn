"""Generate med_surg.json and nclex_prep.json for static deployment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "content"


def build_med_surg() -> dict:
    systems = [
        {
            "id": "cardiovascular",
            "title": "Cardiovascular System",
            "pathophysiology": (
                "The cardiovascular system delivers oxygenated blood via the heart and vasculature. "
                "Heart failure occurs when the pump cannot meet metabolic demands — left-sided failure "
                "backs up into lungs (pulmonary edema, crackles, orthopnea); right-sided failure backs "
                "up systemically (JVD, peripheral edema, hepatomegaly). ACS results from plaque rupture "
                "and thrombus formation. Hypertension damages vessel endothelium. Dysrhythmias alter "
                "cardiac output through rate, rhythm, or conduction disturbances."
            ),
            "nursing_care": [
                "Monitor vital signs, heart sounds, lung sounds, and daily weights",
                "Assess pain using PQRST; administer nitroglycerin and morphine for ACS per protocol",
                "Maintain IV access; prepare for cardiac catheterization when indicated",
                "Position HF patients upright with legs dependent to reduce preload",
                "Strict I&O; limit sodium and fluids per provider order",
                "Educate on low-sodium diet, medication adherence, and daily weight monitoring",
            ],
            "safety": [
                "Never give nitroglycerin if SBP < 90 mmHg or PDE-5 inhibitor within 24–48 hours",
                "Continuous cardiac monitoring for dysrhythmias and electrolyte imbalances",
                "Fall precautions with orthostatic hypotension from diuretics",
                "Bleeding precautions with anticoagulants",
            ],
            "priority_actions": [
                "Chest pain with diaphoresis and ST elevation → activate emergency response",
                "Acute pulmonary edema → high Fowler position, O2, notify provider",
                "Symptomatic bradycardia with hypotension → atropine per ACLS",
                "New atrial fibrillation with rapid ventricular response → assess stability first",
            ],
            "key_conditions": ["Heart failure", "ACS/MI", "Hypertension", "Atrial fibrillation", "PVD"],
        },
        {
            "id": "respiratory",
            "title": "Respiratory System",
            "pathophysiology": (
                "Gas exchange occurs at the alveolar-capillary membrane. COPD involves chronic inflammation "
                "and airflow limitation. Asthma is reversible bronchospasm. Pneumonia is alveolar consolidation. "
                "Pulmonary embolism obstructs pulmonary vasculature. ARDS is diffuse alveolar damage with "
                "refractory hypoxemia."
            ),
            "nursing_care": [
                "Assess RR, effort, SpO2, lung sounds, and work of breathing",
                "Position for maximum lung expansion — tripod for COPD, high Fowler for dyspnea",
                "Administer bronchodilators and oxygen — target SpO2 88–92% in COPD",
                "Encourage coughing, deep breathing, incentive spirometry post-operatively",
                "Chest physiotherapy and suctioning for retained secretions",
                "Monitor ABGs — avoid over-oxygenating chronic CO2 retainers",
            ],
            "safety": [
                "High-flow O2 in COPD may suppress hypoxic drive",
                "NPO before thoracentesis or bronchoscopy per protocol",
                "Fall risk with sedating respiratory medications",
                "Isolation precautions for TB and certain pneumonias",
            ],
            "priority_actions": [
                "SpO2 < 90% with altered mental status → airway assessment first",
                "Sudden pleuritic chest pain and tachycardia → suspect PE",
                "Stridor or silent chest in asthma → impending respiratory failure",
                "Pink frothy sputum → pulmonary edema",
            ],
            "key_conditions": ["COPD", "Asthma", "Pneumonia", "Pulmonary embolism", "ARDS"],
        },
        {
            "id": "neurological",
            "title": "Neurological System",
            "pathophysiology": (
                "Neurological function depends on cerebral perfusion and intact neurons. Stroke causes focal "
                "deficits by vascular territory. Increased ICP reduces CPP (MAP − ICP). Seizures result "
                "from uncontrolled neuronal discharge. Parkinson involves dopamine depletion. MS is CNS "
                "demyelination."
            ),
            "nursing_care": [
                "Serial neurologic assessments — GCS, pupils, motor strength, speech",
                "HOB 30° for ICP management unless contraindicated",
                "Stroke protocol: last known well time, glucose check, NPO for swallow eval",
                "Seizure precautions — padded rails, suction and O2 at bedside",
                "Assist with ADLs while promoting independence in Parkinson patients",
                "Levodopa on schedule — never delay Parkinson medications",
            ],
            "safety": [
                "NPO until swallow assessment after stroke",
                "Avoid Valsalva and extreme neck flexion with elevated ICP",
                "Fall precautions for altered mentation",
                "Aspiration risk — upright positioning for meals",
            ],
            "priority_actions": [
                "Sudden worst headache → suspect subarachnoid hemorrhage",
                "Decreasing GCS or unequal pupils → notify provider immediately",
                "Active seizure → protect head, time seizure, do not restrain",
                "Cushing triad → herniation risk",
            ],
            "key_conditions": ["Ischemic stroke", "Hemorrhagic stroke", "Seizures", "Increased ICP", "Parkinson"],
        },
        {
            "id": "gastrointestinal",
            "title": "Gastrointestinal System",
            "pathophysiology": (
                "The GI tract digests and absorbs nutrients. PUD involves mucosal erosion. IBD causes chronic "
                "inflammation. Bowel obstruction prevents luminal passage. Cirrhosis leads to portal hypertension, "
                "ascites, varices, and hepatic encephalopathy. Pancreatitis involves autodigestion by pancreatic "
                "enzymes."
            ),
            "nursing_care": [
                "Assess bowel sounds, distension, pain, and last BM",
                "NPO with NG decompression for obstruction or acute pancreatitis",
                "Monitor for GI bleeding — hemoglobin, stool color, orthostatic vitals",
                "Administer PPIs, antiemetics, and pain management per protocol",
                "Lactulose for hepatic encephalopathy — goal 2–3 soft stools daily",
                "Pre- and post-op ostomy teaching and stoma assessment",
            ],
            "safety": [
                "NPO verification before procedures and surgery",
                "Bleeding precautions with varices",
                "Confirm NG tube placement with X-ray before feeding",
                "Monitor magnesium with prolonged NG suctioning",
            ],
            "priority_actions": [
                "Hematemesis or melena with hypotension → IV access, fluids, notify provider",
                "Rigid abdomen with rebound tenderness → suspect perforation",
                "Absent bowel sounds with distension → obstruction workup",
                "Asterixis and confusion in cirrhosis → hepatic encephalopathy",
            ],
            "key_conditions": ["PUD/GI bleed", "Bowel obstruction", "Cirrhosis", "Pancreatitis", "IBD"],
        },
        {
            "id": "renal",
            "title": "Renal & Genitourinary System",
            "pathophysiology": (
                "Kidneys regulate fluid, electrolytes, acid-base, and waste. AKI is prerenal, intrarenal, or "
                "postrenal. CKD progresses to ESRD requiring dialysis. Glomerulonephritis causes hematuria. "
                "UTI ascends from urethra. BPH obstructs urine outflow in older males."
            ),
            "nursing_care": [
                "Monitor I&O, daily weights, BUN/creatinine, and electrolytes",
                "Assess urine — report oliguria < 30 mL/hr",
                "Fluid restriction or diuresis per renal function",
                "Dialysis access care — thrill and bruit for AV fistula",
                "Medication dose adjustments for renally excreted drugs",
                "Minimize indwelling catheter duration",
            ],
            "safety": [
                "Contrast dye nephrotoxicity — hydrate and monitor creatinine",
                "Hyperkalemia cardiac precautions",
                "No BP or venipuncture in dialysis fistula arm",
                "Strict aseptic technique with urinary catheters",
            ],
            "priority_actions": [
                "K+ > 6.0 with ECG changes → calcium gluconate, notify provider",
                "Anuria or sudden severe flank pain → renal emergency",
                "Fever with CVA tenderness → pyelonephritis workup",
                "Dialysis disequilibrium → slow ultrafiltration",
            ],
            "key_conditions": ["AKI", "CKD/ESRD", "UTI/Pyelonephritis", "Glomerulonephritis", "BPH"],
        },
        {
            "id": "endocrine",
            "title": "Endocrine System",
            "pathophysiology": (
                "Endocrine glands regulate metabolism and homeostasis. Type 1 DM is autoimmune beta-cell "
                "destruction. Type 2 involves insulin resistance. DKA is insulin deficiency with ketogenesis. "
                "HHNS is profound hyperglycemia without significant ketosis. Hypo/hyperthyroidism alter "
                "metabolic rate. Adrenal disorders affect cortisol balance."
            ),
            "nursing_care": [
                "Blood glucose monitoring — hypoglycemia < 70 mg/dL treat immediately",
                "Insulin per protocol — never mix without verification",
                "DKA/HHNS: IV fluids, insulin infusion, hourly monitoring",
                "Thyroid storm or myxedema coma — ICU-level monitoring",
                "Never abruptly stop corticosteroids",
                "Foot exams and neuropathy screening for diabetic patients",
            ],
            "safety": [
                "Insulin name and dose double-check",
                "Hypoglycemia: 15 g fast-acting carb, recheck in 15 minutes",
                "Hold metformin before contrast per protocol",
                "Sick-day rules education",
            ],
            "priority_actions": [
                "Glucose < 54 with altered mental status → glucagon or IV dextrose",
                "DKA: pH < 7.1 → insulin drip and potassium replacement",
                "Thyroid storm → beta-blockers, antithyroid meds",
                "Addisonian crisis → hydrocortisone IV",
            ],
            "key_conditions": ["Type 1 & 2 DM", "DKA", "HHNS", "Thyroid disorders", "Adrenal disorders"],
        },
        {
            "id": "musculoskeletal",
            "title": "Musculoskeletal System",
            "pathophysiology": (
                "Provides structure, movement, and hematopoiesis. Osteoporosis reduces bone density. OA is "
                "degenerative; RA is autoimmune synovitis. Hip fractures carry high morbidity. Compartment "
                "syndrome compromises perfusion. SCI disrupts motor and sensory pathways below the lesion."
            ),
            "nursing_care": [
                "Assess ROM, strength, pain, and neurovascular status (5 Ps)",
                "Post-op orthopedic: early mobilization, DVT prophylaxis",
                "Fall prevention — clear pathways, assistive devices",
                "Cast care — neurovascular checks, keep dry",
                "SCI: log-roll, skin integrity, autonomic dysreflexia monitoring",
                "Verify weight-bearing restrictions before ambulation",
            ],
            "safety": [
                "Compartment syndrome — pain out of proportion",
                "Fat embolism after long bone fracture",
                "Autonomic dysreflexia in SCI above T6",
                "DVT prophylaxis — SCDs, anticoagulants, early ambulation",
            ],
            "priority_actions": [
                "5 Ps abnormal after cast → bivalve cast, notify provider",
                "SCI BP > 160 with headache → autonomic dysreflexia",
                "Hip fracture post-op sudden SOB → suspect PE",
                "Open fracture → sterile dressing, antibiotics",
            ],
            "key_conditions": ["Osteoporosis/fractures", "OA/RA", "Hip fracture", "Compartment syndrome", "SCI"],
        },
        {
            "id": "hematologic",
            "title": "Hematologic & Immunologic System",
            "pathophysiology": (
                "Blood transports oxygen, provides immunity, and hemostasis. Anemia reduces oxygen-carrying "
                "capacity. Sickle cell causes vaso-occlusive crises. Leukemia is malignant WBC proliferation. "
                "Thrombocytopenia increases bleeding risk. DIC consumes clotting factors. HIV/AIDS compromises "
                "cell-mediated immunity."
            ),
            "nursing_care": [
                "Monitor CBC trends, bleeding signs, and infection indicators",
                "Neutropenic precautions when ANC < 500",
                "Transfusion protocol — two-nurse verification",
                "Bleeding precautions with low platelets",
                "Sickle cell crisis: hydration, pain management, O2",
                "Chemo safety — PPE, double-check doses",
            ],
            "safety": [
                "Febrile transfusion reaction — stop transfusion",
                "Reverse isolation for neutropenia",
                "No aspirin with thrombocytopenia",
                "Chemotherapy hazardous drug handling",
            ],
            "priority_actions": [
                "ANC < 500 with fever → sepsis workup, antibiotics",
                "Platelets < 10,000 or active bleeding → transfusion",
                "Acute chest syndrome in sickle cell → O2, antibiotics",
                "Anaphylaxis during transfusion → stop, epinephrine",
            ],
            "key_conditions": ["Anemia", "Sickle cell", "Leukemia", "Thrombocytopenia/DIC", "HIV/AIDS"],
        },
    ]

    procedures = [
        {
            "id": "ng-tube",
            "title": "Nasogastric Tube Insertion & Care",
            "category": "GI",
            "pre_procedure": ["Verify order", "Assess nasal patency", "Explain and obtain consent"],
            "intra_procedure": ["Measure nose-earlobe-xiphoid", "Confirm with X-ray before feeding", "Secure tube"],
            "post_procedure": ["Irrigate per order", "Oral care q2–4h", "Monitor for aspiration"],
        },
        {
            "id": "foley",
            "title": "Urinary Catheter Insertion",
            "category": "GU",
            "pre_procedure": ["Assess indication", "Gather sterile kit", "Position patient"],
            "intra_procedure": ["Sterile technique", "Inflate balloon per manufacturer", "Closed drainage"],
            "post_procedure": ["Daily meatal care", "Remove ASAP to reduce CAUTI"],
        },
        {
            "id": "central-line",
            "title": "Central Venous Access Care",
            "category": "Vascular",
            "pre_procedure": ["Verify line type and dressing date", "Gather CHG supplies"],
            "intra_procedure": ["Scrub hub 15 seconds", "Needleless connectors per policy"],
            "post_procedure": ["Assess site daily", "CLABSI prevention bundle"],
        },
        {
            "id": "trach-care",
            "title": "Tracheostomy Care & Suctioning",
            "category": "Respiratory",
            "pre_procedure": ["Gather sterile kit", "Pre-oxygenate"],
            "intra_procedure": ["Suction ≤ 15 seconds", "Sterile technique"],
            "post_procedure": ["Humidification", "Emergency trach equipment at bedside"],
        },
        {
            "id": "wound-vac",
            "title": "Negative Pressure Wound Therapy",
            "category": "Integumentary",
            "pre_procedure": ["Assess wound bed", "Pain management"],
            "intra_procedure": ["Seal per manufacturer", "Set pressure per order"],
            "post_procedure": ["Monitor seal and canister", "Report bleeding in canister"],
        },
        {
            "id": "post-op",
            "title": "General Post-Operative Nursing Care",
            "category": "Perioperative",
            "pre_procedure": ["Review surgical report and orders"],
            "intra_procedure": ["ABC assessment in PACU", "Pain and surgical site assessment"],
            "post_procedure": ["Incentive spirometry", "DVT prophylaxis", "Monitor for complications"],
        },
    ]

    core_concepts = [
        {
            "id": "nursing-process",
            "title": "Nursing Process (ADPIE)",
            "summary": "Assessment → Diagnosis → Planning → Implementation → Evaluation",
            "content": "Systematic framework for patient-centered care used throughout med-surg practice.",
            "clinical_relevance": "NCLEX tests each step — especially prioritization during implementation.",
        },
        {
            "id": "prioritization",
            "title": "Prioritization Frameworks",
            "summary": "ABCs, Maslow, acute vs chronic, unstable vs stable",
            "content": "Use ABCs for emergencies. Maslow for psychosocial vs physiological conflicts.",
            "clinical_relevance": "Most NCLEX med-surg questions test prioritization.",
        },
        {
            "id": "infection-control",
            "title": "Infection Prevention & Control",
            "summary": "Standard and transmission-based precautions",
            "content": "Standard precautions for all. Contact for C. diff (soap and water). Airborne for TB.",
            "clinical_relevance": "Know precaution types — C. diff is contact + soap/water.",
        },
        {
            "id": "fluid-electrolytes",
            "title": "Fluid & Electrolyte Balance",
            "summary": "Isotonic, hypotonic, hypertonic fluids and electrolyte disturbances",
            "content": "Assess renal and cardiac status before aggressive replacement.",
            "clinical_relevance": "Hypo/hyperkalemia ECG changes are high-yield NCLEX content.",
        },
        {
            "id": "pain-management",
            "title": "Pain Assessment & Management",
            "summary": "Multimodal analgesia with opioid safety",
            "content": "Assess respiratory rate before additional opioid dosing.",
            "clinical_relevance": "Respiratory depression assessment takes priority over pain score.",
        },
    ]

    priority_drill = [
        {
            "id": "pd-1",
            "scenario": "Post-op patient RR 8, SpO2 88%, difficult to arouse after IV morphine.",
            "options": [
                "Notify provider and prepare naloxone",
                "Reposition and encourage deep breathing",
                "Administer PRN acetaminophen",
                "Document and recheck in 30 minutes",
            ],
            "correct_index": 0,
            "rationale": "Opioid-induced respiratory depression is life-threatening.",
            "ncj_step": "Take Action",
        },
        {
            "id": "pd-2",
            "scenario": "CHF patient with confusion, K+ 6.2, widened QRS on tele.",
            "options": [
                "Administer calcium gluconate IV",
                "Give furosemide IV push",
                "Encourage potassium-rich foods",
                "Trendelenburg position",
            ],
            "correct_index": 0,
            "rationale": "Hyperkalemia with ECG changes requires cardiac membrane stabilization first.",
            "ncj_step": "Take Action",
        },
        {
            "id": "pd-3",
            "scenario": "Diabetic patient diaphoretic, tremulous, BG 48 mg/dL, awake.",
            "options": [
                "Give 15 g fast-acting carbohydrate",
                "Administer 10 units regular insulin",
                "Start D5W infusion",
                "Obtain HbA1c first",
            ],
            "correct_index": 0,
            "rationale": "Rule of 15 for conscious hypoglycemia.",
            "ncj_step": "Take Action",
        },
        {
            "id": "pd-4",
            "scenario": "2 hours post-thyroidectomy: neck swelling, stridor, restlessness.",
            "options": [
                "Open surgical incision at bedside",
                "Apply ice to neck",
                "Administer PO acetaminophen",
                "Place in prone position",
            ],
            "correct_index": 0,
            "rationale": "Expanding hematoma can occlude airway — emergency bedside opening may be required.",
            "ncj_step": "Take Action",
        },
        {
            "id": "pd-5",
            "scenario": "Platelet count 18,000 with gum bleeding and blood in stool.",
            "options": [
                "Bleeding precautions and notify provider",
                "Administer aspirin",
                "Start heparin drip",
                "Apply heat to joints",
            ],
            "correct_index": 0,
            "rationale": "Severe thrombocytopenia with bleeding requires precautions and transfusion consideration.",
            "ncj_step": "Prioritize Hypotheses",
        },
    ]

    flashcards = []
    for s in systems:
        flashcards.append({
            "front": f"Priority action for {s['title']} emergency?",
            "back": s["priority_actions"][0],
            "category": s["title"],
            "clinical_why": s["pathophysiology"][:150],
        })
        flashcards.append({
            "front": f"Key safety concern in {s['title']}?",
            "back": s["safety"][0],
            "category": s["title"],
            "clinical_why": "Prevents iatrogenic harm during med-surg care.",
        })

    practice = [
        {"id": "ms-q1", "question": "Left-sided heart failure — which finding is most consistent?", "options": ["JVD and peripheral edema", "Crackles and pink frothy sputum", "Hepatomegaly and ascites", "Bounding peripheral pulses"], "correct_index": 1, "rationale": "Left-sided HF backs up into pulmonary circulation.", "category": "Cardiovascular", "ncj_step": "Analyze Cues", "difficulty": "medium"},
        {"id": "ms-q2", "question": "Appropriate SpO2 target for COPD on supplemental O2?", "options": ["98–100%", "94–98%", "88–92%", "Below 85%"], "correct_index": 2, "rationale": "Avoid suppressing hypoxic drive in COPD.", "category": "Respiratory", "ncj_step": "Generate Solutions", "difficulty": "medium"},
        {"id": "ms-q3", "question": "Suspected stroke within 45 minutes — first priority?", "options": ["Give tPA immediately", "IV access and blood glucose", "Carotid endarterectomy", "Insert NG tube"], "correct_index": 1, "rationale": "Glucose check and rapid assessment before tPA eligibility.", "category": "Neurological", "ncj_step": "Recognize Cues", "difficulty": "hard"},
        {"id": "ms-q4", "question": "Cirrhosis with confusion and asterixis — priority intervention?", "options": ["Administer lactulose", "Restrict all protein permanently", "Insert urinary catheter", "Abdominal binder"], "correct_index": 0, "rationale": "Hepatic encephalopathy treated with lactulose.", "category": "Gastrointestinal", "ncj_step": "Take Action", "difficulty": "medium"},
        {"id": "ms-q5", "question": "K+ 6.8 with peaked T waves — prepare first?", "options": ["Calcium gluconate IV", "Kayexalate oral", "Furosemide IV", "Insulin with D50"], "correct_index": 0, "rationale": "Calcium stabilizes cardiac membrane immediately.", "category": "Renal", "ncj_step": "Take Action", "difficulty": "hard"},
        {"id": "ms-q6", "question": "Type 1 diabetic BG 42 mg/dL, alert but confused — first action?", "options": ["4 oz orange juice", "10 units NPH insulin", "Normal saline bolus", "Urine ketones first"], "correct_index": 0, "rationale": "Rule of 15 for conscious hypoglycemia.", "category": "Endocrine", "ncj_step": "Take Action", "difficulty": "easy"},
        {"id": "ms-q7", "question": "Post total hip arthroplasty — which finding needs immediate action?", "options": ["Pain 6/10", "SOB and tachycardia", "Serous incision drainage", "Temp 99.1°F"], "correct_index": 1, "rationale": "Sudden SOB suggests pulmonary embolism.", "category": "Musculoskeletal", "ncj_step": "Recognize Cues", "difficulty": "medium"},
        {"id": "ms-q8", "question": "Neutropenic patient temp 100.8°F — priority?", "options": ["Blood cultures and notify for antibiotics", "Cooling blanket only", "Fluids and recheck in 4 hours", "Influenza vaccine"], "correct_index": 0, "rationale": "Fever in neutropenia is a medical emergency.", "category": "Hematologic", "ncj_step": "Take Action", "difficulty": "hard"},
        {"id": "ms-q9", "question": "Which patient should the nurse see first?", "options": ["Post-op pain 5/10", "CHF with new dyspnea SpO2 89%", "Routine BG check due in 30 min", "Discharge teaching stable patient"], "correct_index": 1, "rationale": "Unstable respiratory status takes priority.", "category": "Prioritization", "ncj_step": "Prioritize Hypotheses", "difficulty": "medium"},
        {"id": "ms-q10", "question": "DKA: pH 7.18, K+ 3.2, glucose 480 — before insulin drip?", "options": ["Replace potassium", "Sodium bicarbonate routinely", "Hold all IV fluids", "Subcutaneous insulin only"], "correct_index": 0, "rationale": "Insulin worsens hypokalemia — replace K+ first.", "category": "Endocrine", "ncj_step": "Generate Solutions", "difficulty": "hard"},
        {"id": "ms-q11", "question": "Cast pain unrelieved by opioids with passive toe pain — suspect?", "options": ["Compartment syndrome", "Normal discomfort", "Cast infection", "DVT"], "correct_index": 0, "rationale": "Pain out of proportion suggests compartment syndrome.", "category": "Musculoskeletal", "ncj_step": "Analyze Cues", "difficulty": "medium"},
        {"id": "ms-q12", "question": "Most important warfarin teaching?", "options": ["Consistent vitamin K intake", "Take with NSAIDs", "Double dose if missed", "Avoid all lab draws"], "correct_index": 0, "rationale": "Consistent vitamin K prevents INR fluctuations.", "category": "Cardiovascular", "ncj_step": "Evaluate Outcomes", "difficulty": "easy"},
        {"id": "ms-q13", "question": "Asthma with silent chest and exhaustion indicates?", "options": ["Improving bronchospasm", "Impending respiratory failure", "Successful treatment", "Mild exacerbation"], "correct_index": 1, "rationale": "Silent chest is a pre-arrest sign.", "category": "Respiratory", "ncj_step": "Recognize Cues", "difficulty": "hard"},
        {"id": "ms-q14", "question": "SCI T4: pounding headache, BP 210/118 — first action?", "options": ["Sit upright, loosen clothing", "Rapid IV fluid bolus", "Trendelenburg", "Tight abdominal binder"], "correct_index": 0, "rationale": "Autonomic dysreflexia — sit up, remove trigger.", "category": "Neurological", "ncj_step": "Take Action", "difficulty": "hard"},
        {"id": "ms-q15", "question": "Acute pancreatitis initial management?", "options": ["NPO with IV fluids", "Clear liquid diet ad lib", "High-fat enteral feeds", "Encourage eating"], "correct_index": 0, "rationale": "Bowel rest and hydration reduce pancreatic stimulation.", "category": "Gastrointestinal", "ncj_step": "Generate Solutions", "difficulty": "easy"},
        {"id": "ms-q16", "question": "ESRD on hemodialysis — which finding is urgent?", "options": ["Absent thrill and bruit at fistula", "Weight gain 1 kg", "Mild itching", "Post-dialysis fatigue"], "correct_index": 0, "rationale": "Absent thrill/bruit indicates fistula thrombosis.", "category": "Renal", "ncj_step": "Recognize Cues", "difficulty": "medium"},
        {"id": "ms-q17", "question": "C. difficile care — nurse should?", "options": ["Soap and water hand hygiene", "Alcohol rub only", "Airborne isolation", "N95 for all contact"], "correct_index": 0, "rationale": "Spores not killed by alcohol rubs.", "category": "Infection Control", "ncj_step": "Take Action", "difficulty": "easy"},
        {"id": "ms-q18", "question": "Sickle cell: chest pain, fever, hypoxia — priority?", "options": ["Oxygen and notify provider", "Cold compresses to joints", "Vigorous exercise", "Withhold fluids"], "correct_index": 0, "rationale": "Acute chest syndrome is an emergency.", "category": "Hematologic", "ncj_step": "Take Action", "difficulty": "medium"},
        {"id": "ms-q19", "question": "Post-op urine 15 mL/hr × 3 hr, BP 88/54, HR 118 — suspect?", "options": ["Hypovolemia", "Fluid overload", "Urinary retention", "Normal diuresis"], "correct_index": 0, "rationale": "Oliguria with hypotension indicates hypovolemia.", "category": "Renal", "ncj_step": "Analyze Cues", "difficulty": "medium"},
        {"id": "ms-q20", "question": "Highest lactic acidosis risk pair?", "options": ["Metformin with IV contrast", "Lisinopril with HCTZ", "Statin with aspirin", "Levothyroxine with calcium"], "correct_index": 0, "rationale": "Hold metformin before contrast studies.", "category": "Endocrine", "ncj_step": "Analyze Cues", "difficulty": "medium"},
        {"id": "ms-q21", "question": "Transfusion: chills, fever, back pain — nurse should?", "options": ["Stop transfusion, notify provider", "Slow rate and continue", "Antihistamine and resume", "Document and continue"], "correct_index": 0, "rationale": "Suspected hemolytic reaction — stop immediately.", "category": "Hematologic", "ncj_step": "Take Action", "difficulty": "medium"},
        {"id": "ms-q22", "question": "Appropriate task to delegate to UAP?", "options": ["Ambulate stable post-op with PT clearance", "Assess new chest pain", "Teach insulin administration", "CHF discharge planning"], "correct_index": 0, "rationale": "Stable routine tasks with clear parameters can be delegated.", "category": "Leadership", "ncj_step": "Generate Solutions", "difficulty": "easy"},
    ]

    return {
        "module_id": "med_surg",
        "title": "Medical-Surgical Nursing",
        "core_concepts": core_concepts,
        "body_systems": systems,
        "procedures": procedures,
        "priority_drill": priority_drill,
        "flashcards": flashcards,
        "practice_questions": practice,
    }


def _load_json(name: str) -> dict:
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


# Teaching-focused rationales (2–3 sentences) keyed by question id
NCLEX_ENHANCED_RATIONALES: dict[str, str] = {
    "ms-q1": (
        "Left-sided heart failure causes blood to back up into the pulmonary circulation, producing pulmonary congestion. "
        "Crackles and pink frothy sputum are classic signs of pulmonary edema from left ventricular failure. "
        "JVD, peripheral edema, and hepatomegaly point to right-sided or biventricular failure instead."
    ),
    "ms-q2": (
        "COPD patients often depend on hypoxic drive to maintain adequate ventilation. "
        "Targeting SpO2 88–92% provides sufficient oxygenation while avoiding CO2 retention from over-oxygenation. "
        "Aiming for 98–100% can suppress the hypoxic drive and precipitate respiratory failure."
    ),
    "ms-q3": (
        "Stroke protocol requires rapid assessment before thrombolytic eligibility is determined. "
        "IV access and a blood glucose check are immediate priorities — hypoglycemia can mimic stroke and tPA is contraindicated with active bleeding. "
        "Time last known well must be established, but tPA is never given before imaging and glucose verification."
    ),
    "ms-q4": (
        "Confusion and asterixis in cirrhosis indicate hepatic encephalopathy from ammonia accumulation. "
        "Lactulose acidifies the colon, trapping ammonia and promoting elimination — it is first-line treatment. "
        "Permanent protein restriction is outdated; the priority is reducing ammonia, not long-term dietary restriction."
    ),
    "ms-q5": (
        "Potassium 6.8 mEq/L with peaked T waves is a pre-arrest cardiac emergency. "
        "IV calcium gluconate stabilizes the myocardial cell membrane within minutes, buying time for definitive K+ lowering. "
        "Kayexalate, furosemide, and insulin/D50 lower potassium but work too slowly to protect the heart first."
    ),
    "ms-q6": (
        "A conscious but confused patient with BG 42 mg/dL needs immediate oral fast-acting carbohydrate. "
        "The Rule of 15 calls for 15 g of fast carbs (≈4 oz juice), then recheck glucose in 15 minutes. "
        "Giving insulin or delaying treatment risks progression to seizures and loss of consciousness."
    ),
    "ms-q7": (
        "Sudden shortness of breath and tachycardia after orthopedic surgery are red flags for pulmonary embolism. "
        "PE is a leading cause of postoperative mortality and requires immediate assessment and intervention. "
        "Moderate pain, low-grade fever, and serous drainage are expected post-op findings that do not demand emergent action."
    ),
    "ms-q8": (
        "Fever in a neutropenic patient (ANC typically <500) is a medical emergency — sepsis can progress within hours. "
        "Blood cultures and broad-spectrum antibiotics must begin within 60 minutes per neutropenic fever protocols. "
        "Cooling blankets alone or delayed reassessment risks septic shock and death."
    ),
    "ms-q9": (
        "NCLEX prioritization follows ABCs and unstable over stable patients. "
        "New dyspnea with SpO2 89% in CHF signals acute pulmonary congestion requiring immediate intervention. "
        "Post-op pain 5/10, a routine glucose check, and discharge teaching can wait until the unstable patient is addressed."
    ),
    "ms-q10": (
        "Insulin drives potassium intracellularly, which can worsen hypokalemia and cause fatal dysrhythmias. "
        "With K+ 3.2 mEq/L, potassium replacement must occur before starting the insulin drip in DKA. "
        "IV fluids are essential in DKA, but the specific priority here is correcting hypokalemia before insulin administration."
    ),
    "ms-q11": (
        "Pain unrelieved by opioids plus pain with passive toe movement suggests compartment syndrome — a surgical emergency. "
        "Compartment syndrome causes ischemia from rising fascial pressure and can result in permanent limb loss within hours. "
        "Normal cast discomfort improves with analgesia; compartment pain is out of proportion and worsens with passive stretch."
    ),
    "ms-q12": (
        "Warfarin inhibits vitamin K–dependent clotting factors, so dietary vitamin K directly affects INR. "
        "Consistent daily vitamin K intake prevents dangerous INR fluctuations that cause bleeding or clotting. "
        "NSAIDs increase bleeding risk, missed doses should never be doubled, and INR monitoring is required — not avoided."
    ),
    "ms-q13": (
        "A silent chest in asthma means air movement is so diminished that wheezing disappears — this is a pre-arrest sign. "
        "Exhaustion indicates the patient can no longer maintain the work of breathing and is progressing to respiratory failure. "
        "Do not mistake silence for improvement; prepare for assisted ventilation and emergency medications immediately."
    ),
    "ms-q14": (
        "Pounding headache with BP 210/118 in a T4 SCI patient signals autonomic dysreflexia — a life-threatening sympathetic surge. "
        "Sitting the patient upright and loosening tight clothing reduces venous return and blood pressure immediately. "
        "Trendelenburg, fluid boluses, and abdominal binders worsen hypertension and must be avoided."
    ),
    "ms-q15": (
        "Acute pancreatitis requires bowel rest to reduce pancreatic enzyme stimulation and autodigestion. "
        "NPO status with aggressive IV fluid resuscitation is initial management to prevent hypovolemia and necrosis. "
        "Oral intake — especially high-fat foods — exacerbates pancreatic inflammation and pain."
    ),
    "ms-q16": (
        "A functioning AV fistula produces a palpable thrill and audible bruit from turbulent blood flow. "
        "Absent thrill and bruit suggest thrombosis or stenosis — the lifeline for dialysis is compromised. "
        "Never use the fistula arm for BP, venipuncture, or IV access; report absent thrill immediately."
    ),
    "ms-q17": (
        "C. difficile spores are resistant to alcohol-based hand rubs and require mechanical removal. "
        "Soap-and-water hand hygiene with friction removes spores from hands after contact with the patient or environment. "
        "Contact precautions are appropriate; airborne isolation and N95 are not indicated for C. diff."
    ),
    "ms-q18": (
        "Chest pain, fever, and hypoxia in sickle cell disease suggest acute chest syndrome — a leading cause of death. "
        "Oxygen, pain management, antibiotics, and possible transfusion are needed urgently. "
        "Cold compresses trigger vasoconstriction and sickling; withholding fluids worsens viscosity and vaso-occlusion."
    ),
    "ms-q19": (
        "Oliguria (<30 mL/hr) combined with hypotension and tachycardia indicates hypovolemic shock from inadequate perfusion. "
        "The kidneys conserve volume when cardiac output drops, producing concentrated low urine output. "
        "Fluid resuscitation and identification of the bleeding or fluid loss source are priorities."
    ),
    "ms-q20": (
        "Metformin can cause lactic acidosis, especially when renal perfusion drops during IV contrast administration. "
        "Hold metformin before and 48 hours after contrast studies per protocol to prevent this rare but fatal complication. "
        "The other drug pairs listed are common combinations without this specific high-risk interaction."
    ),
    "ms-q21": (
        "Chills, fever, and back pain during transfusion suggest an acute hemolytic reaction — a life-threatening emergency. "
        "Stop the transfusion immediately, maintain IV access with normal saline, and notify the provider. "
        "Never slow the rate or resume; continuing risks DIC, renal failure, and death."
    ),
    "ms-q22": (
        "Delegation to UAP requires stable patients, routine tasks, and clear parameters within the UAP scope. "
        "Ambulating a stable post-op patient with PT clearance is appropriate delegation with specific instructions. "
        "Assessment, teaching, and discharge planning require RN judgment and cannot be delegated."
    ),
    "mh-q01": (
        "Any statement suggesting suicidal intent requires direct, nonjudgmental assessment of active ideation and plan. "
        "Asking 'Are you having thoughts of killing yourself right now?' is the standard therapeutic and safety approach. "
        "Dismissing, delaying, or offering false reassurance fails to assess risk and may increase isolation."
    ),
    "mh-q02": (
        "Therapeutic communication validates the patient's experience without minimizing or correcting feelings. "
        "Giving false reassurance ('You'll feel better tomorrow') dismisses the patient's reality and shuts down dialogue. "
        "Reflection, open-ended questions, and offering self are therapeutic techniques that build trust."
    ),
    "mh-q03": (
        "A CIWA-Ar score ≥20 indicates severe alcohol withdrawal with risk of seizures and delirium tremens. "
        "Benzodiazepine protocol per facility guidelines is required urgently to prevent life-threatening complications. "
        "Scores 8–15 are moderate; below 8 may need monitoring only — but ≥20 demands immediate pharmacologic treatment."
    ),
    "mh-q04": (
        "Command hallucinations directing harm to others require immediate safety assessment and 1:1 observation. "
        "The nurse must determine whether the patient can resist the commands and whether means and opportunity exist. "
        "Ignoring hallucinations or arguing about their reality does not address the imminent safety risk."
    ),
    "mh-q05": (
        "PHQ-9 item 9 specifically screens for active suicidal ideation in the past two weeks. "
        "A positive response mandates immediate suicide risk assessment — not routine follow-up or discharge. "
        "Suicidal ideation can exist even when mood appears improved; always assess directly."
    ),
    "mh-q06": (
        "Serotonin syndrome results from excess serotonergic activity, often from combining SSRIs, SNRIs, MAOIs, or linezolid. "
        "Hyperreflexia, clonus (especially inducible ankle clonus), agitation, and autonomic instability are hallmark signs. "
        "This is a medical emergency — stop offending agents and notify the provider for cyproheptadine or supportive care."
    ),
    "mh-q07": (
        "The least restrictive environment principle requires starting with verbal de-escalation and milieu management. "
        "Restraint and seclusion are last resorts after less restrictive interventions have been attempted and documented. "
        "CMS regulations and nursing ethics mandate this hierarchy to protect patient dignity and safety."
    ),
    "mh-q08": (
        "Lithium has a narrow therapeutic index and is excreted renally — dehydration and sodium loss increase toxicity. "
        "Patients must maintain consistent fluid intake and sodium consumption; illness with vomiting/diarrhea needs urgent evaluation. "
        "Therapeutic drug levels require regular monitoring; missed doses should not be doubled."
    ),
    "mh-q09": (
        "Trauma-informed care prioritizes safety, trustworthiness, choice, collaboration, and empowerment. "
        "Forcing confrontation of trauma details or using punitive approaches can retraumatize the patient. "
        "Building a predictable, respectful environment supports recovery and therapeutic engagement."
    ),
    "mh-q10": (
        "Second-generation antipsychotics carry significant metabolic risks including weight gain, hyperglycemia, and dyslipidemia. "
        "Baseline and ongoing monitoring of weight, BMI, fasting glucose, and lipids is standard of care. "
        "Failure to monitor can result in new-onset diabetes and cardiovascular disease in psychiatric patients."
    ),
    "mh-q11": (
        "Restraint and seclusion require a provider order, documented least-restrictive alternatives, and continuous face-to-face monitoring. "
        "Regulatory standards (CMS, Joint Commission) mandate time-limited orders and debriefing after release. "
        "Nurses cannot apply restraints indefinitely without reassessment and a valid order."
    ),
    "patho-q1": (
        "Septic (distributive) shock causes massive vasodilation, producing warm, flushed skin in early phases. "
        "As shock progresses, compensatory mechanisms fail and hypotension develops despite warm extremities initially. "
        "Cardiogenic shock presents with cool, clammy skin; hypovolemic shock shows pale, diaphoretic extremities."
    ),
    "patho-q5": (
        "Chronic COPD patients retain CO2 and compensate with renal bicarbonate retention, producing compensated respiratory acidosis. "
        "Their baseline PaCO2 is elevated with near-normal pH — this is their compensated 'normal.' "
        "Over-oxygenating these patients can shift this fragile balance and cause acute CO2 narcosis."
    ),
    "patho-q6": (
        "When septic shock remains hypotensive after adequate fluid resuscitation, vasopressor support is indicated. "
        "Norepinephrine is often first-line to achieve MAP ≥65 mmHg and restore organ perfusion. "
        "Additional fluid boluses alone without vasopressors in refractory shock delay critical perfusion support."
    ),
    "patho-q7": (
        "Prerenal AKI results from decreased renal perfusion (dehydration, heart failure, sepsis) with intact kidney tissue. "
        "BUN rises disproportionately to creatinine, producing a BUN:Cr ratio >20:1. "
        "Intrinsic renal injury shows a ratio closer to 10:1; the distinction guides whether fluids will restore function."
    ),
    "patho-q8": (
        "Thrombolytics (tPA) are contraindicated in hemorrhagic stroke — they would worsen bleeding catastrophically. "
        "Non-contrast CT head is the emergent imaging study to rule out hemorrhage before thrombolytic consideration. "
        "Time is critical, but ruling out bleed takes priority over administering tPA."
    ),
    "patho-q10": (
        "Daily weight is the most sensitive early indicator of fluid retention in heart failure — 2 lb gain in 24 hours signals 1 liter of retained fluid. "
        "Patients should weigh daily at the same time; report gains of 2–3 lb in a day or 5 lb in a week. "
        "Catching fluid retention early prevents hospitalization for acute decompensated HF."
    ),
    "patho-q11": (
        "DKA features significant ketone production with metabolic acidosis (pH <7.3, anion gap elevated). "
        "HHS (hyperosmolar hyperglycemic state) presents with extreme hyperglycemia but minimal ketosis and less acidosis. "
        "Both are emergencies, but ketone prominence distinguishes DKA and guides insulin urgency."
    ),
    "patho-q12": (
        "Berlin ARDS criteria require bilateral infiltrates, P/F ratio <300, and PEEP ≥5 cm H2O not fully explained by cardiac failure. "
        "ARDS severity is classified by P/F ratio: mild 200–300, moderate 100–200, severe <100. "
        "Lung-protective ventilation with low tidal volumes (6 mL/kg) is the cornerstone of management."
    ),
    "patho-q13": (
        "Heparin-induced thrombocytopenia (HIT) is an immune-mediated paradox: platelets drop but thrombosis risk soars. "
        "All heparin products must be stopped immediately when HIT is suspected — continuing causes arterial and venous clots. "
        "Alternative anticoagulation (argatroban, bivalirudin) is needed; platelet transfusion is contraindicated unless bleeding."
    ),
    "patho-q15": (
        "Metabolic acidosis triggers compensatory hyperventilation (Kussmaul respirations) to blow off CO2 and raise pH. "
        "The respiratory system compensates within minutes by increasing rate and depth of breathing. "
        "Bradypnea would worsen acidosis; renal compensation takes days and is not the immediate response."
    ),
    "patho-q16": (
        "Sepsis-3 defines sepsis as life-threatening organ dysfunction caused by a dysregulated host response to infection. "
        "SOFA score ≥2 points from baseline indicates organ dysfunction; qSOFA aids bedside screening. "
        "SIRS criteria alone are insufficient — focus on infection plus organ dysfunction and lactate."
    ),
    "patho-q17": (
        "The ischemic penumbra is tissue at risk but potentially salvageable with timely reperfusion. "
        "The infarcted core is irreversibly damaged; the penumbra surrounds it and deteriorates without blood flow. "
        "This is why stroke treatment is time-critical — 'time is brain' applies to penumbra rescue."
    ),
    "patho-q18": (
        "Potassium >6.5 mEq/L places the patient at immediate risk for ventricular fibrillation and cardiac arrest. "
        "Continuous cardiac monitoring and provider notification are urgent nursing priorities. "
        "IV calcium gluconate (per order) stabilizes the myocardium while definitive K+ lowering therapies are prepared."
    ),
    "aq-01": (
        "SpO2 88% with respiratory rate 32 and accessory muscle use indicates acute respiratory distress requiring immediate action. "
        "The nurse must assess the airway, apply oxygen, position the patient, and notify the provider promptly. "
        "Mildly elevated BP, moderate pain, and normal temperature are not acute threats to airway or breathing."
    ),
    "aq-02": (
        "Abdominal assessment follows the order: inspect, auscultate, percuss, then palpate (IAPPP). "
        "Auscultation must occur before palpation because palpation can alter bowel sounds and lead to inaccurate findings. "
        "Palpating before auscultating is a common error that compromises assessment accuracy."
    ),
    "aq-03": (
        "Orthostatic hypotension is defined as a drop in SBP ≥20 mmHg or DBP ≥10 mmHg within 3 minutes of standing, often with symptoms. "
        "This indicates inadequate cerebral perfusion on position change and increases fall risk. "
        "Any BP change or HR increase alone does not meet the clinical definition."
    ),
    "aq-05": (
        "FAST is the stroke screening mnemonic: Face drooping, Arm weakness, Speech difficulty, Time to call emergency services. "
        "Rapid recognition and activation of the stroke team maximizes the window for thrombolytic therapy. "
        "Early identification directly impacts functional outcomes and mortality."
    ),
    "aq-15": (
        "Absent bowel sounds after abdominal surgery may indicate postoperative ileus or developing obstruction. "
        "Correlate with nausea, abdominal distension, absence of flatus, and pain to differentiate expected ileus from complication. "
        "Notify the provider when bowel sounds remain absent with worsening distension or no flatus — obstruction can progress to ischemia."
    ),
    "aq-17": (
        "Homans sign (calf pain on dorsiflexion) is neither sensitive nor specific enough to diagnose DVT alone. "
        "Assess for unilateral calf swelling, warmth, erythema, and pain while applying Wells criteria and ordering ultrasound. "
        "Missed DVT is a leading cause of preventable pulmonary embolism in hospitalized patients."
    ),
    "aq-19": (
        "Korotkoff phase V — the disappearance of sound — marks diastolic blood pressure in adults per standard technique. "
        "Consistent auscultation technique prevents false hypertension diagnoses and unnecessary treatment. "
        "Pediatric protocols may use phase IV (muffling) per facility policy — know your institution's standard."
    ),
    "aq-20": (
        "Core temperature reflects the hypothalamic set point and is most accurate via pulmonary artery catheter or urinary bladder probe with good urine flow. "
        "Peripheral routes (tympanic, axillary, temporal) are affected by environment and recent intake, reducing accuracy in critical illness. "
        "Accurate temperature trending guides sepsis protocols and fever workups in vulnerable patients."
    ),
    "mc-q01": (
        "Late decelerations indicate uteroplacental insufficiency — the fetus is not receiving adequate oxygen during contractions. "
        "Stop oxytocin if infusing, perform intrauterine resuscitation (position change, O2, IV fluids), and notify the provider. "
        "Increasing oxytocin or ignoring the monitor worsens fetal hypoxia and risks fetal demise."
    ),
    "mc-q02": (
        "A boggy, deviated uterus after delivery indicates uterine atony — the leading cause of postpartum hemorrhage. "
        "Fundal massage is first-line to stimulate contraction and reduce bleeding. "
        "Ice packs and bed rest do not address atony; prompt massage can prevent hemorrhagic shock."
    ),
    "mc-q03": (
        "RUQ/epigastric pain in preeclampsia suggests liver capsule distension and possible HELLP syndrome. "
        "This is a severe feature requiring immediate provider notification and likely magnesium sulfate and delivery planning. "
        "Mild ankle edema and Braxton Hicks contractions are common and not severe features."
    ),
    "mc-q04": (
        "Shoulder dystocia requires McRoberts maneuver (hyperflex thighs) plus suprapubic pressure to free the anterior shoulder. "
        "Fundal pressure pushes the baby further into impaction and is contraindicated. "
        "This is an obstetric emergency — call for help and document time of maneuvers."
    ),
    "mc-q05": (
        "An APGAR of 4 at 1 minute indicates the newborn needs active resuscitation per Neonatal Resuscitation Program (NRP) algorithm. "
        "Continue ventilation, warming, and stimulation; reassess at 5 minutes. "
        "Never stop intervention or discharge a compromised newborn without full resuscitation efforts."
    ),
    "mc-q06": (
        "Absent deep tendon reflexes are the earliest sign of magnesium sulfate toxicity. "
        "Also monitor respiratory rate (>12/min) and urine output (>25–30 mL/hr) before each dose. "
        "Calcium gluconate is the antidote for severe toxicity; report absent reflexes immediately."
    ),
    "mc-q07": (
        "Fever ≥38°C (100.4°F) in an infant under 28–60 days is a medical emergency due to immature immune function. "
        "Full sepsis workup (blood culture, UA, LP per protocol) and empiric antibiotics are required — not outpatient management. "
        "Young infants can deteriorate rapidly from occult bacteremia or meningitis."
    ),
    "mc-q08": (
        "Cord prolapse compresses the umbilical cord and cuts off fetal oxygen supply — an obstetric emergency. "
        "Knee-chest or Trendelenburg position relieves pressure while the nurse elevates the presenting part manually. "
        "Never attempt to push the cord back into the vagina; prepare for emergency cesarean delivery."
    ),
    "mc-q09": (
        "Physiologic jaundice in term newborns typically appears on days 2–3 as fetal RBC breakdown increases bilirubin load. "
        "Jaundice within the first 24 hours is pathologic and requires immediate evaluation for hemolysis or infection. "
        "Breastfed infants can have prolonged physiologic jaundice but still follow the typical onset pattern."
    ),
    "mc-q10": (
        "Postpartum psychosis is a psychiatric emergency occurring within days to 4 weeks after delivery. "
        "It requires immediate psychiatric care, possible hospitalization, and infant safety measures including supervised contact. "
        "Outpatient follow-up alone is insufficient — the mother may have delusions commanding harm to self or infant."
    ),
    "micro-q02": (
        "Pulmonary tuberculosis spreads via airborne droplet nuclei that remain suspended in room air for hours. "
        "Airborne precautions require a negative-pressure AIIR and N95 respirator (or PAPR) for all room entry. "
        "Droplet precautions are insufficient because TB particles are smaller than droplet transmission thresholds."
    ),
    "micro-q03": (
        "Hand hygiene before patient contact breaks the chain of infection at the mode of transmission link. "
        "Pathogens on healthcare worker hands are the most common vehicle for nosocomial spread between patients. "
        "The infectious agent, reservoir, and portal of entry are not directly interrupted by hand washing alone."
    ),
    "micro-q04": (
        "Varicella is transmitted both by airborne droplet nuclei and direct contact with vesicle fluid. "
        "CDC requires airborne isolation plus contact precautions until all lesions are crusted over. "
        "Droplet or contact precautions alone do not provide adequate protection for this dual-mode pathogen."
    ),
    "micro-q05": (
        "Vaccination targets the susceptible host link by stimulating adaptive immunity before pathogen exposure. "
        "Herd immunity reduces transmission by shrinking the pool of susceptible individuals in a population. "
        "Vaccines do not eliminate the agent or reservoir — they prepare the host defense."
    ),
    "micro-q06": (
        "Contact precautions require hand hygiene before donning gown and gloves on room entry. "
        "PPE is donned before contact and doffed inside the room to prevent environmental contamination. "
        "An N95 is not required for contact precautions — it is reserved for airborne pathogens like TB."
    ),
    "micro-q07": (
        "The central line bundle combines hand hygiene, maximal sterile barrier, chlorhexidine skin prep, optimal site selection, and daily necessity review. "
        "This evidence-based bundle significantly reduces CLABSI rates in ICU and acute care settings. "
        "Routine prophylactic antibiotics and daily dressing changes without indication are not bundle components."
    ),
    "micro-q08": (
        "Healthcare workers with influenza must stay home per occupational health policy to prevent nosocomial transmission. "
        "Influenza is contagious before symptoms peak and vulnerable patients (elderly, immunocompromised) face high mortality. "
        "Working with a surgical mask still exposes patients; antivirals are treatment, not a substitute for exclusion."
    ),
    "micro-q09": (
        "Gram-negative bacteria have a thin peptidoglycan layer and lipopolysaccharide outer membrane that does not retain crystal violet. "
        "They appear pink/red after the counterstain (safranin) in the Gram stain procedure. "
        "Purple cocci in clusters describe Gram-positive Staphylococcus; acid-fast staining identifies mycobacteria."
    ),
    "micro-q10": (
        "Antimicrobial stewardship promotes the shortest effective antibiotic course guided by culture results and clinical guidelines. "
        "Broad-spectrum empiric therapy should be de-escalated once the pathogen is identified to reduce resistance and C. diff risk. "
        "Saving leftover antibiotics and indefinite surgical prophylaxis promote resistance and adverse outcomes."
    ),
    "term-q01": (
        "The prefix 'brady-' means slow — bradycardia is a resting heart rate below 60 bpm in adults. "
        "Symptomatic bradycardia (hypotension, altered mental status, chest pain) may require atropine per ACLS protocol. "
        "Not all bradycardia requires treatment; athletes may have normal resting rates below 60."
    ),
    "term-q02": (
        "The suffix '-itis' means inflammation of the attached structure — gastritis is stomach inflammation, meningitis is meningeal inflammation. "
        "Recognizing suffixes allows nurses to decode unfamiliar terms and anticipate clinical presentations. "
        "-osis means abnormal condition, -emia means blood condition, and -logy means study of."
    ),
    "term-q03": (
        "Hematuria combines 'hemat/o' (blood) and '-uria' (urine condition) — blood present in the urine. "
        "Gross hematuria is visible; microscopic hematuria is detected on dipstick or microscopy. "
        "Both require provider notification to rule out infection, stones, trauma, or malignancy."
    ),
    "term-q04": (
        "The root 'nephr/o' refers to the kidney — seen in nephrology, nephritis, and nephrectomy. "
        "Understanding word roots builds vocabulary for renal assessment, medications, and patient education. "
        "Hepat- is liver, pulmon- is lung, and cardi- is heart."
    ),
    "term-q05": (
        "Hyperglycemia means blood glucose above normal limits — hyper- (excessive) + glyc (glucose) + -emia (blood condition). "
        "Sustained hyperglycemia can progress to DKA (type 1) or HHS (type 2) and requires insulin or protocol-driven treatment. "
        "Always verify glucose before administering insulin to prevent hypoglycemic events."
    ),
    "term-q06": (
        "Antibiotics are agents that inhibit or destroy bacteria — anti- (against) + bio (life) + -tic (pertaining to). "
        "They are ineffective against viruses; inappropriate use drives antimicrobial resistance. "
        "Culture and sensitivity guides selection of the narrowest effective spectrum."
    ),
    "term-q07": (
        "Thrombocytopenia means low platelet count — thromb/o (clot/platelet) + cyt (cell) + -penia (deficiency). "
        "Platelets below 50,000 increase bleeding risk; below 20,000 requires bleeding precautions and provider notification. "
        "Monitor for petechiae, ecchymoses, and mucosal bleeding."
    ),
    "term-q08": (
        "The prefix 'dys-' means difficult, painful, or abnormal — dyspnea is labored or difficult breathing. "
        "Dyspnea is a subjective sensation that must be assessed by asking the patient and observing work of breathing. "
        "Never assume dyspnea severity from vital signs alone — pulse oximetry can be normal early in distress."
    ),
    "nclex-mh-1": (
        "Reflection mirrors the patient's stated feeling without judgment, correction, or advice — a core therapeutic technique. "
        "'You feel alone right now' validates the emotion and invites further exploration. "
        "Correcting ('That's not true'), probing defensively ('Why would you think that?'), or advising positivity blocks therapeutic rapport."
    ),
    "nclex-ob-1": (
        "Sudden severe headache and visual changes at 32 weeks gestation are classic warning signs of preeclampsia. "
        "Assess blood pressure immediately and notify the provider — these symptoms suggest severe features and risk of seizure or stroke. "
        "Acetaminophen and rest do not address the underlying pathophysiology; delay risks maternal and fetal morbidity."
    ),
    "nclex-peds-1": (
        "At 4 months, infants typically roll from back to side and demonstrate improved head control during tummy time. "
        "Walking (12–15 months) and two-word phrases (18–24 months) are milestones for much older children. "
        "Age-appropriate milestone knowledge guides anticipatory guidance and early intervention referrals."
    ),
    "nclex-pharm-1": (
        "Digoxin slows AV conduction and increases contractility — bradycardia increases risk for dangerous dysrhythmias. "
        "Hold the dose when apical pulse is <60 bpm in adults (verify facility policy) and notify the provider. "
        "Never administer half doses without an order; always assess apical pulse for a full minute before giving digoxin."
    ),
    "nclex-safe-1": (
        "The RACE protocol for fire response prioritizes Rescue of patients in immediate danger first. "
        "After rescue, activate the Alarm, Contain the fire by closing doors, and Extinguish (if safe) or Evacuate. "
        "Human life always takes priority over property — rescue before attempting to fight the fire."
    ),
    "nclex-pharm-2": (
        "Insulin is an ISMP high-alert medication requiring an independent double-check before administration. "
        "Only regular insulin may be given IV; other formulations are for subcutaneous use only. "
        "Wrong insulin type or dose is a leading cause of preventable hypoglycemic injury and death."
    ),
    "nclex-pharm-3": (
        "Opioid-induced respiratory depression is signaled by RR <12/min, sedation, and pinpoint pupils. "
        "Hold the opioid, stimulate the patient, apply oxygen, and prepare naloxone per protocol. "
        "Never leave a sedated patient unattended after opioid administration — continuous respiratory assessment is required."
    ),
}

NCLEX_CLINICAL_JUDGMENT: dict[str, str] = {
    "ms-q1": "Differentiate left- versus right-sided failure by identifying where congestion backs up — lungs vs. systemic circulation.",
    "ms-q2": "Balance oxygenation with ventilation risk — chronic retainers need lower SpO2 targets than acute patients.",
    "ms-q3": "Time-critical stroke care still requires glucose verification and imaging before thrombolytics.",
    "ms-q4": "Connect neuro changes in liver disease to ammonia accumulation and initiate targeted treatment.",
    "ms-q5": "Sequence hyperkalemia treatment: stabilize the myocardium first, then lower serum potassium.",
    "ms-q6": "Apply the Rule of 15 for conscious hypoglycemia — treat fast, recheck, repeat as needed.",
    "ms-q7": "Recognize post-op SOB as PE until ruled out — a silent killer after orthopedic surgery.",
    "ms-q8": "Neutropenic fever is a 'treat first, diagnose second' emergency — do not wait for culture results to start antibiotics.",
    "ms-q9": "Use ABC framework and instability to rank which patient needs the nurse first.",
    "ms-q10": "Anticipate insulin's effect on potassium before starting DKA protocol — prevent iatrogenic arrhythmia.",
    "ms-q11": "Pain out of proportion to injury is the cardinal cue for compartment syndrome.",
    "ms-q12": "Patient education on warfarin must address dietary consistency, not just medication timing.",
    "ms-q13": "Silent chest in asthma is a danger sign — do not interpret absence of wheeze as improvement.",
    "ms-q14": "Autonomic dysreflexia in SCI above T6 requires immediate upright positioning and trigger removal.",
    "ms-q15": "Bowel rest and hydration are foundational in acute pancreatitis before nutrition is reintroduced.",
    "ms-q16": "The dialysis fistula is the patient's lifeline — assess thrill and bruit every shift.",
    "ms-q17": "Match hand hygiene method to the pathogen — spore-forming organisms require soap and water.",
    "ms-q18": "Acute chest syndrome in sickle cell is an emergency — oxygen, fluids, and provider notification.",
    "ms-q19": "Cluster oliguria with hemodynamic instability to identify hypovolemia early.",
    "ms-q20": "Know high-risk drug-contrast interactions — metformin plus IV contrast risks lactic acidosis.",
    "ms-q21": "Any transfusion reaction with fever and back pain demands immediate cessation and investigation.",
    "ms-q22": "Apply delegation rules: right task, right person, right circumstance, right direction, right supervision.",
    "mh-q01": "Suicidal statements always warrant direct assessment — never avoid the question out of discomfort.",
    "mh-q02": "Distinguish therapeutic from non-therapeutic responses — validation beats correction.",
    "mh-q03": "CIWA-Ar scores guide benzodiazepine dosing urgency in alcohol withdrawal.",
    "mh-q04": "Command hallucinations with violence potential require immediate safety intervention.",
    "mh-q05": "PHQ-9 item 9 is a dedicated suicide screen — a positive answer triggers full risk assessment.",
    "mh-q06": "Recognize serotonin syndrome early — clonus and hyperreflexia distinguish it from other causes of agitation.",
    "mh-q07": "Least restrictive intervention preserves dignity while maintaining safety.",
    "mh-q08": "Lithium toxicity is preventable with consistent sodium, fluid intake, and level monitoring.",
    "mh-q09": "Trauma-informed principles reshape how nurses approach behavior and build therapeutic alliances.",
    "mh-q10": "Metabolic monitoring is essential with antipsychotics — psychiatric medications affect physical health.",
    "mh-q11": "Restraint use is regulated — documentation and monitoring are as important as the intervention itself.",
    "patho-q1": "Early septic shock may look 'warm' — do not be reassured by flushed skin in a febrile patient.",
    "patho-q5": "Know the compensated baseline in COPD — their 'abnormal' ABG may be their normal.",
    "patho-q6": "Escalate from fluids to vasopressors when septic shock does not respond to volume resuscitation.",
    "patho-q7": "BUN:Cr ratio helps distinguish prerenal from intrinsic renal injury at the bedside.",
    "patho-q8": "Rule out hemorrhagic stroke before thrombolytics — CT is non-negotiable.",
    "patho-q10": "Daily weights catch fluid retention before crackles and dyspnea develop.",
    "patho-q11": "Ketone presence differentiates DKA from HHS — both need treatment but pathways differ.",
    "patho-q12": "ARDS requires lung-protective strategies — understand Berlin criteria for severity.",
    "patho-q13": "HIT is a clotting disorder disguised as low platelets — stop heparin immediately.",
    "patho-q15": "Connect acid-base compensation to clinical signs — Kussmaul breathing is the body's rapid response.",
    "patho-q16": "Modern sepsis definition focuses on organ dysfunction, not just vital sign abnormalities.",
    "patho-q17": "Penumbra concept explains why stroke treatment windows exist — salvageable tissue depends on speed.",
    "patho-q18": "Severe hyperkalemia demands cardiac monitoring before and during treatment.",
    "aq-01": "Accessory muscle use with hypoxia signals respiratory failure — act on breathing before other findings.",
    "aq-02": "Assessment technique order prevents altering the very findings you need to detect.",
    "aq-03": "Orthostatic vital signs detect volume depletion and autonomic dysfunction before falls occur.",
    "aq-05": "FAST enables community and bedside stroke recognition — time activation saves brain tissue.",
    "aq-15": "Post-op abdominal assessment integrates bowel sounds with flatus, distension, and nausea.",
    "aq-17": "Never rely on a single physical exam maneuver for DVT — use validated clinical decision tools.",
    "aq-19": "Consistent vital sign technique prevents misclassification and inappropriate treatment.",
    "aq-20": "Core temperature measurement selection affects accuracy in critically ill patients.",
    "mc-q01": "Late decels = fetal hypoxia — intrauterine resuscitation is the nurse's immediate role.",
    "mc-q02": "Boggy fundus = atony = hemorrhage risk — massage before medications when possible.",
    "mc-q03": "RUQ pain in preeclampsia signals severe disease — do not dismiss as heartburn.",
    "mc-q04": "Shoulder dystocia has a defined maneuver sequence — fundal pressure makes it worse.",
    "mc-q05": "Low APGAR triggers NRP algorithm — reassess at 5 minutes, never abandon resuscitation early.",
    "mc-q06": "Magnesium toxicity presents with lost reflexes before respiratory arrest — monitor before each dose.",
    "mc-q07": "Neonatal fever is always serious — young infants need sepsis evaluation, not outpatient care.",
    "mc-q08": "Cord prolapse is a time-critical obstetric emergency — relieve compression while awaiting delivery.",
    "mc-q09": "Jaundice timing distinguishes physiologic from pathologic hyperbilirubinemia.",
    "mc-q10": "Postpartum psychosis requires emergency psychiatric intervention and infant protection.",
    "micro-q02": "Match isolation type to transmission — TB requires airborne, not droplet, precautions.",
    "micro-q03": "Hand hygiene is the single most effective action to break nosocomial transmission.",
    "micro-q04": "Some pathogens require combined precaution types — varicella needs airborne plus contact.",
    "micro-q05": "Vaccination is primary prevention targeting host susceptibility in the chain of infection.",
    "micro-q06": "Correct PPE sequence prevents self-contamination during donning and doffing.",
    "micro-q07": "Evidence-based bundles standardize best practices and reduce preventable infections.",
    "micro-q08": "Ill healthcare workers are a patient safety hazard — occupational health policies protect vulnerable patients.",
    "micro-q09": "Gram stain results guide empiric antibiotic selection while cultures are pending.",
    "micro-q10": "Stewardship protects future patients by limiting resistance and C. difficile.",
    "term-q01": "Medical terminology decoding supports accurate communication and safer care.",
    "term-q02": "Suffix recognition predicts condition type — inflammation, blood disorder, or disease state.",
    "term-q03": "Hematuria always warrants investigation — never normalize blood in urine.",
    "term-q04": "Word roots link terminology to body systems for faster clinical reasoning.",
    "term-q05": "Hyperglycemia terminology connects to actionable nursing assessment and insulin safety.",
    "term-q06": "Antibiotic knowledge prevents misuse and supports stewardship conversations.",
    "term-q07": "Platelet terminology connects to bleeding precaution decisions at the bedside.",
    "term-q08": "Dyspnea assessment requires both subjective report and objective work-of-breathing observation.",
    "nclex-mh-1": "Therapeutic communication prioritizes patient feelings over correction.",
    "nclex-ob-1": "Maternal and fetal safety — preeclampsia warning signs demand immediate action.",
    "nclex-peds-1": "Age-appropriate expectations guide assessment and parent teaching.",
    "nclex-pharm-1": "Medication safety requires assessment before administration.",
    "nclex-safe-1": "Life safety protocols prioritize human rescue.",
    "nclex-pharm-2": "High-alert medications demand independent double-checks and route verification.",
    "nclex-pharm-3": "Opioid safety requires respiratory assessment before and after every dose.",
}

NCLEX_META: dict[str, dict] = {
    "mh-q01": {"category": "Psychosocial Integrity", "ncj_step": "Recognize Cues", "difficulty": "hard"},
    "mh-q02": {"category": "Psychosocial Integrity", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "mh-q03": {"category": "Psychosocial Integrity", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "mh-q04": {"category": "Psychosocial Integrity", "ncj_step": "Take Action", "difficulty": "hard"},
    "mh-q05": {"category": "Psychosocial Integrity", "ncj_step": "Recognize Cues", "difficulty": "hard"},
    "mh-q06": {"category": "Pharmacological Therapies", "ncj_step": "Recognize Cues", "difficulty": "hard"},
    "mh-q07": {"category": "Psychosocial Integrity", "ncj_step": "Generate Solutions", "difficulty": "medium"},
    "mh-q08": {"category": "Pharmacological Therapies", "ncj_step": "Evaluate Outcomes", "difficulty": "medium"},
    "mh-q09": {"category": "Psychosocial Integrity", "ncj_step": "Generate Solutions", "difficulty": "easy"},
    "mh-q10": {"category": "Pharmacological Therapies", "ncj_step": "Evaluate Outcomes", "difficulty": "medium"},
    "mh-q11": {"category": "Psychosocial Integrity", "ncj_step": "Take Action", "difficulty": "medium"},
    "patho-q1": {"category": "Cardiovascular", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "patho-q5": {"category": "Respiratory", "ncj_step": "Analyze Cues", "difficulty": "hard"},
    "patho-q6": {"category": "Cardiovascular", "ncj_step": "Take Action", "difficulty": "hard"},
    "patho-q7": {"category": "Renal", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "patho-q8": {"category": "Neurological", "ncj_step": "Generate Solutions", "difficulty": "hard"},
    "patho-q10": {"category": "Cardiovascular", "ncj_step": "Recognize Cues", "difficulty": "easy"},
    "patho-q11": {"category": "Endocrine", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "patho-q12": {"category": "Respiratory", "ncj_step": "Analyze Cues", "difficulty": "hard"},
    "patho-q13": {"category": "Hematologic", "ncj_step": "Take Action", "difficulty": "hard"},
    "patho-q15": {"category": "Respiratory", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "patho-q16": {"category": "Prioritization", "ncj_step": "Recognize Cues", "difficulty": "medium"},
    "patho-q17": {"category": "Neurological", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "patho-q18": {"category": "Renal", "ncj_step": "Take Action", "difficulty": "hard"},
    "aq-01": {"category": "Respiratory", "ncj_step": "Prioritize Hypotheses", "difficulty": "medium"},
    "aq-02": {"category": "Gastrointestinal", "ncj_step": "Take Action", "difficulty": "easy"},
    "aq-03": {"category": "Cardiovascular", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "aq-05": {"category": "Neurological", "ncj_step": "Recognize Cues", "difficulty": "easy"},
    "aq-15": {"category": "Gastrointestinal", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "aq-17": {"category": "Musculoskeletal", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "aq-19": {"category": "Cardiovascular", "ncj_step": "Take Action", "difficulty": "easy"},
    "aq-20": {"category": "Safety & Infection Control", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "mc-q01": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "hard"},
    "mc-q02": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "medium"},
    "mc-q03": {"category": "Maternal-Newborn", "ncj_step": "Recognize Cues", "difficulty": "hard"},
    "mc-q04": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "hard"},
    "mc-q05": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "medium"},
    "mc-q06": {"category": "Maternal-Newborn", "ncj_step": "Recognize Cues", "difficulty": "medium"},
    "mc-q07": {"category": "Pediatric Nursing", "ncj_step": "Take Action", "difficulty": "hard"},
    "mc-q08": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "hard"},
    "mc-q09": {"category": "Pediatric Nursing", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "mc-q10": {"category": "Maternal-Newborn", "ncj_step": "Take Action", "difficulty": "hard"},
    "micro-q02": {"category": "Infection Control", "ncj_step": "Take Action", "difficulty": "medium"},
    "micro-q03": {"category": "Infection Control", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "micro-q04": {"category": "Infection Control", "ncj_step": "Take Action", "difficulty": "medium"},
    "micro-q05": {"category": "Infection Control", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "micro-q06": {"category": "Safety & Infection Control", "ncj_step": "Take Action", "difficulty": "easy"},
    "micro-q07": {"category": "Safety & Infection Control", "ncj_step": "Generate Solutions", "difficulty": "medium"},
    "micro-q08": {"category": "Safety & Infection Control", "ncj_step": "Take Action", "difficulty": "easy"},
    "micro-q09": {"category": "Infection Control", "ncj_step": "Analyze Cues", "difficulty": "medium"},
    "micro-q10": {"category": "Pharmacological Therapies", "ncj_step": "Evaluate Outcomes", "difficulty": "medium"},
    "term-q01": {"category": "Cardiovascular", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q02": {"category": "Gastrointestinal", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q03": {"category": "Renal", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q04": {"category": "Renal", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q05": {"category": "Endocrine", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q06": {"category": "Pharmacological Therapies", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q07": {"category": "Hematologic", "ncj_step": "Analyze Cues", "difficulty": "easy"},
    "term-q08": {"category": "Respiratory", "ncj_step": "Analyze Cues", "difficulty": "easy"},
}

NCLEX_SKIP_IDS = {
    "patho-q2", "patho-q3", "patho-q4", "patho-q9", "patho-q14",
    "micro-q01", "aq-04",
}

NCLEX_SKIP_PREFIXES = ("Priority question", "Maternal-child NCLEX item")

# Curated allowlists — quality NCLEX-style items per module (target 60–80 total)
NCLEX_MODULE_ALLOWLIST: dict[str, list[str] | None] = {
    "mental_health.json": None,  # all 11
    "pathophysiology.json": [
        "patho-q1", "patho-q5", "patho-q6", "patho-q7", "patho-q8",
        "patho-q10", "patho-q11", "patho-q12", "patho-q13",
    ],
    "assessment.json": [
        "aq-01", "aq-02", "aq-03", "aq-05", "aq-15", "aq-17",
    ],
    "maternal_child.json": [f"mc-q{i:02d}" for i in range(1, 11)],
    "microbiology.json": [f"micro-q{i:02d}" for i in range(2, 11)],
    "terminology.json": [f"term-q{i:02d}" for i in range(1, 7)],
}

SYSTEM_TO_CATEGORY = {
    "cardiovascular": "Cardiovascular",
    "respiratory": "Respiratory",
    "neurological": "Neurological",
    "gastrointestinal": "Gastrointestinal",
    "renal": "Renal",
    "endocrine": "Endocrine",
    "musculoskeletal": "Musculoskeletal",
    "hematologic": "Hematologic",
    "integumentary": "Safety & Infection Control",
    "general": "Prioritization",
}


def _normalize_question(text: str) -> str:
    return " ".join(text.lower().split())


def _enrich_question(q: dict, source_module: str) -> dict:
    qid = q["id"]
    meta = NCLEX_META.get(qid, {})
    base = q.get("rationale") or q.get("explanation") or ""
    clinical = q.get("clinical_why") or q.get("clinical_judgment_focus") or ""
    rationale = NCLEX_ENHANCED_RATIONALES.get(qid)
    if not rationale:
        parts = [p.strip().rstrip(".") for p in [base, clinical] if p and p.strip()]
        seen = set()
        unique = []
        for p in parts:
            key = p.lower()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        rationale = ". ".join(unique[:3]) + ("." if unique else "")
    cj = NCLEX_CLINICAL_JUDGMENT.get(qid) or clinical or ""
    system_cat = SYSTEM_TO_CATEGORY.get(q.get("system", ""), "")
    return {
        "id": qid,
        "question": q["question"],
        "options": q["options"],
        "correct_index": q["correct_index"],
        "rationale": rationale,
        "category": meta.get("category") or q.get("category") or system_cat or "General",
        "ncj_step": meta.get("ncj_step") or q.get("ncj_step") or "Analyze Cues",
        "difficulty": meta.get("difficulty") or q.get("difficulty") or "medium",
        "source_module": source_module,
        "clinical_judgment_focus": cj,
    }


def build_nclex_prep() -> dict:
    """Aggregate NCLEX questions from med_surg and ADN module practice banks."""
    med_surg = build_med_surg()
    seen_questions: set[str] = set()
    all_questions: list[dict] = []

    def add_question(q: dict) -> None:
        key = _normalize_question(q["question"])
        if key in seen_questions:
            return
        seen_questions.add(key)
        all_questions.append(q)

    for q in med_surg["practice_questions"]:
        add_question(_enrich_question(q, "med_surg"))

    for filename, allowlist in NCLEX_MODULE_ALLOWLIST.items():
        module_id = filename.replace(".json", "")
        data = _load_json(filename)
        for q in data.get("practice_questions", []):
            qid = q.get("id", "")
            if allowlist is not None and qid not in allowlist:
                continue
            if qid in NCLEX_SKIP_IDS:
                continue
            if any(q.get("question", "").startswith(p) for p in NCLEX_SKIP_PREFIXES):
                continue
            add_question(_enrich_question(q, module_id))

    extra = [
        {
            "id": "nclex-mh-1",
            "question": "A patient states 'Nobody cares about me.' Which response uses therapeutic communication?",
            "options": [
                "You feel alone right now.",
                "That's not true — your family visits.",
                "Why would you think that?",
                "You should try to be more positive.",
            ],
            "correct_index": 0,
            "category": "Psychosocial Integrity",
            "ncj_step": "Analyze Cues",
            "difficulty": "medium",
        },
        {
            "id": "nclex-ob-1",
            "question": "A pregnant patient at 32 weeks reports sudden severe headache and visual changes. Priority action?",
            "options": [
                "Assess BP and notify provider immediately",
                "Encourage rest and dim lights",
                "Administer PRN acetaminophen",
                "Schedule routine prenatal appointment",
            ],
            "correct_index": 0,
            "category": "Maternal-Newborn",
            "ncj_step": "Recognize Cues",
            "difficulty": "hard",
        },
        {
            "id": "nclex-peds-1",
            "question": "A 4-month-old should achieve which developmental milestone?",
            "options": [
                "Rolls from back to side",
                "Walks independently",
                "Uses two-word phrases",
                "Ties shoelaces",
            ],
            "correct_index": 0,
            "category": "Pediatric Nursing",
            "ncj_step": "Analyze Cues",
            "difficulty": "easy",
        },
        {
            "id": "nclex-pharm-1",
            "question": "Order: Digoxin 0.125 mg PO daily. Apical pulse 52/min. Nurse should?",
            "options": [
                "Hold dose and notify provider",
                "Administer as ordered",
                "Give half the dose",
                "Switch to IV route",
            ],
            "correct_index": 0,
            "category": "Pharmacological Therapies",
            "ncj_step": "Take Action",
            "difficulty": "medium",
        },
        {
            "id": "nclex-safe-1",
            "question": "Fire response — nurse's first action when smoke is seen in a patient room?",
            "options": [
                "Rescue patients in immediate danger",
                "Activate fire alarm",
                "Confine fire by closing doors",
                "Extinguish fire if small",
            ],
            "correct_index": 0,
            "category": "Safety & Infection Control",
            "ncj_step": "Take Action",
            "difficulty": "easy",
        },
        {
            "id": "nclex-pharm-2",
            "question": "Before administering insulin from a vial, the nurse's priority safety action is:",
            "options": [
                "Independent double-check with second RN",
                "Administer immediately to avoid delay",
                "Dilute in normal saline",
                "Give IM for faster absorption",
            ],
            "correct_index": 0,
            "category": "Pharmacological Therapies",
            "ncj_step": "Take Action",
            "difficulty": "medium",
        },
        {
            "id": "nclex-pharm-3",
            "question": "Post-op patient received IV morphine 4 mg. RR 10/min, difficult to arouse. Nurse should:",
            "options": [
                "Stop opioid, stimulate patient, apply O2, prepare naloxone",
                "Administer next scheduled dose",
                "Place in Trendelenburg",
                "Document and recheck in 4 hours",
            ],
            "correct_index": 0,
            "category": "Pharmacological Therapies",
            "ncj_step": "Take Action",
            "difficulty": "hard",
        },
    ]
    extra_sources = {
        "nclex-mh-1": "mental_health",
        "nclex-ob-1": "maternal_child",
        "nclex-peds-1": "pediatrics",
        "nclex-pharm-1": "dosage",
        "nclex-pharm-2": "dosage",
        "nclex-pharm-3": "dosage",
        "nclex-safe-1": "assessment",
    }
    for q in extra:
        add_question(_enrich_question(q, extra_sources.get(q["id"], "nclex")))

    categories: dict[str, list] = {}
    for q in all_questions:
        cat = q["category"]
        categories.setdefault(cat, []).append(q)

    return {
        "title": "NCLEX-RN Prep Center",
        "description": "Aggregated clinical judgment practice across ADN curriculum",
        "ncj_steps": [
            "Recognize Cues",
            "Analyze Cues",
            "Prioritize Hypotheses",
            "Generate Solutions",
            "Take Action",
            "Evaluate Outcomes",
        ],
        "categories": [
            {"id": k.lower().replace(" ", "-").replace("&", "and"), "name": k, "count": len(v)}
            for k, v in sorted(categories.items())
        ],
        "questions_by_category": categories,
        "all_questions": all_questions,
        "total_questions": len(all_questions),
    }


def main():
    med_surg = build_med_surg()
    nclex = build_nclex_prep()

    (CONTENT / "med_surg.json").write_text(json.dumps(med_surg, indent=2), encoding="utf-8")
    (CONTENT / "nclex_prep.json").write_text(json.dumps(nclex, indent=2), encoding="utf-8")

    print(f"med_surg.json: {len(med_surg['body_systems'])} systems, {len(med_surg['practice_questions'])} questions")
    print(f"nclex_prep.json: {nclex['total_questions']} questions, {len(nclex['categories'])} categories")


if __name__ == "__main__":
    main()