"""Generate ~60 normal vs abnormal assessment flashcards from body_systems."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT_PATH = ROOT / "data" / "content" / "assessment.json"

# Hand-crafted high-yield cards (3 samples + expansion templates per system)
SAMPLE_CARDS = [
    {
        "id": "fc-neuro-01",
        "system": "neurological",
        "system_name": "Neurological",
        "type": "normal_vs_abnormal",
        "front": "Neurological — Pupils 3 mm bilaterally, equal, briskly reactive to light. Normal or abnormal?",
        "normal": "PERRLA — pupils 2–6 mm, equal, reactive (normal baseline).",
        "abnormal": "Unequal pupils, sluggish or non-reactive pupils, or new anisocoria.",
        "abnormal_action": "Compare to baseline; perform full neuro check (LOC, strength, speech). Notify provider for new neuro change; stroke protocol if focal deficit.",
        "clinical_why": "Pupil changes may signal increased ICP, stroke, or medication effect — time-sensitive.",
    },
    {
        "id": "fc-cardio-01",
        "system": "cardiovascular",
        "system_name": "Cardiovascular",
        "type": "normal_vs_abnormal",
        "front": "Cardiovascular — Capillary refill 4 seconds in cool, pale toes; pedal pulses weak. Normal or abnormal?",
        "normal": "Cap refill <2 seconds; strong equal peripheral pulses; pink warm extremities.",
        "abnormal": "Delayed cap refill, weak/absent pulses, cool pale extremities — perfusion concern.",
        "abnormal_action": "Obtain vital signs, assess for chest pain/SOB, notify provider. Elevate legs if hypotensive (do NOT use Trendelenburg). IV access and fluids per order.",
        "clinical_why": "Peripheral perfusion reflects cardiac output — treat the patient, not just the number.",
    },
    {
        "id": "fc-resp-01",
        "system": "respiratory",
        "system_name": "Respiratory",
        "type": "normal_vs_abnormal",
        "front": "Respiratory — Bilateral crackles at lung bases, SpO₂ 89% on room air, RR 28. Normal or abnormal?",
        "normal": "Clear breath sounds all fields; SpO₂ ≥94% on room air; effortless breathing 12–20/min.",
        "abnormal": "Crackles suggest fluid in alveoli; hypoxemia and tachypnea indicate respiratory compromise.",
        "abnormal_action": "Position upright (high Fowler's), apply O₂ per protocol, reassess SpO₂, notify provider. Auscultate systematically and monitor work of breathing.",
        "clinical_why": "Hypoxemia is a priority finding — airway and oxygenation before comfort measures.",
    },
]

# Per-system card specs: (front stem, normal snippet, abnormal snippet, action, why)
SYSTEM_CARD_SPECS: dict[str, list[tuple]] = {
    "neurological": [
        ("GCS 15, oriented ×4, speech clear", "Alert, oriented, coherent speech", "Confusion, slurred speech, word-finding difficulty", "Full neuro assessment; note onset time; stroke protocol if focal deficit", "Acute neuro change requires immediate escalation."),
        ("Strength 5/5 all extremities bilaterally", "Equal strength 5/5", "Unilateral weakness or numbness", "FAST screen; notify provider; document last-known-well", "Unilateral weakness suggests stroke until ruled out."),
        ("Steady gait, no assistive device needed", "Steady coordinated gait", "Unsteady gait, inability to move extremity", "Fall precautions; neuro checks; PT consult per order", "Gait change may reflect weakness, meds, or orthostasis."),
        ("No seizure activity observed", "No seizure activity", "Active seizure or post-ictal confusion", "Protect airway, turn to side, time seizure, notify provider", "Seizure = airway and safety priority."),
    ],
    "cardiovascular": [
        ("Apical pulse regular 78/min, S1/S2 without extra sounds", "Regular rate 60–100; S1/S2 only", "Irregular rhythm, murmur, gallop S3/S4", "12-lead ECG if symptomatic; notify provider; continuous monitoring if ordered", "New arrhythmia may reduce cardiac output."),
        ("No pitting edema; JVD not visible at 45°", "No edema; no JVD", "Pitting edema, JVD at 45°", "Daily weights, strict I&O, elevate legs, notify provider", "Edema + JVD suggest fluid overload/heart failure."),
        ("BP 118/72, HR 72, warm pink extremities", "Stable vitals; good perfusion", "SBP <90 with symptoms, HR <40 or >150", "Supine, leg elevation if tolerated, IV fluids per order, notify provider", "Hypotension with symptoms = perfusion emergency."),
        ("Chest pain absent; denies SOB", "No chest pain", "Chest pain + diaphoresis + SOB", "12-lead ECG, vitals, aspirin per protocol, notify provider immediately", "ACS presentation requires time-sensitive intervention."),
    ],
    "respiratory": [
        ("Symmetric chest rise; clear breath sounds", "Symmetric expansion; clear lungs", "Accessory muscle use, asymmetric expansion", "Position upright, O₂, peak flow/IS if ordered, notify provider", "Increased work of breathing signals distress."),
        ("SpO₂ 97% on room air, RR 16", "SpO₂ ≥94% RA; RR 12–20", "SpO₂ <94%, tachypnea", "Apply O₂, reassess, notify if not improving", "Hypoxemia needs correction before routine care."),
        ("No cough; sputum clear/white if present", "No productive cough", "Productive cough with colored sputum, hemoptysis", "Culture per order; isolation if TB suspected; notify provider", "Purulent sputum suggests infection; hemoptysis is urgent."),
        ("No wheezes; good air entry all fields", "Clear breath sounds", "Wheezes, rhonchi, diminished sounds, silent chest", "Bronchodilator per order; prepare for escalation if silent chest", "Silent chest in asthma = impending respiratory failure."),
    ],
    "gastrointestinal": [
        ("Abdomen soft, non-tender; active BS ×4", "Soft, non-tender; active bowel sounds", "Distension, absent/hyperactive BS, guarding", "NPO if surgical concern; notify provider; NG tube per order", "Absent BS + distension suggests ileus/obstruction."),
        ("Regular BM pattern; no nausea", "Regular elimination; no NV", "Diarrhea, constipation, melena, hematochezia", "Stool sample per order; monitor H&H; GI bleed protocol if indicated", "GI bleeding can cause rapid hemodynamic collapse."),
        ("No rebound tenderness or rigidity", "Non-tender abdomen", "Rebound tenderness, rigid board-like abdomen", "NPO, IV access, notify surgeon/provider — no laxatives/enemas", "Rigid abdomen = surgical emergency until proven otherwise."),
        ("Last BM yesterday, soft brown stool", "Normal elimination", "Projectile vomiting, coffee-ground emesis", "NPO, NG decompression per order, notify provider", "Coffee-ground emesis suggests upper GI bleed."),
    ],
    "genitourinary": [
        ("Voiding without difficulty; urine clear yellow", "Normal voiding pattern", "Oliguria, dysuria, hematuria", "Strict I&O; bladder scan; notify provider", "Oliguria may signal AKI or obstruction."),
        ("No suprapubic fullness", "No bladder distension", "Palpable distended bladder, acute retention", "Bladder scan; straight catheter per order; monitor output", "Retention can cause AKI and discomfort."),
        ("Urine output 50 mL/hr", "Adequate urine output", "Anuria or <30 mL/hr", "Assess hydration, catheter patency; notify provider", "Anuria with pain suggests obstruction."),
        ("No flank pain or fever", "No GU pain", "Flank pain + fever + CVA tenderness", "Urine culture per order; antipyretics; notify provider", "Pyelonephritis requires prompt treatment."),
    ],
    "musculoskeletal": [
        ("Full ROM all joints without pain", "Full painless ROM", "Limited ROM, pain with movement", "Immobilize if trauma; pain management; imaging per order", "Pain-limited ROM after injury needs evaluation."),
        ("Strength 5/5 major muscle groups", "Strength 5/5", "Weakness grade <5", "Compare bilaterally; neuro checks distal to injury", "New weakness may be neuro or musculoskeletal emergency."),
        ("Steady gait, independent ambulation", "Steady gait", "Unable to bear weight after fall", "Fall precautions; imaging per trauma protocol; pain control", "Hip/pelvis fracture common in older adult falls."),
        ("No swelling or deformity at joints", "No joint deformity", "Hot swollen joint with fever", "Notify provider; joint aspiration per order; infection workup", "Septic arthritis is orthopedic emergency."),
    ],
    "integumentary": [
        ("Skin warm, dry, intact; turgor elastic", "Intact skin; turgor <2 sec", "Poor turgor, tenting — dehydration", "Encourage fluids if appropriate; IV fluids per order; monitor I&O", "Poor turgor signals dehydration, especially in older adults."),
        ("Even skin color; no open areas", "Even coloration; intact skin", "Pallor, cyanosis, jaundice, mottling", "Assess perfusion and O₂; notify provider for acute color change", "Acute cyanosis = oxygenation/perfusion problem."),
        ("No pressure injury present", "Intact skin over bony prominences", "Stageable pressure injury or purple maroon areas (DTI)", "Reposition q2h, Braden interventions, notify wound team", "Pressure injuries worsen quickly — prevention is nursing priority."),
        ("Small bruise 1 cm, non-tender", "Expected minor ecchymosis", "Rapidly spreading petechiae/purpura + fever", "Notify provider; blood cultures if ordered; monitor LOC", "Purpura + fever may indicate serious infection or DIC."),
    ],
    "heent": [
        ("PERRLA; conjunctiva pink; sclera white", "PERRLA; pink conjunctiva", "Unequal pupils, sluggish reactivity", "Neuro check; notify provider; avoid opioids if RR depressed", "New anisocoria with LOC change = neuro emergency."),
        ("Moist pink oral mucosa", "Moist mucous membranes", "Dry cracked lips, oral lesions, thrush", "Oral care; hydration; swab if NPO; notify for painful lesions", "Dry mucosa reflects hydration and infection risk."),
        ("Face symmetric at rest and with smile", "Facial symmetry", "Unilateral facial droop", "FAST stroke screen; note onset; notify provider immediately", "Facial droop is stroke sign until proven otherwise."),
        ("Nares patent bilaterally; no drainage", "Patent nares", "Purulent nasal drainage, epistaxis uncontrolled", "Notify provider; apply pressure for epistaxis; airway watch", "Uncontrolled epistaxis or angioedema threatens airway."),
    ],
    "psychosocial": [
        ("Mood appropriate; denies SI/HI", "Appropriate affect; denies self-harm", "Hopelessness, expresses desire to harm self", "Direct suicide screening; 1:1 per protocol; remove harmful items", "Active SI with plan requires immediate safety intervention."),
        ("Coherent thought process; engaged", "Coherent, goal-directed", "Disorganized thought, responding to internal stimuli", "Therapeutic communication; low stimulation; notify provider", "Psychosis may impair ability to participate in care."),
        ("Identifies support persons", "Support system identified", "Signs of neglect or abuse disclosed", "Mandatory reporting per state law; separate interview if safe", "Abuse disclosure triggers legal and safety obligations."),
        ("Calm, cooperative with care", "Calm cooperative behavior", "Severe agitation with violence risk", "De-escalation; 1:1 observation; medication per order", "Agitation threatens patient and staff safety."),
    ],
    "endocrine-immune": [
        ("Thyroid non-palpable; no tremor", "Non-palpable smooth thyroid", "Goiter, nodule, exophthalmos, tremor", "Vitals including temp/HR; TSH per order; notify provider", "Thyroid storm/myxedema crisis are endocrine emergencies."),
        ("Lymph nodes small, mobile, non-tender", "Small mobile nodes", "Hard fixed nodes, tender enlarged nodes", "Document size/location; notify provider; infection/malignancy workup", "Fixed supraclavicular node suggests malignancy."),
        ("Skin intact; wounds healing normally", "Intact healing skin", "Frequent infections, poor wound healing", "Infection precautions; glucose if diabetic; notify provider", "Immunocompromise blunts classic inflammation signs."),
        ("Fingerstick glucose 110 mg/dL, alert", "Euglycemia with normal LOC", "Glucose <70 or >400 with altered LOC", "Hypoglycemia protocol (15 g fast carb); notify provider for hyperglycemia crisis", "Hypoglycemia causes confusion, seizures, and falls."),
    ],
}


def _make_card(system_id: str, system_name: str, idx: int, spec: tuple) -> dict:
    front_stem, normal, abnormal, action, why = spec
    return {
        "id": f"fc-{system_id[:4]}-{idx:02d}",
        "system": system_id,
        "system_name": system_name,
        "type": "normal_vs_abnormal",
        "front": f"{system_name} — {front_stem}. Normal or abnormal?",
        "normal": normal,
        "abnormal": abnormal,
        "abnormal_action": action,
        "clinical_why": why,
    }


def generate_all_cards() -> list[dict]:
    cards = list(SAMPLE_CARDS)
    seen_ids = {c["id"] for c in cards}

    data = json.loads(ASSESSMENT_PATH.read_text(encoding="utf-8"))
    for sys in data.get("body_systems", []):
        sid = sys["id"]
        name = sys["name"]
        specs = SYSTEM_CARD_SPECS.get(sid, [])
        for i, spec in enumerate(specs, start=1):
            card = _make_card(sid, name, i, spec)
            if card["id"] in seen_ids:
                card["id"] = f"fc-{sid}-{i:02d}"
            cards.append(card)
            seen_ids.add(card["id"])

    # High-yield red-flag recognition cards
    red_flag_cards = [
        {
            "id": "fc-rf-01",
            "system": "neurological",
            "system_name": "Neurological",
            "type": "red_flag",
            "front": "RED FLAG — Sudden worst headache of life with stiff neck and fever. Priority action?",
            "normal": "Mild tension headache without neuro deficit (context-dependent).",
            "abnormal": "Thunderclap headache + meningeal signs — meningitis/subarachnoid hemorrhage concern.",
            "abnormal_action": "Neuro/vitals stat; notify provider; prepare for CT/LP per order; seizure precautions.",
            "clinical_why": "Thunderclap headache is a neuro emergency until proven otherwise.",
        },
        {
            "id": "fc-rf-02",
            "system": "cardiovascular",
            "system_name": "Cardiovascular",
            "type": "red_flag",
            "front": "RED FLAG — Sudden unilateral leg swelling, warmth, and pain. Concern?",
            "normal": "Mild bilateral ankle edema at end of day (common in venous insufficiency).",
            "abnormal": "Unilateral calf swelling + pain — DVT until ruled out; PE risk if dyspneic.",
            "abnormal_action": "Do not massage leg; notify provider; anticoagulation/imaging per order; monitor SpO₂.",
            "clinical_why": "DVT/PE is a leading preventable cause of hospital death.",
        },
        {
            "id": "fc-rf-03",
            "system": "respiratory",
            "system_name": "Respiratory",
            "type": "red_flag",
            "front": "RED FLAG — Audible stridor at rest, SpO₂ 90%. First nursing action?",
            "normal": "Mild wheeze with good air exchange on bronchodilator (asthma stable).",
            "abnormal": "Stridor = upper airway narrowing — impending obstruction.",
            "abnormal_action": "Call for help; airway equipment to bedside; notify provider/rapid response; calm positioning.",
            "clinical_why": "Stridor is an airway emergency — minutes matter.",
        },
        {
            "id": "fc-rf-04",
            "system": "gastrointestinal",
            "system_name": "Gastrointestinal",
            "type": "red_flag",
            "front": "RED FLAG — Rigid, board-like abdomen with rebound tenderness. Your action?",
            "normal": "Mild post-prandial fullness without tenderness.",
            "abnormal": "Peritoneal signs — surgical abdomen until proven otherwise.",
            "abnormal_action": "NPO, IV access, notify surgeon/provider, vitals q15min — no enemas/laxatives.",
            "clinical_why": "Peritonitis progresses to sepsis and perforation without intervention.",
        },
        {
            "id": "fc-rf-05",
            "system": "genitourinary",
            "system_name": "Genitourinary",
            "type": "red_flag",
            "front": "RED FLAG — Post-op patient anuric 10 hours with suprapubic distension. Action?",
            "normal": "Voiding within 6–8 hours post-op with adequate output.",
            "abnormal": "Acute urinary retention — bladder distension, AKI risk.",
            "abnormal_action": "Bladder scan; straight catheter per order; strict I&O; notify provider.",
            "clinical_why": "Retention causes pain, infection, and renal injury if prolonged.",
        },
        {
            "id": "fc-rf-06",
            "system": "musculoskeletal",
            "system_name": "Musculoskeletal",
            "type": "red_flag",
            "front": "RED FLAG — Casted leg: pain unrelieved by opioids, pain on passive toe extension, toes cool. Diagnosis concern?",
            "normal": "Expected surgical pain managed with ordered analgesia.",
            "abnormal": "Pain out of proportion + pain with passive stretch — compartment syndrome.",
            "abnormal_action": "Remove restrictive dressings/cast per protocol; notify provider immediately; do not elevate leg.",
            "clinical_why": "Compartment syndrome causes irreversible tissue damage within hours.",
        },
        {
            "id": "fc-rf-07",
            "system": "integumentary",
            "system_name": "Integumentary (Skin)",
            "type": "red_flag",
            "front": "RED FLAG — Wound with exposed bone on coccyx. How do you stage/document?",
            "normal": "Intact skin or Stage 1 non-blanchable erythema only.",
            "abnormal": "Full-thickness tissue loss with visible bone = Stage 4 pressure injury.",
            "abnormal_action": "Photo per policy; wound consult; pressure redistribution; never reverse stage.",
            "clinical_why": "Accurate staging drives treatment and quality reporting.",
        },
        {
            "id": "fc-rf-08",
            "system": "heent",
            "system_name": "HEENT",
            "type": "red_flag",
            "front": "RED FLAG — Trauma patient with Battle sign and clear fluid from nose. Concern?",
            "normal": "Minor epistaxis controlled with pressure.",
            "abnormal": "Battle sign + CSF rhinorrhea — basilar skull fracture.",
            "abnormal_action": "C-spine precautions; notify trauma team; NPO; neuro checks.",
            "clinical_why": "Basilar skull fracture risks meningitis and neuro complications.",
        },
        {
            "id": "fc-rf-09",
            "system": "psychosocial",
            "system_name": "Psychosocial",
            "type": "red_flag",
            "front": "RED FLAG — Patient states specific suicide plan with pills in room. Priority?",
            "normal": "Passive death wish without plan or means (still assess fully).",
            "abnormal": "Active suicidal ideation with plan and means — imminent risk.",
            "abnormal_action": "1:1 observation; remove means; notify provider/charge nurse; document exact quotes.",
            "clinical_why": "Highest-risk patients need immediate safety interventions.",
        },
        {
            "id": "fc-rf-10",
            "system": "endocrine-immune",
            "system_name": "Endocrine & Immune",
            "type": "red_flag",
            "front": "RED FLAG — Diabetic patient: glucose 42 mg/dL, diaphoretic, confused. Action?",
            "normal": "Fasting glucose 70–100 mg/dL with normal LOC.",
            "abnormal": "Symptomatic hypoglycemia — neuroglycopenia risk.",
            "abnormal_action": "15 g fast-acting carb if able to swallow safely; glucagon/IV dextrose per order; recheck in 15 min.",
            "clinical_why": "Hypoglycemia causes falls, seizures, and death if untreated.",
        },
        {
            "id": "fc-rf-11",
            "system": "respiratory",
            "system_name": "Respiratory",
            "type": "red_flag",
            "front": "RED FLAG — Asthma patient: silent chest, exhausted, SpO₂ 88%. Meaning?",
            "normal": "Audible wheezes with good air movement on bronchodilator.",
            "abnormal": "Silent chest = severe bronchospasm with minimal air movement — impending failure.",
            "abnormal_action": "Call rapid response; continuous nebs per order; prepare for intubation; monitor ABG.",
            "clinical_why": "Decreasing wheeze with fatigue signals deterioration, not improvement.",
        },
        {
            "id": "fc-rf-12",
            "system": "cardiovascular",
            "system_name": "Cardiovascular",
            "type": "red_flag",
            "front": "RED FLAG — HR 168 irregular, BP 86/50, dizzy. Priority?",
            "normal": "Stable sinus rhythm 60–100 with normotension.",
            "abnormal": "Unstable tachyarrhythmia with hypotension — perfusion compromised.",
            "abnormal_action": "Continuous monitoring; IV access; notify provider; cardioversion/meds per ACLS protocol.",
            "clinical_why": "Unstable arrhythmia requires immediate treatment to restore perfusion.",
        },
        {
            "id": "fc-rf-13",
            "system": "gastrointestinal",
            "system_name": "Gastrointestinal",
            "type": "red_flag",
            "front": "RED FLAG — Post-op absent bowel sounds, distension, vomiting fecal material.",
            "normal": "Hypoactive BS first 24–48 hr post-op without distension.",
            "abnormal": "Obstruction/ileus — feculent vomitus is late sign.",
            "abnormal_action": "NPO, NG decompression per order, IV fluids, notify surgeon.",
            "clinical_why": "Bowel obstruction can cause perforation and sepsis.",
        },
        {
            "id": "fc-rf-14",
            "system": "neurological",
            "system_name": "Neurological",
            "type": "red_flag",
            "front": "RED FLAG — GCS drops from 15 to 12 over 2 hours post head injury.",
            "normal": "Stable GCS 15 after minor head injury with improving symptoms.",
            "abnormal": "Declining GCS — expanding intracranial lesion until ruled out.",
            "abnormal_action": "Neuro checks q15min; notify provider; CT head per trauma protocol.",
            "clinical_why": "GCS decline ≥2 points warrants urgent neuro imaging.",
        },
        {
            "id": "fc-rf-15",
            "system": "vital_signs",
            "system_name": "Vital Signs",
            "type": "red_flag",
            "front": "RED FLAG — Infant RR 65, nasal flaring, retractions, SpO₂ 91%.",
            "normal": "Infant RR ~30–60 with easy breathing (age-dependent).",
            "abnormal": "Respiratory distress with hypoxemia — not normal tachypnea alone.",
            "abnormal_action": "Position; O₂; notify provider; prepare for escalation; suction if needed.",
            "clinical_why": "Pediatric patients decompensate quickly — assess work of breathing, not rate alone.",
        },
    ]
    for rc in red_flag_cards:
        if rc["id"] not in seen_ids:
            cards.append(rc)
            seen_ids.add(rc["id"])

    # Vital signs bonus cards
    vital_cards = [
        {
            "id": "fc-vitals-01",
            "system": "vital_signs",
            "system_name": "Vital Signs",
            "type": "normal_vs_abnormal",
            "front": "Adult temp 101.8°F (38.8°C), HR 112, BP 102/64. Normal or abnormal?",
            "normal": "Temp 97.8–99°F (36.5–37.2°C); HR 60–100; BP ~120/80 baseline varies.",
            "abnormal": "Fever with tachycardia and relative hypotension — possible infection with sepsis risk.",
            "abnormal_action": "Blood cultures per order, antipyretics, fluids, notify provider; sepsis screening.",
            "clinical_why": "Fever + tachycardia + hypotension = systemic inflammatory response — escalate early.",
        },
        {
            "id": "fc-vitals-02",
            "system": "vital_signs",
            "system_name": "Vital Signs",
            "type": "normal_vs_abnormal",
            "front": "Orthostatic vitals: lying BP 120/80 → standing BP 100/70 with dizziness. Normal or abnormal?",
            "normal": "SBP drop <20 mmHg and DBP drop <10 mmHg without symptoms on standing.",
            "abnormal": "Drop ≥20 SBP or ≥10 DBP with dizziness — orthostatic hypotension.",
            "abnormal_action": "Fall precautions, gradual position changes, fluids per order, review medications.",
            "clinical_why": "Orthostasis increases fall risk — common with diuretics, dehydration, and older adults.",
        },
    ]
    for vc in vital_cards:
        if vc["id"] not in seen_ids:
            cards.append(vc)

    return cards


def main():
    cards = generate_all_cards()
    data = json.loads(ASSESSMENT_PATH.read_text(encoding="utf-8"))
    data["flashcards"] = cards
    ASSESSMENT_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(cards)} flashcards")


if __name__ == "__main__":
    main()