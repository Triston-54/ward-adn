"""Build microbiology.json."""
from __future__ import annotations

from typing import Any

from scripts.restore_content_payload.common import mcq, src


def _chain_interventions() -> dict[str, list[dict]]:
    return {
        "agent": [
            {"id": "sterilize", "label": "Sterilization/disinfection of equipment", "correct": True, "explanation": "Reduces viable pathogens on fomites and instruments.", "clinical_why": "Targets the infectious agent directly on surfaces and devices."},
            {"id": "antimicrobial", "label": "Appropriate antimicrobial therapy per culture", "correct": True, "explanation": "Treats active infection caused by the pathogen.", "clinical_why": "Stewardship: culture first when possible, shortest effective course."},
            {"id": "vaccine_host", "label": "Vaccination of exposed staff", "correct": False, "explanation": "Vaccination builds host immunity — it does not eliminate the agent link.", "clinical_why": "Host susceptibility intervention, not agent destruction."},
        ],
        "reservoir": [
            {"id": "clean_env", "label": "Environmental cleaning (EPA-registered disinfectant)", "correct": True, "explanation": "Removes pathogens from surfaces where they survive.", "clinical_why": "C. diff requires bleach; C. auris needs EPA claim against organism."},
            {"id": "food_safety", "label": "Food safety and water treatment", "correct": True, "explanation": "Prevents reservoir in food/water sources.", "clinical_why": "Norovirus and Salmonella often foodborne."},
            {"id": "isolation_only", "label": "Patient isolation alone", "correct": False, "explanation": "Isolation primarily breaks transmission, not the reservoir itself.", "clinical_why": "Pair isolation with cleaning and source control."},
        ],
        "portal_exit": [
            {"id": "respiratory_hygiene", "label": "Respiratory hygiene/cough etiquette", "correct": True, "explanation": "Contains pathogens leaving via respiratory tract.", "clinical_why": "Cover coughs; mask patient with respiratory infection."},
            {"id": "wound_dressing", "label": "Contained wound drainage and dressing changes", "correct": True, "explanation": "Prevents spread from portal of exit.", "clinical_why": "Standard precautions for all body fluids."},
            {"id": "no_hand_hygiene", "label": "Skip hand hygiene after patient contact", "correct": False, "explanation": "Hand hygiene is essential after touching portals of exit.", "clinical_why": "WHO 5 Moments framework."},
        ],
        "transmission": [
            {"id": "hand_hygiene_tx", "label": "Hand hygiene before/after patient contact", "correct": True, "explanation": "Primary break for contact transmission.", "clinical_why": "Soap-and-water for C. diff spores."},
            {"id": "ppe", "label": "Appropriate PPE per transmission-based precautions", "correct": True, "explanation": "Blocks droplet, contact, airborne spread.", "clinical_why": "N95 + contact for varicella until lesions crusted."},
            {"id": "shared_equipment", "label": "Reuse non-cleaned equipment room-to-room", "correct": False, "explanation": "Fomites carry pathogens between patients.", "clinical_why": "Dedicated equipment or disinfection between uses."},
        ],
        "portal_entry": [
            {"id": "skin_prep", "label": "Skin antisepsis before invasive procedures", "correct": True, "explanation": "Reduces portal-of-entry contamination.", "clinical_why": "Chlorhexidine prep reduces CLABSI/SSI."},
            {"id": "sterile_technique", "label": "Sterile technique for invasive devices", "correct": True, "explanation": "Protects mucous membranes and sterile sites.", "clinical_why": "Central line bundles prevent bloodstream infection."},
            {"id": "reuse_needles", "label": "Reuse needles between patients", "correct": False, "explanation": "Never reuse sharps — bloodborne pathogen risk.", "clinical_why": "Single-use sharps disposal in puncture-resistant container."},
        ],
        "host": [
            {"id": "vaccination", "label": "Vaccination per schedule", "correct": True, "explanation": "Builds adaptive immunity in susceptible host.", "clinical_why": "Healthcare worker immunizations protect workforce."},
            {"id": "nutrition_rest", "label": "Nutrition, rest, and chronic disease management", "correct": True, "explanation": "Supports immune competence.", "clinical_why": "Malnutrition and stress increase infection risk."},
            {"id": "prophylactic_abx_all", "label": "Routine prophylactic antibiotics for all patients", "correct": False, "explanation": "Contributes to resistance and CDI — only specific indications.", "clinical_why": "Surgical prophylaxis is time-limited per protocol."},
        ],
    }


