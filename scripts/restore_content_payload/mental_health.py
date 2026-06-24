"""Build mental_health.json."""
from __future__ import annotations

from typing import Any

from scripts.restore_content_payload.common import mcq, src


def build() -> dict[str, Any]:
    s = src("mental_health")
    therapeutic_communication = [
        {"id": "active-listening", "technique": "Active Listening", "description": "Attend fully; use open posture and verbal acknowledgments.", "example": "I hear that you're feeling overwhelmed.", "when_to_use": "All therapeutic interactions", "avoid": ["Interrupting", "Planning response while patient speaks"], "source": s},
        {"id": "open-ended", "technique": "Open-Ended Questions", "description": "Invite narrative without yes/no limits.", "example": "Tell me more about what happened before you felt anxious.", "when_to_use": "Assessment and rapport building", "avoid": ["Leading questions"], "source": s},
        {"id": "reflection", "technique": "Reflection", "description": "Mirror feelings or content to validate.", "example": "You sound frustrated about the wait.", "when_to_use": "Emotional distress", "avoid": ["Minimizing ('You'll be fine')"], "source": s},
        {"id": "clarification", "technique": "Clarification", "description": "Seek specific meaning when vague.", "example": "When you say 'voices,' what are they saying?", "when_to_use": "Psychotic symptoms or ambiguous statements", "avoid": ["Assuming meaning"], "source": s},
        {"id": "silence", "technique": "Therapeutic Silence", "description": "Allow pause for patient processing.", "example": "Nurse remains present without filling pause after loss disclosure.", "when_to_use": "Grief, trauma disclosure", "avoid": ["Changing subject immediately"], "source": s},
        {"id": "summarization", "technique": "Summarization", "description": "Review key points to confirm understanding.", "example": "So tonight you felt hopeless after argument, no plan to act.", "when_to_use": "End of interview; safety assessment", "avoid": ["Omitting suicide plan details"], "source": s},
        {"id": "broadening", "technique": "Broadening the Topic", "description": "Expand from narrow complaint to context.", "example": "Besides sleep, how has mood been this week?", "when_to_use": "Depression screening", "avoid": ["Yes/no chains only"], "source": s},
        {"id": "offering-self", "technique": "Offering Self", "description": "Communicate availability and presence.", "example": "I'll be here with you during the procedure.", "when_to_use": "Anxiety, loneliness", "avoid": ["False promises of outcomes"], "source": s},
    ]
    communication_barriers = [
        {"id": "barrier-advice", "barrier": "Giving Unsolicited Advice", "description": "Telling patient what to do instead of exploring.", "example": "You should just leave that relationship.", "therapeutic_alternative": "What options have you considered?", "source": s},
        {"id": "barrier-belittling", "barrier": "Belittling Feelings", "description": "Minimizing emotions ('Don't worry').", "example": "Others have it worse.", "therapeutic_alternative": "This sounds really painful for you.", "source": s},
        {"id": "barrier-false-reassurance", "barrier": "False Reassurance", "description": "Promising outcomes without evidence.", "example": "Everything will be fine.", "therapeutic_alternative": "We'll work through this together step by step.", "source": s},
        {"id": "barrier-changing-subject", "barrier": "Changing Subject", "description": "Avoiding uncomfortable topics.", "example": "Patient mentions SI — nurse asks about lunch.", "therapeutic_alternative": "Direct suicide assessment with caring tone.", "source": s},
    ]
    safety_risk_flags = [
        {"id": "rf-si-plan", "finding": "Active suicidal ideation with plan and access to means", "category": "Suicide", "priority": "immediate", "action": "1:1 observation; remove means; notify provider; document direct quotes", "source": s},
        {"id": "rf-homicidal", "finding": "Homicidal ideation with identified victim and plan", "category": "Violence", "priority": "immediate", "action": "Notify provider and security; 1:1; duty to warn per state law", "source": s},
        {"id": "rf-elopement", "finding": "Voluntary hold patient attempting to leave unit", "category": "Safety", "priority": "immediate", "action": "Follow elopement protocol; notify charge nurse; do not physically restrain without training/order", "source": s},
        {"id": "rf-seclusion", "finding": "Escalating aggression with weapons or thrown objects", "category": "Violence", "priority": "immediate", "action": "Call team; clear area; de-escalation; seclusion/restraint only as last resort per policy", "source": s},
        {"id": "rf-withdrawal", "finding": "CIWA-Ar score ≥20 or autonomic hyperactivity with delirium", "category": "Substance", "priority": "immediate", "action": "Notify provider; benzodiazepine protocol; continuous monitoring", "source": s},
        {"id": "rf-serotonin", "finding": "Agitation, hyperreflexia, clonus, fever after serotonergic drugs", "category": "Medication", "priority": "immediate", "action": "Stop serotonergic agents; notify provider; monitor vitals — serotonin syndrome", "source": s},
        {"id": "rf-nyms", "finding": "Neuroleptic malignant syndrome: rigidity, fever, altered mental status on antipsychotic", "category": "Medication", "priority": "immediate", "action": "Stop antipsychotic; notify provider; ICU-level care", "source": s},
        {"id": "rf-self-harm", "finding": "Fresh cutting or ligature marks with intent to die", "category": "Self-harm", "priority": "immediate", "action": "Safety search; 1:1; wound care; psychiatric evaluation", "source": s},
    ]
    screening_tools = [
        {"id": "tool-phq9", "name": "PHQ-9", "purpose": "Depression severity screening", "scoring": "0–27; ≥10 suggests moderate depression; item 9 screens suicide", "nursing_action": "Escalate positive item 9 immediately; notify provider for high scores", "source": s},
        {"id": "tool-gad7", "name": "GAD-7", "purpose": "Generalized anxiety disorder screening", "scoring": "0–21; ≥10 moderate anxiety", "nursing_action": "Support coping strategies; notify provider for severe scores", "source": s},
        {"id": "tool-ciwa", "name": "CIWA-Ar", "purpose": "Alcohol withdrawal assessment", "scoring": "<10 mild; 10–18 moderate; ≥20 severe", "nursing_action": "Benzodiazepine per protocol for elevated scores; q1-2h monitoring if severe", "source": s},
        {"id": "tool-cows", "name": "COWS", "purpose": "Opioid withdrawal assessment", "scoring": "Aggregated signs — higher = more severe withdrawal", "nursing_action": "Medication-assisted treatment per provider; comfort measures", "source": s},
    ]
    communication_scenarios = [
        {"id": "cs-01", "title": "Patient states 'Nobody cares if I live or die'", "patient_statement": "Nobody cares if I live or die.", "category": "Suicide risk", "options": ["Don't talk like that — you'll be fine", "It sounds like you're feeling hopeless. Are you thinking of harming yourself?", "Let's change the subject", "I'll come back when you're calmer"], "correct_index": 1, "explanation": "Direct, caring suicide inquiry is therapeutic and required.", "clinical_why": "Asking about suicide does not increase risk.", "source": s},
        {"id": "cs-02", "title": "Angry about wait time", "patient_statement": "This place is a joke! I've been waiting hours!", "category": "De-escalation", "options": ["Yelling won't help", "I can see you're frustrated. I'm here to help — tell me what's most urgent right now.", "Leave if you don't like it", "Ignore until calm"], "correct_index": 1, "explanation": "Acknowledge emotion and redirect to problem-solving.", "clinical_why": "Validation reduces escalation.", "source": s},
        {"id": "cs-03", "title": "Command hallucinations", "patient_statement": "The voices tell me to hurt the nurse.", "category": "Psychosis", "options": ["Those voices aren't real — ignore them", "You're safe here. Do you feel able to resist those commands right now?", "Share this only if asked later", "Laugh it off"], "correct_index": 1, "explanation": "Assess command hallucinations and safety; notify provider.", "clinical_why": "Command hallucinations increase violence risk.", "source": s},
        {"id": "cs-04", "title": "Grief disclosure", "patient_statement": "I can't stop crying since my wife died.", "category": "Grief", "options": ["Therapeutic silence and presence, then reflect feelings", "You need to move on", "Here's a pamphlet — read later", "Medication will fix this immediately"], "correct_index": 0, "explanation": "Presence and reflection support grieving process.", "clinical_why": "Non-judgmental support builds trust.", "source": s},
        {"id": "cs-05", "title": "Refusing medication", "patient_statement": "I'm not taking those pills — they're poison.", "category": "Medication refusal", "options": ["Force medication", "Help me understand your concerns about the medication.", "Walk away", "Lie and say they're vitamins"], "correct_index": 1, "explanation": "Explore beliefs and collaborate — may need capacity evaluation.", "clinical_why": "Rights and safety balance requires assessment.", "source": s},
    ]
    disorders = [
        {"id": "mdd", "name": "Major Depressive Disorder", "category": "Mood", "summary": "Persistent depressed mood or anhedonia ≥2 weeks with functional impairment", "pathophysiology": "Monoamine dysregulation; HPA axis changes; neuroplasticity reduction.", "nursing_care": ["Suicide screening each shift", "Encourage ADLs", "Medication adherence", "SAD PERSONS risk factors"], "medications": ["SSRIs", "SNRIs"], "source": s},
        {"id": "bipolar", "name": "Bipolar Disorder", "category": "Mood", "summary": "Episodes of mania/hypomania alternating with depression", "pathophysiology": "Dysregulated mood circuits; strong genetic component.", "nursing_care": ["Sleep protection", "Limit stimulation in mania", "Lithium levels", "Suicide risk in depression phase"], "medications": ["Lithium", "Valproate", "Atypical antipsychotics"], "source": s},
        {"id": "schizophrenia", "name": "Schizophrenia", "category": "Psychotic", "summary": "Positive symptoms (hallucinations, delusions) and negative symptoms (flat affect, avolition)", "pathophysiology": "Dopamine hypothesis; structural brain changes.", "nursing_care": ["Therapeutic communication", "Medication adherence", "Metabolic monitoring with atypicals", "Safety with command hallucinations"], "medications": ["Antipsychotics"], "source": s},
        {"id": "anxiety-gad", "name": "Generalized Anxiety Disorder", "category": "Anxiety", "summary": "Excessive worry ≥6 months with physical symptoms", "pathophysiology": "Hyperactive amygdala; GABA imbalance.", "nursing_care": ["Relaxation techniques", "SSRIs/SNRIs", "Avoid caffeine", "CBT referral"], "medications": ["SSRIs", "Buspirone"], "source": s},
        {"id": "ptsd", "name": "PTSD", "category": "Trauma", "summary": "Trauma exposure with intrusion, avoidance, hyperarousal, negative cognition", "pathophysiology": "Hyperactive fear response; altered memory consolidation.", "nursing_care": ["Trauma-informed care", "Predictable environment", "Grounding techniques", "Avoid retraumatization"], "medications": ["SSRIs", "Prazosin for nightmares"], "source": s},
        {"id": "substance-use", "name": "Substance Use Disorder", "category": "Substance", "summary": "Maladaptive use with impairment and craving", "pathophysiology": "Reward pathway hijacking; tolerance and withdrawal.", "nursing_care": ["Withdrawal protocols", "Motivational interviewing", "Harm reduction", "CIWA/COWS monitoring"], "medications": ["Buprenorphine", "Naltrexone", "Benzodiazepines for alcohol withdrawal"], "source": s},
    ]
    de_escalation = [
        {"id": "de-technique-01", "type": "technique", "title": "Calm Voice and Open Posture", "description": "Lower voice volume; hands visible; maintain safe distance.", "category": "Verbal", "source": s},
        {"id": "de-technique-02", "type": "technique", "title": "Set Clear Limits", "description": "State expectations calmly: 'I need you to step back so we can talk safely.'", "category": "Verbal", "source": s},
        {"id": "de-technique-03", "type": "technique", "title": "Offer Choices", "description": "Two acceptable options to restore sense of control.", "category": "Verbal", "source": s},
        {"id": "de-scenario-01", "type": "scenario", "title": "Pacing and shouting in hallway", "category": "Agitation", "options": ["Restrain immediately", "Approach with team, offer quiet space and PRN per order", "Yell back", "Ignore"], "correct_index": 1, "explanation": "Least restrictive intervention first with team support.", "clinical_why": "De-escalation reduces restraint trauma.", "source": s},
    ]
    safety_drill = [
        {"id": "drill-01", "finding": "Patient handed nurse a suicide note and pills", "category": "Suicide", "options": ["1:1 observation and notify provider immediately", "Place note in chart and continue rounds", "Return pills to bedside table", "Wait for family to arrive"], "correct_index": 0, "explanation": "Imminent risk — continuous observation and means removal.", "clinical_why": "Written plan with means is highest acute risk.", "source": s},
        {"id": "drill-02", "finding": "Patient with history of violence picks up chair", "category": "Violence", "options": ["Clear others, call team, verbal de-escalation", "Grab chair from patient alone", "Turn back to document", "Close door and leave patient"], "correct_index": 0, "explanation": "Team response and safety of others priority.", "clinical_why": "Never intervene alone without training.", "source": s},
        {"id": "drill-03", "finding": "Alcohol withdrawal tremors, HR 118, CIWA 22", "category": "Withdrawal", "options": ["Notify provider and initiate benzodiazepine protocol", "Offer coffee only", "Discharge home", "Reassess next week"], "correct_index": 0, "explanation": "Severe withdrawal — medical emergency.", "clinical_why": "Delirium tremens can be fatal.", "source": s},
        {"id": "drill-04", "finding": "Patient reports command to stab roommate", "category": "Psychosis", "options": ["Assess intent/capacity to resist; 1:1; notify provider; separate roommate", "Ignore unless attempt made", "Tell roommate to defend self", "Unlock all doors"], "correct_index": 0, "explanation": "Command hallucinations with identified target = immediate safety.", "clinical_why": "Duty to protect patient and others.", "source": s},
        {"id": "drill-05", "finding": "Lithium level 2.2 mEq/L with coarse tremor and confusion", "category": "Medication toxicity", "options": ["Hold lithium and notify provider immediately", "Give extra lithium", "Encourage fluids only without notifying", "Discharge"], "correct_index": 0, "explanation": "Lithium toxicity — narrow therapeutic index.", "clinical_why": "Levels >1.5 often toxic — seizure risk.", "source": s},
    ]
    practice_questions = [
        mcq("mh-q01", "Therapeutic response to 'I want to die':", ["You'll feel better tomorrow", "Are you having thoughts of killing yourself right now?", "Don't say that", "I'll get back to you"], 1, "Direct suicide assessment is standard of care.", nclex_category="Psychosocial Integrity", source_key="mental_health"),
        mcq("mh-q02", "Non-therapeutic communication is:", ["Reflection", "Giving false reassurance", "Open-ended questions", "Offering self"], 1, "False reassurance dismisses feelings.", source_key="mental_health"),
        mcq("mh-q03", "CIWA-Ar score 22 indicates:", ["Mild withdrawal", "Moderate withdrawal", "Severe withdrawal requiring urgent treatment", "No withdrawal"], 2, "≥20 severe — benzodiazepine protocol.", source_key="mental_health"),
        mcq("mh-q04", "Priority for command hallucinations to harm others:", ["Safety assessment and 1:1", "Ignore until acted on", "Argue voices are unreal", "Discharge"], 0, "Assess ability to resist commands.", source_key="mental_health"),
        mcq("mh-q05", "PHQ-9 item 9 positive requires:", ["Routine follow-up in month", "Immediate suicide risk assessment", "Ignore if mood improved", "Discharge"], 1, "Item 9 screens active suicidal ideation.", source_key="mental_health"),
        mcq("mh-q06", "Serotonin syndrome includes:", ["Hyperreflexia, clonus, agitation", "Bradycardia only", "Hypothermia only", "No autonomic changes"], 0, "Serotonergic excess — medical emergency.", source_key="mental_health"),
        mcq("mh-q07", "Least restrictive intervention means:", ["Restraint first", "Start with verbal de-escalation and milieu management", "Seclusion for all agitation", "Chemical restraint without assessment"], 1, "CMS and nursing ethics prioritize least restriction.", source_key="mental_health"),
        mcq("mh-q08", "Lithium teaching includes:", ["Maintain consistent sodium and fluid intake", "Skip doses when thirsty", "Double dose if missed", "No level monitoring needed"], 0, "Dehydration and Na loss increase toxicity.", source_key="mental_health"),
        mcq("mh-q09", "Trauma-informed care emphasizes:", ["Safety, trust, choice, collaboration", "Confrontation of trauma details immediately", "Punishment for behaviors", "Isolation"], 0, "Avoid retraumatization.", source_key="mental_health"),
        mcq("mh-q10", "Antipsychotic monitoring includes:", ["Weight, glucose, lipids for metabolic syndrome", "Only BP", "No monitoring", "TSH only"], 0, "Atypicals cause metabolic adverse effects.", source_key="mental_health"),
        mcq("mh-q11", "Restraint/seclusion requires:", ["Provider order, least restrictive alternatives attempted, continuous monitoring", "Nurse discretion alone indefinitely", "No documentation", "PRN without face-to-face eval"], 0, "Regulatory requirements for behavioral health.", source_key="mental_health"),
    ]
    return {
        "module_id": "mental_health",
        "title": "NURS 147 — Mental Health Nursing",
        "therapeutic_communication": therapeutic_communication,
        "communication_barriers": communication_barriers,
        "communication_scenarios": communication_scenarios,
        "safety_risk_flags": safety_risk_flags,
        "screening_tools": screening_tools,
        "disorders": disorders,
        "de_escalation": de_escalation,
        "safety_drill": safety_drill,
        "practice_questions": practice_questions,
        "source": s,
    }