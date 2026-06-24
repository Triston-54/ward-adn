#!/usr/bin/env python3
"""Final production pass — expand pediatrics, NCLEX prioritization/safety, sync counts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data" / "content"

PEDS_EXPANSION = [
    {
        "id": "peds-vitals-infant",
        "title": "Pediatric Vital Sign Norms — Infant (0–12 mo)",
        "category": "Growth & Vitals",
        "content": "HR 100–160, RR 30–60, BP ~70–100/50–65 systolic. Temperature: rectal most accurate in infants.",
        "key_points": [
            "Bradycardia in infant often signals hypoxia — assess ABCs before assuming sleep",
            "Cap refill >2 sec suggests poor perfusion",
            "Pulse ox on right hand pre-ductal in newborn if concern for CHD",
        ],
        "nursing_actions": [
            "Use length-based resuscitation tape (Broselow) for weight-based dosing",
            "Trend vitals; single reading less meaningful than pattern",
        ],
        "clinical_why": "Age-specific norms prevent mislabeling normal infant tachycardia as emergency or missing true decompensation.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-vitals-toddler",
        "title": "Pediatric Vital Sign Norms — Toddler (1–3 yr)",
        "category": "Growth & Vitals",
        "content": "HR 90–150, RR 24–40. Fear and crying elevate HR/RR — allow calm period before reassessment.",
        "key_points": [
            "Communicate at eye level; use simple words",
            "Parent presence reduces anxiety and improves cooperation",
            "Weight in kg required for all pediatric medication calculations",
        ],
        "nursing_actions": [
            "Explain procedures in developmentally appropriate language",
            "Offer choices when safe (which arm for BP)",
        ],
        "clinical_why": "Toddlers cannot articulate symptoms — behavioral cues and parent report are primary assessment data.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-vitals-schoolage",
        "title": "Pediatric Vital Sign Norms — School Age (6–12 yr)",
        "category": "Growth & Vitals",
        "content": "HR 70–120, RR 18–30, BP approaching adult ranges by adolescence.",
        "key_points": [
            "Children may minimize pain — observe gait, activity, facial expression",
            "School-age children understand cause-effect; brief honest explanations build trust",
        ],
        "nursing_actions": [
            "Involve child in care when appropriate",
            "Screen for anxiety about procedures",
        ],
        "clinical_why": "Normal ranges widen with age — applying adult vital sign alarms causes false emergencies.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-communication",
        "title": "Family-Centered & Developmental Communication",
        "category": "Pediatric Safety",
        "content": "Assess the child within the context of family; include caregivers in teaching. Use therapeutic touch, distraction, and play for younger children.",
        "key_points": [
            "Infants: nonverbal cues (tone, touch, feeding)",
            "Toddlers: short sentences, concrete terms, avoid 'don't hurt'",
            "Adolescents: confidential time; assess risk behaviors respectfully",
        ],
        "nursing_actions": [
            "Ask parent what calms the child",
            "Use Child Life services when available",
        ],
        "clinical_why": "NCLEX Psychosocial Integrity emphasizes family-centered care and age-appropriate interaction.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-sids",
        "title": "SIDS Prevention & Safe Sleep",
        "category": "Pediatric Safety",
        "content": "ABC: Alone, on Back, in Crib. Firm flat surface, no soft bedding, smoke-free environment.",
        "key_points": [
            "Supine sleeping every sleep period until 1 year",
            "Room-sharing without bed-sharing recommended first 6 months",
            "Pacifier at nap/bedtime after breastfeeding established",
        ],
        "nursing_actions": [
            "Model safe sleep in hospital",
            "Teach parents to avoid overlays, bumpers, inclined sleepers",
        ],
        "clinical_why": "Safe sleep teaching is a high-yield NCLEX Health Promotion item linked to sudden unexpected infant death reduction.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-choking",
        "title": "Choking & Foreign Body Aspiration",
        "category": "Pediatric Safety",
        "content": "Toddlers explore orally — coins, grapes, hot dogs are common aspirated objects. Partial obstruction may have stridor and cough; complete obstruction is silent with ineffective cough.",
        "key_points": [
            "Infant: 5 back blows + 5 chest thrusts",
            "Child >1 yr: abdominal thrusts (Heimlich)",
            "Cut food to <½ inch; avoid round firm foods for toddlers",
        ],
        "nursing_actions": [
            "Assess airway before any other intervention",
            "Call code/respond per facility BLS protocol",
        ],
        "clinical_why": "Airway obstruction is an immediate life threat — NCLEX prioritization favors airway interventions first.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-medication-safety",
        "title": "Pediatric Medication Safety",
        "category": "Pediatric Safety",
        "content": "Always verify weight in kg. Never use 'teaspoon' household measures. Liquid concentrations vary — read label every time.",
        "key_points": [
            "mg/kg dosing — double-check with another nurse",
            "Never administer adult tablets split without pharmacy approval",
            "Topical medications absorb faster in infants — systemic toxicity risk",
        ],
        "nursing_actions": [
            "Use oral syringe not kitchen spoon",
            "Document site for topical meds; teach parents",
        ],
        "clinical_why": "Pediatric dosing errors are a leading cause of preventable harm — dimensional analysis and weight verification are NCLEX staples.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-lead-poisoning",
        "title": "Lead Poisoning Screening",
        "category": "Growth & Development",
        "content": "CDC: screen all children at 12 and 24 months; high-risk areas may need earlier/more frequent screening.",
        "key_points": [
            "Pica, developmental delay, irritability may present",
            "Old paint, imported toys, water pipes are exposure sources",
        ],
        "nursing_actions": [
            "Refer elevated BLL per local health department protocol",
            "Teach handwashing and wet-mop dust control",
        ],
        "clinical_why": "Environmental health screening is Health Promotion — anticipatory guidance prevents irreversible neurodevelopmental injury.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-adolescent-confidentiality",
        "title": "Adolescent Health & Confidentiality",
        "category": "Pediatric Safety",
        "content": "Assess STI risk, substance use, depression, and safety confidentially when state law permits. Balance autonomy with mandatory reporting for abuse/harm.",
        "key_points": [
            "HEADSS assessment: Home, Education, Activities, Drugs, Sexuality, Suicide",
            "HPV, meningococcal, Tdap boosters per adolescent schedule",
        ],
        "nursing_actions": [
            "Provide private interview time",
            "Know mandatory reporting obligations",
        ],
        "clinical_why": "Adolescents disclose sensitive information only when trust and privacy are protected.",
        "source_ref": "maternal_child",
    },
    {
        "id": "peds-croup",
        "title": "Croup (Laryngotracheobronchitis)",
        "category": "Pediatric Respiratory",
        "content": "Barking cough, inspiratory stridor, hoarseness — often worse at night. Mild: cool mist; severe: racemic epinephrine and steroids per order.",
        "key_points": [
            "Stridor at rest = severe — continuous monitoring",
            "Avoid agitating child; stress worsens obstruction",
        ],
        "nursing_actions": [
            "Position of comfort; humidified air",
            "Notify provider for stridor at rest or retractions",
        ],
        "clinical_why": "Pediatric airway edema can progress rapidly — early escalation prevents respiratory arrest.",
        "source_ref": "maternal_child",
    },
]

IMMUNIZATION_SCHEDULE = [
    {"vaccine": "Hepatitis B", "age": "Birth, 1–2 mo, 6–18 mo", "nursing_considerations": "Birth dose within 24 hr; document lot and site. Screen maternal HBsAg status."},
    {"vaccine": "DTaP", "age": "2, 4, 6, 15–18 mo; 4–6 yr", "nursing_considerations": "Local reaction common; fever — antipyretic per order. Contraindicated if encephalopathy within 7 days of prior dose."},
    {"vaccine": "IPV (Polio)", "age": "2, 4, 6–18 mo; 4–6 yr", "nursing_considerations": "IM or SQ per product; observe 15 min post-vaccination."},
    {"vaccine": "Hib", "age": "2, 4, 6, 12–15 mo", "nursing_considerations": "Protects against Haemophilus influenzae type b meningitis/epiglottitis."},
    {"vaccine": "PCV13/15", "age": "2, 4, 6, 12–15 mo", "nursing_considerations": "Pneumococcal conjugate — reduces otitis, pneumonia, bacteremia."},
    {"vaccine": "Rotavirus", "age": "2, 4 mo (series)", "nursing_considerations": "Oral vaccine; latex allergy caution with some applicators."},
    {"vaccine": "MMR", "age": "12–15 mo; 4–6 yr", "nursing_considerations": "Live attenuated — avoid in severe immunocompromise; give VIS sheet."},
    {"vaccine": "Varicella", "age": "12–15 mo; 4–6 yr", "nursing_considerations": "Airborne + contact precautions if active varicella in susceptible contacts."},
    {"vaccine": "Hepatitis A", "age": "12–23 mo (2-dose series)", "nursing_considerations": "Recommended for all children; travel/endemic exposure teaching."},
    {"vaccine": "Influenza", "age": "Annual ≥6 mo", "nursing_considerations": "First season: 2 doses if <8 yr and previously unvaccinated."},
    {"vaccine": "HPV", "age": "11–12 yr (2-dose if started <15)", "nursing_considerations": "Cancer prevention; counsel on syncope after injection in adolescents."},
    {"vaccine": "Tdap", "age": "11–12 yr booster", "nursing_considerations": "Pertussis protection wanes — adolescent booster protects infants via cocooning."},
    {"vaccine": "Meningococcal ACWY", "age": "11–12 yr; booster 16 yr", "nursing_considerations": "Required for college/military in many states; MenB separate series for high risk."},
]

PEDS_FLASHCARDS = [
    {"id": "peds-fc-01", "front": "Infant HR normal range", "back": "100–160 bpm — bradycardia may signal hypoxia", "category": "Pediatric"},
    {"id": "peds-fc-02", "front": "Neonatal fever emergency", "back": "≤28 days with rectal temp ≥38°C (100.4°F) = full sepsis workup", "category": "Pediatric"},
    {"id": "peds-fc-03", "front": "Safe sleep (SIDS)", "back": "Alone, on Back, in Crib — firm surface, no soft bedding", "category": "Pediatric Safety"},
    {"id": "peds-fc-04", "front": "4-month milestones", "back": "Rolls back→side, social smile, reaches for objects, improved head control", "category": "Pediatric Milestones"},
    {"id": "peds-fc-05", "front": "12-month milestones", "back": "Walks with support/first steps, single words, object permanence", "category": "Pediatric Milestones"},
    {"id": "peds-fc-06", "front": "Pediatric pain — infant", "back": "FLACC scale: Face, Legs, Activity, Cry, Consolability", "category": "Pediatric"},
    {"id": "peds-fc-07", "front": "Never give children", "back": "Aspirin — Reye syndrome risk with viral illness", "category": "Pediatric Safety"},
    {"id": "peds-fc-08", "front": "Choking infant", "back": "5 back blows + 5 chest thrusts — do not blind finger sweep", "category": "Pediatric Safety"},
    {"id": "peds-fc-09", "front": "Varicella precautions", "back": "Airborne AND contact until lesions crusted (CDC)", "category": "Pediatric"},
    {"id": "peds-fc-10", "front": "Weight-based dosing", "back": "Always kg; oral syringe; verify concentration (mg/mL)", "category": "Pediatric Safety"},
]

NCLEX_NEW = [
    {
        "id": "nclex-prio-02",
        "question": "Four patients call the nurse simultaneously. Who should be assessed first?",
        "options": [
            "Post-op day 1 requesting pain medication rated 6/10",
            "Client with new onset chest pain and diaphoresis",
            "Client awaiting discharge teaching for insulin injection",
            "Client with a medication due in 30 minutes",
        ],
        "correct_index": 1,
        "rationale": "New chest pain with diaphoresis suggests acute coronary syndrome — a potential life threat requiring immediate assessment (ABCs, ECG, vitals, provider notification). Pain medication, discharge teaching, and a medication due in 30 minutes are important but not emergent compared to possible myocardial infarction.",
        "category": "Prioritization",
        "ncj_step": "Prioritize Hypotheses",
        "difficulty": "medium",
        "source_module": "med_surg",
        "clinical_judgment_focus": "Unstable vs. stable — acute cardiac symptoms outrank comfort and routine tasks.",
    },
    {
        "id": "nclex-prio-03",
        "question": "After receiving report, which client should the nurse see first?",
        "options": [
            "Diabetic client whose breakfast tray just arrived",
            "Client with COPD whose SpO2 dropped from 94% to 88% with increased work of breathing",
            "Client requesting assistance to the bathroom",
            "Client scheduled for physical therapy at 1000",
        ],
        "correct_index": 1,
        "rationale": "Declining oxygen saturation with increased work of breathing signals respiratory compromise — assess airway, position, O₂ delivery, and notify provider. Meal timing, toileting, and scheduled therapy are lower priority than potential respiratory failure.",
        "category": "Prioritization",
        "ncj_step": "Recognize Cues",
        "difficulty": "medium",
        "source_module": "med_surg",
        "clinical_judgment_focus": "Trending vital sign changes trump scheduled activities.",
    },
    {
        "id": "nclex-prio-04",
        "question": "The nurse has 15 minutes left in shift. Which task is best delegated to an unlicensed assistive personnel (UAP)?",
        "options": [
            "Ambulating a post-op client day 1 after abdominal surgery",
            "Feeding an alert stroke client with mild dysphagia",
            "Obtaining routine vital signs on stable clients",
            "Reinforcing discharge teaching about wound care",
        ],
        "correct_index": 2,
        "rationale": "Routine vital signs on stable clients are within UAP scope when no unstable findings are expected. Post-op ambulation, dysphagia feeding, and discharge teaching require nursing assessment and judgment — inappropriate to delegate.",
        "category": "Prioritization",
        "ncj_step": "Generate Solutions",
        "difficulty": "medium",
        "source_module": "med_surg",
        "clinical_judgment_focus": "Delegation requires matching task stability with caregiver scope.",
    },
    {
        "id": "nclex-prio-05",
        "question": "Which finding requires immediate nursing intervention?",
        "options": [
            "Report of dry mouth after starting antihistamine",
            "Urine output 35 mL/hr for the past 2 hours",
            "New onset confusion and slurred speech",
            "Incisional pain rated 4/10 after analgesic given 1 hour ago",
        ],
        "correct_index": 2,
        "rationale": "Acute confusion and slurred speech may indicate stroke, hypoglycemia, sepsis, or medication toxicity — all require immediate assessment (glucose, neuro checks, vitals). Dry mouth is an expected antihistamine effect; 35 mL/hr meets minimum adult output; mild pain after recent analgesic is monitored but not emergent.",
        "category": "Prioritization",
        "ncj_step": "Recognize Cues",
        "difficulty": "hard",
        "source_module": "assessment",
        "clinical_judgment_focus": "Neurological acute changes are always high priority.",
    },
    {
        "id": "nclex-safe-02",
        "question": "Before administering a scheduled opioid, the nurse notes respirations 8/min and the client is difficult to arouse. What is the priority action?",
        "options": [
            "Administer the opioid as scheduled and recheck in 30 minutes",
            "Hold the opioid, assess further, and notify provider — consider naloxone per protocol",
            "Document and continue routine care",
            "Offer a snack to stimulate the client",
        ],
        "correct_index": 1,
        "rationale": "Respiratory depression (RR <10) with decreased level of consciousness indicates opioid toxicity — hold further opioids, maintain airway, stimulate/support respirations, notify provider, and prepare naloxone per facility protocol. Administering another dose could cause arrest.",
        "category": "Safety & Infection Control",
        "ncj_step": "Take Action",
        "difficulty": "hard",
        "source_module": "dosage",
        "clinical_judgment_focus": "Medication safety — assess before administering sedating drugs.",
    },
    {
        "id": "nclex-safe-03",
        "question": "A nurse discovers a client on the floor beside the bed, alert and complaining of hip pain. What is the first action?",
        "options": [
            "Help client back to bed immediately",
            "Assess client and call for help per fall protocol",
            "Complete incident report before assessment",
            "Obtain x-ray order before moving client",
        ],
        "correct_index": 1,
        "rationale": "After a fall, assess for injury and neurological status before moving the client. Call for help and follow facility fall protocol — do not lift alone if hip fracture suspected. Incident reporting follows assessment and stabilization, not before.",
        "category": "Safety & Infection Control",
        "ncj_step": "Take Action",
        "difficulty": "medium",
        "source_module": "assessment",
        "clinical_judgment_focus": "Client safety — assess injury before movement or documentation tasks.",
    },
    {
        "id": "nclex-safe-04",
        "question": "Which action prevents central line-associated bloodstream infection (CLABSI)?",
        "options": [
            "Change transparent dressing every 7 days per policy and use chlorhexidine scrub",
            "Flush with heparin only when line is used",
            "Remove cap and leave hub open during transport",
            "Administer prophylactic IV antibiotics daily",
        ],
        "correct_index": 0,
        "rationale": "CLABSI bundles include hand hygiene, maximal barrier precautions on insertion, chlorhexidine skin prep, appropriate dressing changes, and hub disinfection before access. Open hubs and routine prophylactic antibiotics are not evidence-based and increase risk.",
        "category": "Safety & Infection Control",
        "ncj_step": "Generate Solutions",
        "difficulty": "medium",
        "source_module": "microbiology",
        "clinical_judgment_focus": "Infection prevention bundles are high-yield NCLEX Safety items.",
    },
    {
        "id": "nclex-safe-05",
        "question": "A nurse is preparing to hang IV potassium chloride 10 mEq in 100 mL over 1 hour. Which verification step is essential?",
        "options": [
            "Confirm concentration and maximum infusion rate per policy; use pump",
            "Administer as IV push if client is symptomatic",
            "Dilute in D5W only without checking current fluids",
            "Double the rate if K+ is critically low",
        ],
        "correct_index": 0,
        "rationale": "IV potassium is never given IV push — it causes cardiac arrest. Concentration, dilution, and infusion rate must match policy (typically ≤10 mEq/hr peripheral, higher central with monitoring). Always verify against current fluids and renal status.",
        "category": "Safety & Infection Control",
        "ncj_step": "Take Action",
        "difficulty": "hard",
        "source_module": "dosage",
        "clinical_judgment_focus": "High-alert medication safety — KCl errors are lethal.",
    },
    {
        "id": "nclex-peds-02",
        "question": "A 2-year-old is admitted with suspected ingestion. Which assessment finding is most urgent?",
        "options": [
            "Tearful when parent leaves the room",
            "Drooling and inability to swallow with stridor",
            "Weight at 50th percentile",
            "Last immunizations at 18 months",
        ],
        "correct_index": 1,
        "rationale": "Drooling, inability to swallow, and stridor suggest airway edema or obstruction from caustic or foreign body ingestion — immediate airway assessment and escalation. Separation anxiety is expected; growth and immunization history are not emergent.",
        "category": "Pediatric Nursing",
        "ncj_step": "Prioritize Hypotheses",
        "difficulty": "hard",
        "source_module": "pediatrics",
        "clinical_judgment_focus": "Pediatric airway compromise is always first priority.",
    },
    {
        "id": "nclex-mh-02",
        "question": "A client states, 'I have a plan to overdose tonight with my pills at home.' What is the nurse's priority response?",
        "options": [
            "Stay with client, remove means, initiate suicide precautions per protocol, notify provider",
            "Schedule follow-up outpatient appointment next week",
            "Ask client to sign a no-harm contract and document",
            "Encourage client to think about family impact",
        ],
        "correct_index": 0,
        "rationale": "Active suicidal ideation with plan, means, and timeline is a psychiatric emergency. Constant observation, environmental safety (remove pills/sharps), provider notification, and possible inpatient care take priority. No-harm contracts are not substitutes for safety precautions.",
        "category": "Psychosocial Integrity",
        "ncj_step": "Take Action",
        "difficulty": "hard",
        "source_module": "mental_health",
        "clinical_judgment_focus": "Suicide risk with plan and means requires immediate safety intervention.",
    },
]


def load_json(name: str) -> dict:
    with open(CONTENT / name, encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, data: dict) -> None:
    with open(CONTENT / name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def expand_pediatrics() -> dict:
    mc = load_json("maternal_child.json")
    existing_ids = {p["id"] for p in mc.get("pediatric_essentials", [])}
    added = 0
    for item in PEDS_EXPANSION:
        if item["id"] not in existing_ids:
            mc.setdefault("pediatric_essentials", []).append(item)
            added += 1
    mc["immunization_schedule"] = IMMUNIZATION_SCHEDULE
    fc_ids = {f["id"] for f in mc.get("flashcards", [])}
    fc_added = 0
    for fc in PEDS_FLASHCARDS:
        if fc["id"] not in fc_ids:
            mc.setdefault("flashcards", []).append(fc)
            fc_added += 1
    save_json("maternal_child.json", mc)
    return {"peds_topics_added": added, "flashcards_added": fc_added, "immunization_entries": len(IMMUNIZATION_SCHEDULE)}


def expand_nclex() -> dict:
    nclex = load_json("nclex_prep.json")
    existing = {q["id"] for q in nclex.get("all_questions", [])}
    added = []
    for q in NCLEX_NEW:
        if q["id"] in existing:
            continue
        added.append(q)
        nclex.setdefault("all_questions", []).append(q)
        cat = q["category"]
        nclex.setdefault("questions_by_category", {}).setdefault(cat, []).append(q)
    # Rebuild category counts
    counts: dict[str, int] = {}
    for q in nclex["all_questions"]:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    for cat in nclex.get("categories", []):
        if cat["name"] in counts:
            cat["count"] = counts[cat["name"]]
        elif cat["id"] == "prioritization":
            cat["count"] = counts.get("Prioritization", cat.get("count", 0))
    # Ensure Prioritization category exists
    cat_names = {c["name"] for c in nclex.get("categories", [])}
    if "Prioritization" not in cat_names:
        nclex.setdefault("categories", []).append({"id": "prioritization", "name": "Prioritization", "count": counts.get("Prioritization", 0)})
    if "Safety & Infection Control" not in cat_names:
        nclex.setdefault("categories", []).append({"id": "safety", "name": "Safety & Infection Control", "count": counts.get("Safety & Infection Control", 0)})
    for cat in nclex["categories"]:
        if cat["name"] in counts:
            cat["count"] = counts[cat["name"]]
    nclex["total_questions"] = len(nclex["all_questions"])
    save_json("nclex_prep.json", nclex)
    return {"questions_added": len(added), "total_questions": nclex["total_questions"]}


def main() -> None:
    results = {
        "pediatrics": expand_pediatrics(),
        "nclex": expand_nclex(),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()