def build() -> dict[str, Any]:
    s = src("microbiology")
    infection_chain = [
        {"id": "agent", "name": "Infectious Agent", "description": "Pathogen capable of causing disease — bacteria, virus, fungus, parasite, prion.", "intervention": "Antimicrobial therapy when indicated; sterilization/disinfection; proper specimen handling", "nursing_priority": "Identify organism and susceptibility; apply standard precautions for all patients.", "source": s},
        {"id": "reservoir", "name": "Reservoir", "description": "Environment where pathogen lives and multiplies — humans, animals, soil, water, fomites.", "intervention": "Environmental cleaning; food/water safety; source control of colonized patients", "nursing_priority": "Terminal cleaning of rooms; dedicated equipment for MDRO when policy requires.", "source": s},
        {"id": "portal_exit", "name": "Portal of Exit", "description": "Route pathogen leaves reservoir — respiratory secretions, blood, GI tract, skin lesions.", "intervention": "Respiratory hygiene; contained wound care; safe handling of body fluids", "nursing_priority": "Gloves/gown when contact with fluids expected; leak-proof waste disposal.", "source": s},
        {"id": "transmission", "name": "Mode of Transmission", "description": "Contact, droplet, airborne, vector, or vehicle spread from source to host.", "intervention": "Hand hygiene; transmission-based precautions; safe injection practices", "nursing_priority": "Match precautions to pathogen — contact for C. diff; airborne for TB.", "source": s},
        {"id": "portal_entry", "name": "Portal of Entry", "description": "Mucous membranes, respiratory tract, GI tract, broken skin, genitourinary tract.", "intervention": "Skin antisepsis; sterile technique; device bundles (CLABSI, CAUTI prevention)", "nursing_priority": "Minimize invasive devices; maintain closed drainage systems.", "source": s},
        {"id": "host", "name": "Susceptible Host", "description": "Person lacking immunity or with compromised defenses — age, illness, immunosuppression.", "intervention": "Vaccination; nutrition/rest; protective and neutropenic precautions when indicated", "nursing_priority": "Assess immune status; reverse isolation for neutropenia per protocol.", "source": s},
    ]
    concepts = [
        {"id": "standard-precautions", "title": "Standard Precautions", "summary": "Treat all blood/body fluids as potentially infectious", "content": "Hand hygiene, PPE when exposure anticipated, safe sharps handling, respiratory hygiene. Foundation for all patient care regardless of diagnosis.", "clinical_relevance": "Applied to every patient encounter — NCLEX infection control baseline.", "nursing_implications": ["Perform hand hygiene before and after patient contact", "Use gloves for potential fluid contact", "Face protection if splash risk"], "source": s},
        {"id": "transmission-based-precautions", "title": "Transmission-Based Precautions", "summary": "Contact, droplet, and airborne additions to standard precautions", "content": "Contact: MDRO, C. diff, norovirus. Droplet: influenza, pertussis (~3–6 ft). Airborne: TB, measles, varicella (requires airborne + contact until crusted).", "clinical_relevance": "Varicella needs N95/AIIR AND contact precautions.", "nursing_implications": ["Signage on door", "PPE donning/doffing sequence", "Patient transport minimized"], "source": s},
        {"id": "antimicrobial-stewardship", "title": "Antimicrobial Stewardship", "summary": "Optimize antibiotic use to reduce resistance and CDI", "content": "Obtain cultures before antibiotics when possible. Use narrowest effective spectrum for shortest effective duration per guideline. Educate patients not to share or save antibiotics.", "clinical_relevance": "Overuse drives C. diff and MDRO emergence.", "nursing_implications": ["Verify indication and duration", "Monitor for CDI with new diarrhea on antibiotics", "Hold and notify if rash/anaphylaxis"], "source": s},
        {"id": "hai-prevention", "title": "Healthcare-Associated Infections (HAI)", "summary": "CLABSI, CAUTI, VAP, SSI, CDI prevention bundles", "content": "Central line bundle, urinary catheter stewardship, ventilator bundle, surgical antisepsis, and contact precautions for C. diff with soap-and-water hand hygiene.", "clinical_relevance": "Preventable harm — nursing bundles are first-line defense.", "nursing_implications": ["Daily line necessity review", "Remove urinary catheter ASAP", "HOB 30–45° for ventilated patients"], "source": s},
        {"id": "asepsis-levels", "title": "Medical vs Surgical Asepsis", "summary": "Clean technique vs sterile technique", "content": "Medical asepsis reduces microorganisms (hand hygiene, clean gloves). Surgical asepsis eliminates organisms in sterile field (OR, central line insertion).", "clinical_relevance": "Match technique to procedure invasiveness.", "nursing_implications": ["Never break sterile field 1-inch border", "Clean vs sterile wound care per order"], "source": s},
        {"id": "immunization-principles", "title": "Immunization Principles", "summary": "Active and passive immunity in infection prevention", "content": "Vaccines stimulate antibody production (active). Immunoglobulins provide temporary passive immunity. Herd immunity protects vulnerable hosts.", "clinical_relevance": "Healthcare workers need hepatitis B, influenza, MMR, varicella per facility policy.", "nursing_implications": ["Document lot number and site", "Observe for 15 min post-vaccine if policy requires", "Screen contraindications"], "source": s},
        {"id": "mdro-awareness", "title": "Multidrug-Resistant Organisms (MDRO)", "summary": "MRSA, VRE, ESBL, CRE, C. diff, C. auris", "content": "Contact precautions, dedicated equipment, hand hygiene, and environmental cleaning. Antibiotic stewardship limits emergence.", "clinical_relevance": "MDRO spread is preventable with contact precautions and cleaning.", "nursing_implications": ["Gown/gloves on room entry", "Notify infection prevention", "Cohort when necessary"], "source": s},
        {"id": "specimen-collection", "title": "Specimen Collection & Chain of Custody", "summary": "Accurate culture before antibiotics", "content": "Collect specimens aseptically before starting empiric antibiotics when delay is safe. Label at bedside, transport per policy.", "clinical_relevance": "Contaminated specimens lead to inappropriate therapy.", "nursing_implications": ["Verify order and site", "Use sterile technique for sterile sites", "Document collection time"], "source": s},
    ]
    pathogens = [
        {"name": "MRSA", "full_name": "Methicillin-resistant Staphylococcus aureus", "type": "Gram-positive bacteria (MDRO)", "precautions": "Contact precautions; gown and gloves", "nursing_action": "Dedicated equipment; nasal decolonization per protocol; wound care with contact precautions", "clinical_why": "Colonization vs infection — contact precautions prevent spread in facilities.", "source": s},
        {"name": "C. diff", "full_name": "Clostridioides difficile", "type": "Gram-positive spore-forming anaerobe", "precautions": "Contact precautions; soap-and-water hand hygiene (alcohol gel ineffective on spores)", "nursing_action": "Bleach environmental cleaning; discontinue inciting antibiotics per order; contact precautions", "clinical_why": "Antibiotic-associated diarrhea — toxin causes pseudomembranous colitis.", "source": s},
        {"name": "Influenza", "full_name": "Influenza virus", "type": "RNA virus", "precautions": "Droplet precautions; mask within 3–6 ft", "nursing_action": "Antivirals per order within 48 hr when indicated; droplet PPE; encourage vaccination", "clinical_why": "High mortality in elderly and immunocompromised.", "source": s},
        {"name": "TB", "full_name": "Mycobacterium tuberculosis", "type": "Acid-fast bacillus", "precautions": "Airborne precautions; N95 respirator; negative-pressure AIIR", "nursing_action": "Place in AIIR; wear fit-tested N95; initiate airborne precautions until ruled out or noninfectious", "clinical_why": "Airborne spread via droplet nuclei — occupational health priority.", "source": s},
        {"name": "Norovirus", "full_name": "Norovirus", "type": "RNA virus", "precautions": "Contact precautions; soap-and-water hand hygiene", "nursing_action": "Contact precautions; environmental cleaning; restrict ill staff from work", "clinical_why": "Highly contagious gastroenteritis — outbreaks in facilities.", "source": s},
        {"name": "Pseudomonas", "full_name": "Pseudomonas aeruginosa", "type": "Gram-negative bacillus", "precautions": "Standard precautions; contact if MDR/colonization per policy", "nursing_action": "VAP bundle: HOB 30–45°, oral care, closed suction; avoid moist reservoirs", "clinical_why": "Opportunist in moist environments and ventilated patients.", "source": s},
        {"name": "Candida auris", "full_name": "Candida auris", "type": "Fungus (MDRO)", "precautions": "Contact precautions; notify infection control immediately", "nursing_action": "EPA-registered disinfectant with C. auris claim; cohorting/screening per protocol", "clinical_why": "Environmental persistence — many routine disinfectants ineffective.", "source": s},
        {"name": "Hepatitis B", "full_name": "Hepatitis B virus", "type": "DNA virus (bloodborne)", "precautions": "Standard precautions; sharps safety", "nursing_action": "Never recap needles; hepatitis B vaccination for healthcare workers", "clinical_why": "Percutaneous exposure risk with sharps injuries.", "source": s},
    ]
    practice_questions = [
        mcq("micro-q01", "A patient with C. difficile diarrhea requires which hand hygiene method?", ["Alcohol-based hand rub only", "Soap and water", "No hand hygiene if gloves worn", "Bleach on hands directly"], 1, "Spores are not killed by alcohol gel — soap and water with friction removes spores.", clinical_why="Contact precautions plus soap-and-water is mandatory for C. diff.", nclex_category="Safety and Infection Control", source_key="microbiology"),
        mcq("micro-q02", "Which precaution type is required for pulmonary tuberculosis?", ["Contact", "Droplet", "Airborne", "Protective environment"], 2, "TB spreads via droplet nuclei — N95 and AIIR required.", source_key="microbiology"),
        mcq("micro-q03", "The nurse breaks which chain link by performing hand hygiene before patient care?", ["Infectious agent", "Mode of transmission", "Portal of entry", "Reservoir"], 1, "Hand hygiene interrupts contact transmission of pathogens.", source_key="microbiology"),
        mcq("micro-q04", "Varicella (chickenpox) requires:", ["Airborne precautions only", "Contact precautions only", "Both airborne and contact precautions until lesions crusted", "Droplet precautions only"], 2, "CDC: airborne isolation plus contact until all lesions crusted.", source_key="microbiology"),
        mcq("micro-q05", "Vaccination primarily targets which chain link?", ["Agent", "Reservoir", "Transmission", "Susceptible host"], 3, "Vaccines reduce host susceptibility by building immunity.", source_key="microbiology"),
        mcq("micro-q06", "First action when entering room of patient on contact precautions?", ["Don mask", "Perform hand hygiene and don gown/gloves", "Don N95", "Remove all equipment from room"], 1, "Don PPE on entry; doff inside room avoiding contamination.", source_key="microbiology"),
        mcq("micro-q07", "CLABSI prevention includes:", ["Daily chlorhexidine baths only", "Central line bundle: hand hygiene, maximal barrier, chlorhexidine prep, review necessity", "Prophylactic IV antibiotics for all lines", "Changing dressings daily without indication"], 1, "Evidence-based bundle reduces bloodstream infections.", source_key="microbiology"),
        mcq("micro-q08", "A nurse with influenza should:", ["Continue working with surgical mask", "Receive prophylactic antibiotics and work", "Stay home until fever-free per policy; antivirals if indicated", "Wear N95 and continue all assignments"], 2, "Work restriction prevents nosocomial spread.", source_key="microbiology"),
        mcq("micro-q09", "Gram stain of Gram-negative organisms shows:", ["Purple cocci in clusters", "Pink/red rod-shaped bacteria", "Acid-fast bacilli", "No cell wall"], 1, "Gram- bacteria have thin peptidoglycan and lipopolysaccharide outer membrane — stain pink.", source_key="microbiology"),
        mcq("micro-q10", "Antimicrobial stewardship prioritizes:", ["Broadest spectrum for all infections", "Shortest effective course per culture/guideline", "Completing saved antibiotics at home", "Prophylactic antibiotics for all surgical patients indefinitely"], 1, "Stewardship limits resistance and CDI.", source_key="microbiology"),
    ]
    application_questions = [
        mcq("micro-app01", "You enter a room after C. diff care without soap-and-water hand hygiene. What is the risk?", ["No risk if gloves were worn", "Spores may spread to next patient via contact", "Alcohol gel kills spores adequately", "Only airborne spread occurs"], 1, "Gloves do not replace hand hygiene; spores persist on hands.", nclex_category="Management of Care", source_key="microbiology"),
        mcq("micro-app02", "Post-op patient develops fever and erythema at IV site with purulent drainage. Priority nursing action?", ["Apply warm compress and continue infusion", "Stop infusion, notify provider, culture site per order", "Start prophylactic vancomycin independently", "Document and reassess next shift"], 1, "Suspected line infection — stop infusion, notify, culture.", source_key="microbiology"),
        mcq("micro-app03", "Roommate of patient with new MRSA wound infection should:", ["Share bathroom without precautions", "Be screened/cohorted per policy; contact precautions for index patient", "Receive prophylactic oral antibiotics", "Be discharged immediately"], 1, "Contact precautions for MRSA; screen contacts per facility policy.", source_key="microbiology"),
        mcq("micro-app04", "During influenza season, unvaccinated nurse develops fever and myalgia. Best action?", ["Wear droplet PPE and continue assignments", "Self-isolate and notify occupational health per policy", "Take leftover patient antibiotics", "Administer influenza vaccine therapeutically only"], 1, "Ill HCP should not care for high-risk patients.", source_key="microbiology"),
        mcq("micro-app05", "Patient on ventilator — which intervention reduces VAP risk?", ["Supine flat positioning", "HOB 30–45°, oral care, subglottic suction per protocol", "Sedation to avoid coughing", "Change ventilator circuit hourly"], 1, "Ventilator bundle elements reduce aspiration pneumonia.", source_key="microbiology"),
    ]
    break_chain_scenarios = [
        {"id": "bcs-01", "title": "MRSA Contact Precautions", "scenario": "New admission with MRSA in wound culture.", "target_link": "transmission", "question": "Which intervention best breaks transmission?", "options": ["Gown and gloves on room entry", "Routine prophylactic vancomycin for roommate", "Alcohol gel only after room exit", "No PPE if hands look clean"], "correct_index": 0, "explanation": "Contact precautions with gown/gloves block contact transmission.", "clinical_why": "Dedicated equipment and hand hygiene complete the bundle.", "source": s},
        {"id": "bcs-02", "title": "C. diff Outbreak", "scenario": "Three patients on unit develop watery diarrhea on antibiotics.", "target_link": "transmission", "question": "Priority environmental intervention?", "options": ["Alcohol dispensers at every door", "Bleach-based cleaning of high-touch surfaces", "UV lights only", "Open windows"], "correct_index": 1, "explanation": "C. diff spores require sporicidal cleaning.", "clinical_why": "Pair with soap-and-water hand hygiene and contact precautions.", "source": s},
        {"id": "bcs-03", "title": "Needlestick Injury", "scenario": "Nurse sustains percutaneous injury from used needle.", "target_link": "portal_entry", "question": "Immediate priority?", "options": ["Finish medication administration first", "Wash area, report exposure, initiate PEP per protocol", "Ignore if patient is low-risk", "Apply alcohol only"], "correct_index": 1, "explanation": "Bloodborne pathogen exposure protocol starts immediately.", "clinical_why": "HBV/HCV/HIV PEP windows are time-sensitive.", "source": s},
        {"id": "bcs-04", "title": "Neutropenic Patient", "scenario": "Chemotherapy patient ANC 400/mm³.", "target_link": "host", "question": "Which nursing measure protects susceptible host?", "options": ["Fresh flowers in room", "Protective precautions: cooked food, avoid ill visitors", "Shared nebulizer without cleaning", "Raw vegetable salad from cafeteria"], "correct_index": 1, "explanation": "Reverse/protective precautions reduce exposure to pathogens.", "clinical_why": "Low ANC — fever is emergency; no live plants.", "source": s},
        {"id": "bcs-05", "title": "TB Rule-Out", "scenario": "Patient with chronic cough, night sweats, positive quantiferon.", "target_link": "transmission", "question": "First placement action?", "options": ["Private room with door closed; airborne precautions until ruled out", "Droplet mask only at bedside", "No precautions until sputum returns", "Contact precautions only"], "correct_index": 0, "explanation": "Suspected TB requires airborne isolation immediately.", "clinical_why": "N95 fit-tested respirator; AIIR when available.", "source": s},
    ]
    what_if_scenarios = [
        {"id": "wif-01", "title": "What if alcohol gel is used after C. diff care?", "scenario": "Nurse uses alcohol hand rub leaving C. diff room.", "question": "Expected outcome?", "options": ["Spores eliminated", "Spores remain viable on hands — transmission risk continues", "Contact precautions no longer needed", "Patient develops immunity"], "correct_index": 1, "explanation": "Alcohol does not kill C. diff spores.", "clinical_why": "Soap-and-water with friction is required.", "source": s},
        {"id": "wif-02", "title": "What if urinary catheter stays 10 days without indication?", "scenario": "Indwelling catheter without daily necessity review.", "question": "Primary HAI risk?", "options": ["VAP", "CAUTI", "SSI", "CDI"], "correct_index": 1, "explanation": "Prolonged catheterization is leading CAUTI risk.", "clinical_why": "Remove as soon as clinically appropriate.", "source": s},
        {"id": "wif-03", "title": "What if broad-spectrum antibiotics continue 14 days without indication?", "scenario": "Patient improves but antibiotics not discontinued.", "question": "Most likely complication?", "options": ["C. difficile infection", "Improved resistance only in patient", "No effect", "Immediate cure"], "correct_index": 0, "explanation": "Disrupted microbiome allows C. diff overgrowth.", "clinical_why": "Stewardship — shortest effective course.", "source": s},
        {"id": "wif-04", "title": "What if ventilated patient supine 24 hours?", "scenario": "HOB kept flat for comfort.", "question": "Aspiration/VAP risk?", "options": ["Decreases", "Increases — aspiration and VAP risk rise", "Unchanged", "Eliminated with sedation"], "correct_index": 1, "explanation": "Supine position promotes aspiration.", "clinical_why": "HOB 30–45° unless contraindicated.", "source": s},
    ]
    return {
        "module_id": "microbiology",
        "title": "Microbiology & Infection Control",
        "infection_chain": infection_chain,
        "chain_interventions": _chain_interventions(),
        "microbe_classification": [
            {"type": "Bacteria", "icon": "🦠", "cell_type": "Prokaryote", "structure": "Prokaryotic cells with peptidoglycan cell wall; classified by Gram stain (Gram-positive vs Gram-negative) and shape (cocci, bacilli).", "treatment": "Antibiotics guided by culture/sensitivity and Gram stain; supportive care; antimicrobial stewardship — shortest effective course.", "notes": "Most treatable with antibiotics; Gram stain guides empiric therapy.", "examples": ["Staphylococcus aureus (MRSA)", "Escherichia coli", "Mycobacterium tuberculosis", "Streptococcus pyogenes"], "clinical_why": "Gram stain guides empiric antibiotics before culture results return — nurses monitor for allergy, C. diff risk, and MDRO transmission."},
            {"type": "Viruses", "icon": "🧬", "cell_type": "Acellular", "structure": "Acellular particles with protein capsid (and envelope in some); obligate intracellular parasites requiring host cells to replicate.", "treatment": "Antivirals when available (e.g., influenza, HIV, HSV); supportive care; vaccination for prevention; antibiotics are ineffective.", "notes": "Require host cell; antivirals limited; vaccines prevent many.", "examples": ["Influenza", "HIV", "RSV", "Norovirus", "SARS-CoV-2"], "clinical_why": "Isolation precautions and symptom management are nursing priorities — droplet for influenza, contact for norovirus, standard plus transmission-based per pathogen."},
            {"type": "Fungi", "icon": "🍄", "cell_type": "Eukaryote", "structure": "Eukaryotic organisms with chitin cell walls; include yeasts (single-celled) and molds (filamentous).", "treatment": "Antifungals matched to organism (azole, echinocandin, amphotericin); remove indwelling devices when Candida involved; environmental cleaning for mold.", "notes": "Antifungals needed; opportunistic in immunocompromised.", "examples": ["Candida albicans", "Aspergillus", "Cryptococcus", "Candida auris"], "clinical_why": "Opportunistic in immunocompromised, ICU, and broad-spectrum antibiotic recipients — C. auris requires contact precautions and EPA-registered disinfectant."},
            {"type": "Parasites", "icon": "🔬", "cell_type": "Eukaryote", "structure": "Eukaryotic — protozoa (single-celled) and helminths (multicellular worms); life cycles may involve multiple hosts.", "treatment": "Antiparasitic agents specific to organism (metronidazole, ivermectin, antimalarials); fluid/electrolyte support; prevention via sanitation and safe water.", "notes": "Protozoa and helminths; travel and sanitation relevant.", "examples": ["Giardia lamblia", "Plasmodium (malaria)", "Enterobius (pinworm)", "Toxoplasma gondii"], "clinical_why": "Travel history, water exposure, and sanitation guide suspicion — stool ova/parasite exams and travel screening support diagnosis."},
            {"type": "Prions", "icon": "⚠️", "cell_type": "Proteinaceous infectious particle", "structure": "Misfolded proteins (no DNA/RNA); resist heat and standard chemical disinfection — not living cells.", "treatment": "No curative treatment; palliative and supportive care; strict instrument reprocessing and notification for neurosurgical exposure.", "notes": "No routine sterilization in community settings; CJD precautions for neuro tissue.", "examples": ["Creutzfeldt-Jakob disease (CJD)", "Variant CJD"], "clinical_why": "Standard steam sterilization may not inactivate prions — notify infection control immediately for neuro tissue or high-risk instrument exposure."},
        ],
        "healthcare_pathogens": pathogens,
        "concepts": concepts,
        "gram_stain_procedure": [
            "Fix smear with heat or methanol",
            "Crystal violet (primary stain) — all cells purple",
            "Iodine mordant — forms crystal violet-iodine complex",
            "Alcohol decolorization — Gram- lose purple; Gram+ retain",
            "Safranin counterstain — Gram- appear pink/red",
            "Microscopic examination and report",
        ],
        "gram_stain_interpretation": {
            "gram_positive": {"appearance": "Purple/blue cocci or rods", "cell_wall": "Thick peptidoglycan retains crystal violet", "examples": ["Staphylococcus", "Streptococcus", "Clostridioides difficile"]},
            "gram_negative": {"appearance": "Pink/red rods or cocci", "cell_wall": "Thin peptidoglycan + outer membrane with LPS", "examples": ["E. coli", "Pseudomonas", "Klebsiella"]},
            "clinical_note": "Gram stain guides empiric antibiotics before culture sensitivities return.",
        },
        "hand_hygiene": {
            "who_five_moments": ["Before touching a patient", "Before clean/aseptic procedure", "After body fluid exposure risk", "After touching a patient", "After touching patient surroundings"],
            "soap_and_water_required": ["C. difficile", "Norovirus", "Visible soil on hands", "After caring for patients with infectious spores"],
            "alcohol_rub": "Effective for most routine care when hands not visibly soiled — rub until dry.",
            "nursing_priority": "Single most effective action to prevent HAI.",
        },
        "ppe_guide": {
            "gloves": "When contact with blood/body fluids, mucous membranes, non-intact skin anticipated",
            "gown": "Contact precautions; substantial splash risk",
            "mask": "Droplet precautions; surgical mask within 3–6 ft",
            "eye_protection": "Splash/spray risk to mucous membranes",
            "n95": "Airborne precautions — fit-tested respirator",
            "sequence": "Don: gown → mask/respirator → goggles → gloves. Doff inside room avoiding contamination.",
        },
        "hai_types": [
            {"id": "clabsi", "name": "CLABSI", "definition": "Central line-associated bloodstream infection", "bundle": ["Hand hygiene", "Maximal barrier on insertion", "Chlorhexidine skin prep", "Daily line necessity review"]},
            {"id": "cauti", "name": "CAUTI", "definition": "Catheter-associated UTI", "bundle": ["Insert only when indicated", "Maintain closed drainage", "Remove ASAP", "Perineal care"]},
            {"id": "vap", "name": "VAP", "definition": "Ventilator-associated pneumonia", "bundle": ["HOB 30–45°", "Oral care", "Sedation vacation per protocol", "DVT prophylaxis"]},
            {"id": "ssi", "name": "SSI", "definition": "Surgical site infection", "bundle": ["Antibiotic prophylaxis per protocol", "Glucose control", "Hair removal with clippers", "Normothermia"]},
            {"id": "cdi", "name": "CDI", "definition": "Clostridioides difficile infection", "bundle": ["Antibiotic stewardship", "Contact precautions", "Soap-and-water HH", "Bleach cleaning"]},
        ],
        "break_chain_scenarios": break_chain_scenarios,
        "what_if_scenarios": what_if_scenarios,
        "break_points": [
            "Hand hygiene before and after every patient contact",
            "Transmission-based precautions matched to pathogen",
            "Remove invasive devices as soon as clinically safe",
            "Antimicrobial stewardship — culture before antibiotics when possible",
            "Environmental cleaning with organism-appropriate disinfectant",
        ],
        "practice_questions": practice_questions,
        "application_questions": application_questions,
        "source": s,
    }