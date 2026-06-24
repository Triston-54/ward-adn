"""Build maternal_child.json."""
from __future__ import annotations

from typing import Any

from scripts.restore_content_payload.common import mcq, src


def _topic(tid: str, title: str, category: str, content: str, nursing: list[str]) -> dict:
    return {"id": tid, "title": title, "category": category, "content": content, "nursing_actions": nursing, "source_ref": "maternal_child"}


def build() -> dict[str, Any]:
    s = src("maternal_child")
    pregnancy_stages = [
        _topic("tri1-overview", "First Trimester Overview", "Antepartum", "Weeks 1–12: organogenesis, highest teratogen sensitivity.", ["Folic acid 400–800 mcg", "Assess pregnancy symptoms", "Dating ultrasound"]),
        _topic("tri1-milestones", "First Trimester Milestones", "Antepartum", "Heart begins beating ~6 weeks; limbs form by 8 weeks.", ["Avoid teratogens", "Review medications with provider"]),
        _topic("tri2-overview", "Second Trimester Overview", "Antepartum", "Weeks 13–27: quickening, fetal growth accelerates.", ["Anomaly scan ~20 weeks", "Glucose screening 24–28 weeks"]),
        _topic("tri2-milestones", "Second Trimester Milestones", "Antepartum", "Vernix, lanugo; mother feels fetal movement 18–20 weeks.", ["Fundal height assessment", "Educate on fetal movement counts"]),
        _topic("tri3-overview", "Third Trimester Overview", "Antepartum", "Weeks 28–40: fetal maturation, maternal discomfort increases.", ["Fetal kick counts", "Signs of labor teaching", "Preeclampsia education"]),
        _topic("tri3-milestones", "Third Trimester Milestones", "Antepartum", "Lung surfactant matures; betamethasone 24–34 weeks if preterm risk.", ["Non-stress tests if indicated", "Birth plan discussion"]),
        _topic("edd-naegle", "Estimated Due Date (Naegele)", "Antepartum", "LMP − 3 months + 7 days (280 days).", ["Confirm dating with early ultrasound"]),
        _topic("prenatal-visits", "Prenatal Visit Schedule", "Antepartum", "Monthly until 28 weeks, q2 weeks until 36, weekly until delivery.", ["BP, weight, urine protein, fundal height"]),
        _topic("fetal-wellbeing", "Fetal Well-Being Assessment", "Antepartum", "Kick counts, NST, BPP when indicated for high-risk.", ["Report decreased fetal movement immediately"]),
    ]
    labor_delivery = [
        _topic("stage-1-labor", "Stage 1 Labor", "Intrapartum", "Onset of contractions to full dilation; active labor ≥6 cm; transition ~8–10 cm intense.", ["Monitor FHR and contractions", "Pain management", "Position changes"]),
        _topic("stage-2-labor", "Stage 2 Labor", "Intrapartum", "Full dilation to birth — pushing.", ["Coach pushing", "Prepare for shoulder dystocia response", "Perineal care"]),
        _topic("stage-3-labor", "Stage 3 Labor", "Intrapartum", "Birth to placenta delivery.", ["Watch for hemorrhage", "Oxytocin per order after birth", "Assess placenta integrity"]),
        _topic("stage-4-labor", "Stage 4 Labor", "Intrapartum", "First 1–2 hours postpartum — recovery.", ["Vitals q15min", "Fundal massage", "Breastfeeding support"]),
        _topic("fhr-baseline", "FHR Baseline Assessment", "Intrapartum", "Normal 110–160 bpm; variability moderate; accelerations reassuring.", ["Document baseline, variability, accelerations/decelerations"]),
        _topic("fhr-decelerations", "FHR Decelerations", "Intrapartum", "Early: mirror contractions. Variable: cord compression. Late: gradual nadir after contraction peak — uteroplacental insufficiency.", ["Late decels: stop oxytocin, left lateral, O₂, IV fluids, notify provider"]),
        _topic("leopold-maneuvers", "Leopold Maneuvers", "Intrapartum", "Palpate fetal lie, presentation, and position.", ["Perform before FHR auscultation placement"]),
        _topic("labor-positions", "Labor Positioning", "Intrapartum", "Upright positions aid descent; left lateral improves placental perfusion.", ["Encourage position changes", "Birth ball, squat bar as available"]),
    ]
    postpartum_newborn = [
        _topic("bubble-assessment", "Postpartum Bubble Assessment", "Postpartum", "B — bonding; U — uterus firm/fundal height; B — breasts; B — bowel/bladder; L — lochia; E — episiotomy/edema.", ["Fundal massage if boggy", "Assess lochia amount/color"]),
        _topic("lochia-assessment", "Lochia Assessment", "Postpartum", "Rubra days 1–3; serosa 4–10; alba up to 6 weeks. Foul odor or heavy bleeding abnormal.", ["Pad counts", "Report saturation >1 pad/hr"]),
        _topic("postpartum-maternal-flags", "Postpartum Maternal Warning Signs", "Postpartum", "Fever, foul lochia, incision erythema, chest pain, leg swelling, mood changes with hallucinations.", ["Educate before discharge", "Emergency return precautions"]),
        _topic("apgar-scoring", "APGAR Scoring", "Newborn", "1 and 5 minutes: Appearance, Pulse, Grimace, Activity, Respiration. <7 needs intervention.", ["Resuscitation per NRP", "Document scores"]),
        _topic("immediate-newborn-care", "Immediate Newborn Care", "Newborn", "Dry, warm, stimulate, delay cord clamp per policy, skin-to-skin, vitamin K and eye prophylaxis per order.", ["Assess airway", "Prevent hypothermia"]),
        _topic("newborn-physical-assessment", "Newborn Physical Assessment", "Newborn", "Vitals, reflexes, skin, fontanelles, hips, heart/lung auscultation.", ["Red reflex eye exam", "Weight and measurements"]),
        _topic("bonding-kangaroo", "Bonding & Kangaroo Care", "Newborn", "Skin-to-skin stabilizes temperature and glucose; promotes attachment.", ["Encourage early breastfeeding"]),
        _topic("breastfeeding-basics", "Breastfeeding Basics", "Newborn", "Latch, frequency 8–12 feeds/24 hr, wet diapers day 4+.", ["Assess latch and maternal nipple pain", "IBCLC referral"]),
        _topic("newborn-warning-signs", "Newborn Warning Signs", "Newborn", "Poor feeding, lethargy, respiratory distress, circumoral cyanosis, fever ≥38°C.", ["Report immediately", "Sepsis workup in young infant"]),
    ]
    pediatric_essentials = [
        _topic("growth-percentiles", "Growth Percentiles", "Pediatrics", "Weight, length, head circumference plotted on WHO/CDC charts.", ["Trend over time more important than single point"]),
        _topic("milestone-infant", "Infant Milestones", "Pediatrics", "Social smile ~2 mo, rolls ~4–6 mo, sits ~6 mo, crawls ~9 mo.", ["Refer delays per Early Intervention"]),
        _topic("milestone-toddler", "Toddler Milestones", "Pediatrics", "Walks ~12 mo, 50 words ~18 mo, parallel play.", ["Safety: gates, poison prevention"]),
        _topic("milestone-preschool", "Preschool Milestones", "Pediatrics", "Tricycle, sentences, cooperative play.", ["Vision/hearing screening"]),
        _topic("immunization-basics", "Immunization Schedule", "Pediatrics", "CDC schedule — DTaP, IPV, MMR, varicella, Hep B series.", ["Document lot and site", "VIS sheets"]),
        _topic("pediatric-fever", "Pediatric Fever", "Pediatrics", "Context matters — behavior, hydration, age. Infant ≤28 days with ≥38°C = emergency workup.", ["Antipyretics weight-based", "Never aspirin — Reye syndrome"]),
        _topic("dehydration-peds", "Pediatric Dehydration", "Pediatrics", "Assess fontanel, mucous membranes, urine output, cap refill.", ["Oral rehydration if mild; IV if severe"]),
        _topic("pain-assessment-peds", "Pediatric Pain Assessment", "Pediatrics", "FLACC infant; FACES/Wong-Baker child; self-report when able.", ["Believe child's report"]),
    ]
    safety_red_flags = [
        {"id": "rf-preeclampsia", "finding": "BP ≥140/90 after 20 weeks with proteinuria OR systemic symptoms (headache, RUQ pain, vision changes)", "category": "OB emergency", "action": "Notify provider; assess HELLP; seizure precautions; magnesium per order", "escalation": "Magnesium sulfate for severe features; delivery may be indicated"},
        {"id": "rf-eclampsia", "finding": "Seizure in preeclamptic patient", "category": "OB emergency", "action": "Side-lying, airway, magnesium per protocol, notify provider, prepare for delivery"},
        {"id": "rf-hemorrhage", "finding": "Postpartum hemorrhage — fundus boggy, soaking >1 pad/hr", "category": "Postpartum", "action": "Fundal massage, IV access, oxytocin per order, notify provider, blood products"},
        {"id": "rf-cord-prolapse", "finding": "Umbilical cord prolapse with fetal bradycardia", "category": "Labor emergency", "action": "Knee-chest or exaggerated Sims; elevate presenting part; emergency cesarean"},
        {"id": "rf-shoulder-dystocia", "finding": "Turtle sign — head delivered, shoulders stuck", "category": "Labor emergency", "action": "McRoberts + suprapubic pressure; NO fundal pressure; notify team"},
        {"id": "rf-placental-abruption", "finding": "Painful rigid abdomen, dark bleeding, nonreassuring FHR", "category": "OB emergency", "action": "Left lateral, O₂, IV access, notify provider, prepare for emergency delivery"},
        {"id": "rf-postpartum-psychosis", "finding": "Hallucinations, delusions, bizarre behavior days–4 weeks postpartum", "category": "Psychiatric emergency", "action": "Constant observation; infant safety; psychiatry; do not leave alone with baby"},
        {"id": "rf-neonatal-fever", "finding": "Infant ≤28 days rectal temp ≥38°C (100.4°F)", "category": "Neonatal emergency", "action": "Full sepsis workup per protocol; notify provider; NPO for procedures"},
        {"id": "rf-resp-distress-newborn", "finding": "Nasal flaring, grunting, retractions, circumoral cyanosis", "category": "Neonatal", "action": "Position; O₂; notify provider/NRP team"},
        {"id": "rf-late-decel", "finding": "Repetitive late decelerations with decreased variability", "category": "Fetal distress", "action": "Stop oxytocin, left lateral, O₂, IV fluids, notify provider"},
        {"id": "rf-magnesium-toxicity", "finding": "Absent DTRs, RR <12, urine output <30 mL/hr on magnesium", "category": "Medication", "action": "Stop magnesium; notify provider; calcium gluconate per order"},
        {"id": "rf-pp-endometritis", "finding": "Fever, foul lochia, uterine tenderness postpartum", "category": "Postpartum infection", "action": "Cultures; antibiotics per order; monitor vitals"},
        {"id": "rf-jaundice-newborn", "finding": "Jaundice <24 hr of life or rapidly rising bilirubin", "category": "Neonatal", "action": "Bilirubin level; phototherapy per order; breastfeeding support"},
        {"id": "rf-croup-stridor", "finding": "Barking cough, stridor at rest in toddler", "category": "Pediatric airway", "action": "Comfort; nebulized epinephrine/steroids per order; airway monitoring"},
        {"id": "rf-nonaccidental-trauma", "finding": "Injuries inconsistent with history in child", "category": "Child safety", "action": "Mandatory reporting; separate interviews; document objectively"},
    ]
    complications_drill = []
    drill_specs = [
        ("mc-drill-01", "Sudden heavy lochia with boggy fundus 1 hr postpartum", "Fundal massage and notify provider — PPH", 0),
        ("mc-drill-02", "BP 168/112, RUQ pain, 3+ protein at 34 weeks", "Preeclampsia protocol — notify provider, assess HELLP", 0),
        ("mc-drill-03", "Late decelerations with oxytocin infusion", "Stop oxytocin, intrauterine resuscitation, notify provider", 0),
        ("mc-drill-04", "Prolapsed cord visible with bradycardia", "Knee-chest, elevate presenting part, emergency delivery prep", 0),
        ("mc-drill-05", "Newborn axillary temp 38.5°C at 10 days old", "Sepsis workup per neonatal fever protocol", 0),
        ("mc-drill-06", "Mother reports auditory hallucinations 5 days postpartum", "1:1, infant safety, psychiatry — postpartum psychosis", 0),
        ("mc-drill-07", "Absent DTRs on magnesium sulfate", "Stop magnesium, notify provider, check RR and urine output", 0),
        ("mc-drill-08", "14-day-old fever 38.2°C — lethargic", "Emergency workup — infant ≤28 days standard", 0),
        ("mc-drill-09", "Variable decelerations with cord visible at introitus", "Amnioinfusion per order or position change; prepare for cesarean if nonreassuring", 0),
        ("mc-drill-10", "Toddler not walking at 18 months", "Referral for developmental evaluation — not normal variant", 0),
        ("mc-drill-11", "Shoulder dystocia during delivery", "McRoberts and suprapubic pressure — no fundal pressure", 0),
        ("mc-drill-12", "RUQ pain, platelets 68k, AST elevated postpartum with confusion", "HELLP vs psychosis overlap — labs and psych eval; notify provider", 0),
        ("mc-drill-13", "Late decels at 8 cm dilation", "Intrauterine resuscitation before pushing — fetal status priority", 0),
    ]
    for did, finding, correct_action, correct in drill_specs:
        complications_drill.append({
            "id": did, "finding": finding, "category": "OB/Peds",
            "options": [correct_action, "Continue routine care and document", "Administer PRN acetaminophen only", "Discharge teaching"],
            "correct_index": correct,
            "explanation": f"Priority action: {correct_action}",
            "clinical_why": "Maternal-fetal and neonatal safety prioritization per NCLEX.",
            "source_ref": "maternal_child",
        })
    flashcards = []
    for i, (front, back, cat) in enumerate([
        ("APGAR 1 min", "Assess at 1 and 5 min — <7 needs help", "Newborn"),
        ("Fundal height mid-pregnancy", "~cm equals weeks gestation ±2", "Antepartum"),
        ("Preeclampsia BP", "≥140/90 after 20 wks with proteinuria or systemic symptoms", "OB"),
        ("Magnesium antidote", "Calcium gluconate for toxicity", "OB"),
        ("Late deceleration", "Uteroplacental insufficiency — stop pitocin, O₂, fluids", "FHR"),
        ("Early deceleration", "Head compression — usually benign", "FHR"),
        ("Variable decel", "Cord compression — position change, amnioinfusion", "FHR"),
        ("Preeclampsia/HELLP", "Hemolysis, Elevated Liver enzymes, Low Platelets + RUQ pain", "OB"),
        ("McRoberts", "Hyperflex hips for shoulder dystocia", "Labor"),
        ("No fundal pressure", "Contraindicated in shoulder dystocia", "Labor"),
        ("Kangaroo care", "Skin-to-skin thermoregulation and bonding", "Newborn"),
        ("Physiologic jaundice", "Days 2–3 term infant; pathologic if <24 hr", "Newborn"),
        ("Lochia rubra", "Days 1–3 bright red", "Postpartum"),
        ("PPH boggy fundus", "Massage first-line before medications", "Postpartum"),
        ("Neonatal fever ≤28d", "Full sepsis workup mandatory", "Neonatal"),
        ("Betamethasone window", "24–34 weeks for fetal lung maturity", "Antepartum"),
        ("FHR baseline", "110–160 bpm normal", "FHR"),
        ("Cord prolapse position", "Knee-chest preferred over Trendelenburg in pregnancy", "Emergency"),
        ("Breastfeeding frequency", "8–12 feeds/24 hr newborn", "Newborn"),
        ("Immunization documentation", "Lot number, site, VIS given", "Pediatrics"),
        ("FLACC scale", "Face Legs Activity Cry Consolability — infant pain", "Pediatrics"),
        ("Toddler safety", "Poison control, gates, water safety", "Pediatrics"),
        ("Postpartum psychosis timing", "Days to 4 weeks — psychiatric emergency", "Postpartum"),
        ("HELLP platelets", "Thrombocytopenia <100k component", "OB"),
        ("Variability moderate", "6–25 bpm reassuring", "FHR"),
        ("Supine hypotension", "Left lateral tilt after 20 weeks", "Antepartum"),
        ("Naegele rule", "LMP −3 mo +7 days", "Antepartum"),
        ("Vitamin K newborn", "IM per protocol — prevents hemorrhagic disease", "Newborn"),
        ("Erythromycin eye prophylaxis", "Prevents gonorrheal ophthalmia neonatorum", "Newborn"),
        ("Dehydration infant", "Sunken fontanel, dry mucosa, decreased urine", "Pediatrics"),
        ("Shoulder dystocia sign", "Turtle sign — head retracts against perineum", "Labor"),
        ("Placental abruption", "Painful bleeding, rigid abdomen", "OB"),
    ], 1):
        flashcards.append({"id": f"mc-fc-{i:02d}", "front": front, "back": back, "category": cat})
    practice_questions = [
        mcq("mc-q01", "Late decelerations during labor — first action?", ["Stop oxytocin and intrauterine resuscitation", "Increase oxytocin", "Prepare for immediate discharge", "Turn off monitor"], 0, "Late decels = uteroplacental insufficiency.", source_key="maternal_child"),
        mcq("mc-q02", "Postpartum fundus boggy — intervene with:", ["Fundal massage", "Ice pack only", "Encourage bed rest 24 hr", "Discharge"], 0, "First-line for atonic uterus.", source_key="maternal_child"),
        mcq("mc-q03", "Preeclampsia severe feature includes:", ["RUQ epigastric pain", "Mild ankle edema only", "Braxton Hicks", "Fetal hiccups"], 0, "RUQ pain suggests liver capsule distension/HELLP.", source_key="maternal_child"),
        mcq("mc-q04", "Shoulder dystocia maneuver:", ["McRoberts + suprapubic pressure", "Fundal pressure", "Trendelenburg", "Forceps from abdomen"], 0, "AWHONN/NRP standard — no fundal pressure.", source_key="maternal_child"),
        mcq("mc-q05", "Newborn APGAR 4 at 1 minute — nurse:", ["Continue resuscitation per NRP and reassess at 5 min", "Stop all intervention", "Discharge to mother only", "Document only"], 0, "Low score requires intervention.", source_key="maternal_child"),
        mcq("mc-q06", "Magnesium toxicity sign:", ["Absent deep tendon reflexes", "Increased reflexes", "Hypertension", "Tachycardia only"], 0, "Also RR depression and decreased urine output.", source_key="maternal_child"),
        mcq("mc-q07", "14-day-old with 38.3°C fever — priority:", ["Full sepsis evaluation per neonatal protocol", "Acetaminophen and home", "Wait 24 hours", "Cool bath only"], 0, "Young infant fever is emergency.", source_key="maternal_child"),
        mcq("mc-q08", "Cord prolapse nursing action:", ["Knee-chest, elevate presenting part, notify for emergency delivery", "Push cord back into vagina repeatedly", "Place patient supine flat only", "Stop monitoring FHR"], 0, "Relieve cord compression.", source_key="maternal_child"),
        mcq("mc-q09", "Physiologic jaundice typically appears:", ["Day 2–3 in term newborn", "First hour of life", "Never in breastfed infants", "Only in preterm"], 0, "Pathologic if <24 hr.", source_key="maternal_child"),
        mcq("mc-q10", "Postpartum psychosis requires:", ["Immediate psychiatric care and infant safety measures", "Routine outpatient follow-up only", "Ignore unless violent", "Sedation at home without supervision"], 0, "Psychiatric emergency days–4 weeks postpartum.", source_key="maternal_child"),
    ]
    for i in range(11, 22):
        practice_questions.append(mcq(
            f"mc-q{i:02d}",
            f"Maternal-child NCLEX item {i}: Which finding requires immediate provider notification?",
            ["Nonreassuring FHR with late decelerations", "Mild hunger in laboring patient", "Normal fetal hiccups", "Requested ice chips"],
            0,
            "Fetal and maternal emergencies take priority over comfort measures.",
            source_key="maternal_child",
        ))
    return {
        "module_id": "maternal_child",
        "title": "Maternal-Newborn & Pediatric Nursing",
        "pregnancy_stages": pregnancy_stages,
        "labor_delivery": labor_delivery,
        "postpartum_newborn": postpartum_newborn,
        "pediatric_essentials": pediatric_essentials,
        "safety_red_flags": safety_red_flags,
        "complications_drill": complications_drill,
        "flashcards": flashcards,
        "practice_questions": practice_questions,
        "source": s,
    }