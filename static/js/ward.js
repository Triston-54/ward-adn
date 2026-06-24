/**
 * The Ward — Global JavaScript utilities
 * Command palette, source verification, Socratic tutor, keyboard shortcuts
 */

const MODULE_PATH_MAP = {
    '/index.html': 'general',
    '/modules/terminology.html': 'terminology',
    '/modules/terminology': 'terminology',
    '/modules/microbiology.html': 'microbiology',
    '/modules/microbiology': 'microbiology',
    '/modules/dosage.html': 'dosage',
    '/modules/dosage': 'dosage',
    '/modules/assessment.html': 'assessment',
    '/modules/assessment': 'assessment',
    '/modules/mental-health.html': 'mental_health',
    '/modules/mental-health': 'mental_health',
    '/modules/pathophysiology.html': 'pathophysiology',
    '/modules/pathophysiology': 'pathophysiology',
    '/modules/maternal-child.html': 'maternal_child',
    '/modules/maternal-child': 'maternal_child',
    '/modules/med_surg.html': 'med_surg',
    '/modules/maternal_newborn.html': 'maternal_newborn',
    '/modules/pediatrics.html': 'pediatrics',
    '/nclex-prep.html': 'nclex_prep',
    '/how-to-use.html': 'how_to_use',
    '/audit': 'audit',
};

const MODULE_TAB_DEFAULTS = {
    '/modules/terminology.html': 'builder',
    '/modules/terminology': 'builder',
    '/modules/microbiology.html': 'chain',
    '/modules/microbiology': 'chain',
    '/modules/dosage.html': 'calculator',
    '/modules/dosage': 'calculator',
    '/modules/assessment.html': 'head-to-toe',
    '/modules/assessment': 'head-to-toe',
    '/modules/mental-health.html': 'therapeutic-communication',
    '/modules/mental-health': 'therapeutic-communication',
    '/modules/pathophysiology.html': 'core-concepts',
    '/modules/pathophysiology': 'core-concepts',
    '/modules/maternal-child.html': 'antepartum',
    '/modules/maternal-child': 'antepartum',
    '/modules/med_surg.html': 'core-concepts',
    '/modules/maternal_newborn.html': 'antepartum',
    '/modules/pediatrics.html': 'milestones',
    '/nclex-prep.html': 'practice',
};

function goToModuleTab(path, tab) {
    const legacyPath = path.replace(/\.html$/, '');
    const def = MODULE_TAB_DEFAULTS[path] || MODULE_TAB_DEFAULTS[legacyPath] || '';
    const navPath = path.endsWith('.html') ? path : `${path}.html`;

    if (typeof WardTabs !== 'undefined') {
        const onModule = location.pathname === path
            || location.pathname === legacyPath
            || location.pathname.endsWith(navPath);
        if (onModule) {
            WardTabs.goTo(legacyPath, tab, def);
            return;
        }
    }

    const navDef = MODULE_TAB_DEFAULTS[navPath] || def;
    location.href = tab && tab !== navDef ? `${navPath}#${tab}` : navPath;
}

const MODULE_LABELS = {
    terminology: 'Medical Terminology',
    microbiology: 'Microbiology',
    dosage: 'NURS 145 — Dosage',
    assessment: 'NURS 146 — Health Assessment',
    mental_health: 'NURS 147 — Mental Health',
    pathophysiology: 'Pathophysiology',
    maternal_child: 'NURS 148 — Maternal-Child',
    med_surg: 'Medical-Surgical Nursing',
    maternal_newborn: 'Maternal-Newborn Nursing',
    pediatrics: 'Pediatric Nursing',
    nclex_prep: 'NCLEX Prep',
    audit: 'Content Audit',
    general: 'General Nursing',
};

let currentModule = detectCurrentModule();
let _sourceCache = [];

const REF_TYPE_LABELS = {
    textbook: 'Textbook',
    oer: 'OER Textbook',
    nclex: 'NCLEX Blueprint',
    guideline: 'Clinical Guideline',
    curriculum: 'Program Curriculum',
    reference: 'Reference',
};

// ── Module detection ──────────────────────────────────────────────────────────

function detectCurrentModule() {
    const path = window.location.pathname;
    if (path === '/' || path.endsWith('/index.html')) return 'general';
    for (const [prefix, moduleId] of Object.entries(MODULE_PATH_MAP)) {
        if (path.startsWith(prefix) || path.endsWith(prefix)) return moduleId;
    }
    return 'general';
}

// Auto-detect on load and navigation
document.addEventListener('DOMContentLoaded', () => {
    currentModule = detectCurrentModule();
    const dataMod = document.querySelector('[data-module]')?.dataset?.module;
    if (dataMod) currentModule = dataMod;
    fetch('/api/socratic/config')
        .then(r => r.ok ? r.json() : null)
        .then(cfg => {
            if (cfg) {
                window.__wardSocraticConfig = cfg;
                registerSocraticCommandsFromRegistry(cfg);
            }
        })
        .catch(() => {});
});

// ── Command Palette ─────────────────────────────────────────────────────────

const GLOBAL_COMMANDS = [
    { id: 'home', name: 'Dashboard', section: 'Navigate', action: () => location.href = '/index.html', keywords: 'home overview dashboard' },
    { id: 'how-to-use', name: 'How to Use The Ward', section: 'Navigate', action: () => location.href = '/how-to-use.html', keywords: 'guide help study workflow nclex strategy student how to use' },
    { id: 'terminology', name: 'Medical Terminology', section: 'Navigate', action: () => location.href = '/modules/terminology.html', keywords: 'terms words prefix suffix' },
    { id: 'microbiology', name: 'Microbiology', section: 'Navigate', action: () => location.href = '/modules/microbiology.html', keywords: 'infection bacteria virus chain' },
    { id: 'dosage', name: 'NURS 145 — Dosage', section: 'Navigate', action: () => location.href = '/modules/dosage.html', keywords: 'nurs 145 math calculate iv drug' },
    { id: 'assessment', name: 'NURS 146 — Health Assessment', section: 'Navigate', action: () => location.href = '/modules/assessment.html', keywords: 'nurs 146 head to toe physical exam health assessment' },
    { id: 'mental-health', name: 'NURS 147 — Mental Health', section: 'Navigate', action: () => location.href = '/modules/mental-health.html', keywords: 'nurs 147 psychosocial therapeutic communication suicide safety mental health' },
    { id: 'pathophysiology', name: 'Pathophysiology', section: 'Navigate', action: () => location.href = '/modules/pathophysiology.html', keywords: 'patho disease process inflammation shock CHF COPD diabetes renal cascade' },
    { id: 'maternal-child', name: 'NURS 148 — Maternal-Child', section: 'Navigate', action: () => location.href = '/modules/maternal-child.html', keywords: 'nurs 148 ob obstetric labor delivery newborn pediatric peds pregnancy maternal child' },
    { id: 'med-surg', name: 'Medical-Surgical Nursing', section: 'Navigate', action: () => location.href = '/modules/med_surg.html', keywords: 'med surg adult nursing' },
    { id: 'maternal-newborn', name: 'Maternal-Newborn Nursing', section: 'Navigate', action: () => location.href = '/modules/maternal_newborn.html', keywords: 'ob labor delivery newborn' },
    { id: 'pediatrics', name: 'Pediatric Nursing', section: 'Navigate', action: () => location.href = '/modules/pediatrics.html', keywords: 'peds pediatric milestones' },
    { id: 'nclex-prep', name: 'NCLEX Prep Center', section: 'Navigate', action: () => location.href = '/nclex-prep.html', keywords: 'nclex rn practice rationales clinical judgment' },
    { id: 'socratic', name: 'Socratic Tutor', section: 'Actions', action: () => openSocraticMode(), keywords: 'ask ai explain help tutor socratic teaching partner preceptor guide' },
    { id: 'socratic-explore', name: 'Ask Guiding Questions', section: 'Socratic', action: () => openSocraticMode(), keywords: 'socratic explore guide think first questions ask before tell' },
    { id: 'socratic-mechanism', name: 'Explain the Mechanism', section: 'Socratic', action: () => { openSocraticMode(); askSocraticIntent('explain_mechanism'); }, keywords: 'mechanism drug pathophysiology how works moa socratic' },
    { id: 'socratic-clinical', name: 'Why Clinically?', section: 'Socratic', action: () => { openSocraticMode(); askSocraticIntent('clinical_why'); }, keywords: 'clinical why bedside nursing safety nclex naplex socratic' },
    { id: 'socratic-further', name: 'Explain Further', section: 'Socratic', action: () => { openSocraticMode(); askSocraticIntent('explain_further'); }, keywords: 'deeper layer teach more socratic explain further' },
    { id: 'socratic-considerations', name: 'Professional Considerations', section: 'Socratic', action: () => { openSocraticMode(); askSocraticIntent('professional_considerations'); }, keywords: 'nursing pharmacist considerations monitoring counseling safety socratic' },
    { id: 'verify', name: 'Verify Source', section: 'Actions', action: () => verifySource(currentModule), keywords: 'source citation reference verify' },
    { id: 'sync', name: 'Sync Progress', section: 'Actions', action: () => syncProgress(), keywords: 'save database sync progress' },
    { id: 'content-audit', name: 'Content Audit', section: 'Tools', action: () => location.href = '/audit', keywords: 'audit review verify flag correctness content admin' },
];

const MODULE_COMMANDS = {
    terminology: [
        { id: 'term-dashboard', name: 'Nursing Dashboard', section: 'Terminology', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'term-builder', name: 'Word Builder', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'builder'), keywords: 'build decode prefix root suffix', hint: 'Tab' },
        { id: 'term-database', name: 'Term Database', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'database'), keywords: 'search lookup glossary', hint: 'Tab' },
        { id: 'term-flashcards', name: 'Terminology Flashcards', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'flashcards'), keywords: 'srs study cards spaced repetition', hint: 'Tab' },
        { id: 'term-practice', name: 'Terminology Practice', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'practice'), keywords: 'quiz nclex test', hint: 'Tab' },
        { id: 'term-myterms', name: 'Add Custom Term', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'myterms'), keywords: 'create custom my terms glossary', hint: 'Tab' },
        { id: 'term-export', name: 'Export Terminology', section: 'Terminology', action: () => goToModuleTab('/modules/terminology.html', 'export'), keywords: 'download pdf markdown json', hint: 'Tab' },
        { id: 'term-export-md', name: 'Export Term Flashcards (MD)', section: 'Terminology · Export', action: () => exportFlashcardsGlobal(), keywords: 'markdown anki download flashcards', hint: 'Export' },
        { id: 'term-copy-50', name: 'Copy 50 Terms (Clipboard)', section: 'Terminology · Export', action: () => { if (typeof Terminology !== 'undefined') Terminology.copyToClipboard(50); else goToModuleTab('/modules/terminology.html', 'export'); }, keywords: 'clipboard copy glossary definitions', hint: 'Export' },
        { id: 'term-socratic', name: 'Socratic — Terminology', section: 'Socratic', action: () => openSocraticMode('terminology'), keywords: 'tutor ask explain term prefix' },
    ],
    microbiology: [
        { id: 'micro-dashboard', name: 'Nursing Dashboard', section: 'Microbiology', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'micro-chain', name: 'Chain Builder', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'chain'), keywords: 'infection chain links', hint: 'Tab' },
        { id: 'micro-learn', name: 'Learn Pathogens', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'learn'), keywords: 'pathogen precautions', hint: 'Tab' },
        { id: 'micro-break', name: 'Break the Chain', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'break-chain'), keywords: 'scenario clinical', hint: 'Tab' },
        { id: 'micro-whatif', name: 'What-If Scenarios', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'what-if'), keywords: 'judgment infection control', hint: 'Tab' },
        { id: 'micro-flashcards', name: 'Pathogen Flashcards', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'flashcards'), keywords: 'study cards pathogens deck export', hint: 'Tab' },
        { id: 'micro-practice', name: 'Microbiology Practice', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'practice'), keywords: 'nclex quiz', hint: 'Tab' },
        { id: 'micro-export', name: 'Export Microbiology', section: 'Microbiology', action: () => goToModuleTab('/modules/microbiology.html', 'export'), keywords: 'download cheat sheet markdown', hint: 'Tab' },
        { id: 'micro-export-md', name: 'Export Pathogen Flashcards (MD)', section: 'Microbiology · Export', action: () => exportFlashcardsGlobal(), keywords: 'markdown anki deck download', hint: 'Export' },
        { id: 'micro-socratic', name: 'Socratic — Microbiology', section: 'Socratic', action: () => openSocraticMode('microbiology', 'pathophysiology'), keywords: 'tutor pathogen infection chain' },
    ],
    audit: [
        { id: 'audit-dashboard', name: 'Audit Dashboard', section: 'Content Audit', action: () => location.href = '/audit', keywords: 'review verify flag content' },
        { id: 'audit-terminology', name: 'Audit — Terminology', section: 'Content Audit', action: () => location.href = '/audit?module=terminology', keywords: 'terms glossary review' },
        { id: 'audit-microbiology', name: 'Audit — Microbiology', section: 'Content Audit', action: () => location.href = '/audit?module=microbiology', keywords: 'infection pathogens review' },
        { id: 'audit-dosage', name: 'Audit — Dosage', section: 'Content Audit', action: () => location.href = '/audit?module=dosage', keywords: 'calculations review' },
        { id: 'audit-assessment', name: 'Audit — Assessment', section: 'Content Audit', action: () => location.href = '/audit?module=assessment', keywords: 'head to toe review' },
        { id: 'audit-mental-health', name: 'Audit — Mental Health', section: 'Content Audit', action: () => location.href = '/audit?module=mental_health', keywords: 'psychosocial therapeutic communication review' },
        { id: 'audit-pathophysiology', name: 'Audit — Pathophysiology', section: 'Content Audit', action: () => location.href = '/audit?module=pathophysiology', keywords: 'disease cascade concepts review' },
        { id: 'audit-maternal-child', name: 'Audit — Maternal-Child', section: 'Content Audit', action: () => location.href = '/audit?module=maternal_child', keywords: 'ob obstetric pediatric review' },
    ],
    dosage: [
        { id: 'dose-dashboard', name: 'Nursing Dashboard', section: 'Dosage', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'dose-calc', name: 'Dosage Calculator', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'calculator'), keywords: 'calculate sympy dimensional analysis katex', hint: 'Tab' },
        { id: 'dose-practice', name: 'Dosage Practice', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'practice'), keywords: 'problems quiz', hint: 'Tab' },
        { id: 'dose-traps', name: 'Error Traps', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'traps'), keywords: 'mistakes safety', hint: 'Tab' },
        { id: 'dose-pharm', name: 'Pharmacology', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'pharm'), keywords: 'drug classes analgesics antibiotics cardiovascular MOA nursing implications interactions', hint: 'Tab' },
        { id: 'dose-favorites', name: 'Saved Calculations', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'favorites'), keywords: 'favorites saved', hint: 'Tab' },
        { id: 'dose-export', name: 'Export Dosage', section: 'Dosage', action: () => goToModuleTab('/modules/dosage.html', 'export'), keywords: 'practice sheet traps pdf', hint: 'Tab' },
        { id: 'dose-export-calc', name: 'Export Last Calculation', section: 'Dosage · Export', action: () => { if (typeof Dosage !== 'undefined') Dosage.exportLastCalculation(); else goToModuleTab('/modules/dosage.html', 'export'); }, keywords: 'sympy katex worksheet print pdf calculation', hint: 'Export' },
        { id: 'dose-socratic', name: 'Socratic — Dosage', section: 'Socratic', action: () => openSocraticMode('dosage', 'calculation'), keywords: 'tutor calculate dimensional analysis' },
    ],
    assessment: [
        { id: 'ha-dashboard', name: 'Nursing Dashboard', section: 'Assessment', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'ha-head', name: 'Head-to-Toe Assessment', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'head-to-toe'), keywords: 'sequence vitals', hint: 'Tab' },
        { id: 'ha-systems', name: 'Body Systems', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'systems'), keywords: 'normal abnormal findings', hint: 'Tab' },
        { id: 'ha-checklists', name: 'Assessment Checklists', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'checklists'), keywords: 'interactive checklist', hint: 'Tab' },
        { id: 'ha-assess-next', name: 'Assess Next Scenarios', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'assess-next'), keywords: 'clinical judgment priority', hint: 'Tab' },
        { id: 'ha-soap', name: 'SOAP Documentation', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'soap'), keywords: 'documentation notes', hint: 'Tab' },
        { id: 'ha-documentation', name: 'Documentation Practice', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'documentation'), keywords: 'soap validate sbar handoff feedback', hint: 'Tab' },
        { id: 'ha-flashcards', name: 'Assessment Flashcards', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'flashcards'), keywords: 'normal abnormal findings deck srs', hint: 'Tab' },
        { id: 'ha-special', name: 'Special Populations', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'special-pop'), keywords: 'pediatric geriatric ob obstetric', hint: 'Tab' },
        { id: 'ha-redflags', name: 'Assessment Red Flags', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'red-flags'), keywords: 'critical emergency', hint: 'Tab' },
        { id: 'ha-redflag-drill', name: 'Red Flag Drill', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'red-flag-drill'), keywords: 'triage emergency critical action escalation drill', hint: 'Tab' },
        { id: 'ha-skills', name: 'Assessment Skills', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'skills'), keywords: 'technique ausculatation orthostatic fast stroke', hint: 'Tab' },
        { id: 'ha-practice', name: 'Assessment Practice', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'practice'), keywords: 'nclex quiz', hint: 'Tab' },
        { id: 'ha-export', name: 'Export Assessment', section: 'Assessment', action: () => goToModuleTab('/modules/assessment.html', 'export'), keywords: 'download pdf checklist red flags head to toe', hint: 'Tab' },
        { id: 'ha-export-md', name: 'Export Assessment Flashcards (MD)', section: 'Assessment · Export', action: () => exportFlashcardsGlobal(), keywords: 'markdown anki deck download', hint: 'Export' },
        { id: 'ha-copy-head', name: 'Copy Head-to-Toe (Clipboard)', section: 'Assessment · Export', action: () => { if (typeof Assessment !== 'undefined') Assessment.copyHeadToToeClipboard(); else WardExport.copyExportText('/api/assessment/export/head-to-toe', 'Head-to-toe sequence copied to clipboard'); }, keywords: 'clipboard copy sequence vitals', hint: 'Export' },
        { id: 'ha-copy-redflags', name: 'Copy Red Flags (Clipboard)', section: 'Assessment · Export', action: () => { if (typeof Assessment !== 'undefined') Assessment.copyRedFlagsClipboard(); else WardExport.copyExportText('/api/assessment/export/red-flags', 'Red flags reference copied to clipboard'); }, keywords: 'clipboard copy critical emergency', hint: 'Export' },
        { id: 'ha-socratic', name: 'Socratic — Assessment', section: 'Socratic', action: () => openSocraticMode('assessment', 'assessment_finding'), keywords: 'tutor finding red flag head to toe' },
    ],
    mental_health: [
        { id: 'mh-dashboard', name: 'Nursing Dashboard', section: 'Mental Health', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'mh-comm', name: 'Therapeutic Communication', section: 'Mental Health', action: () => goToModuleTab('/modules/mental-health.html', 'therapeutic-communication'), keywords: 'open ended active listening reflection trauma informed', hint: 'Tab' },
        { id: 'mh-safety', name: 'Safety & Risk Assessment', section: 'Mental Health', action: () => goToModuleTab('/modules/mental-health.html', 'safety-risk'), keywords: 'suicide homicide ASQ CSSRS CIWA COWS 1:1 observation', hint: 'Tab' },
        { id: 'mh-flashcards', name: 'Safety Drill', section: 'Mental Health', action: () => goToModuleTab('/modules/mental-health.html', 'safety-risk'), keywords: 'suicide risk drill safety screening', hint: 'Tab' },
        { id: 'mh-socratic', name: 'Socratic — Mental Health', section: 'Socratic', action: () => openSocraticMode('mental_health', 'psychosocial'), keywords: 'tutor therapeutic communication suicide safety' },
    ],
    pathophysiology: [
        { id: 'patho-dashboard', name: 'Nursing Dashboard', section: 'Pathophysiology', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'patho-concepts', name: 'Core Concepts', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'core-concepts'), keywords: 'inflammation immune cellular adaptation ABG', hint: 'Tab' },
        { id: 'patho-diseases', name: 'Disease Processes', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'disease-processes'), keywords: 'CHF COPD diabetes shock sepsis renal', hint: 'Tab' },
        { id: 'patho-compare', name: 'Compare & Contrast', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'compare-contrast'), keywords: 'hypovolemic cardiogenic shock differentiation', hint: 'Tab' },
        { id: 'patho-scenarios', name: 'What Breaks Down', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'what-breaks-down'), keywords: 'cascade teaching scenario interactive', hint: 'Tab' },
        { id: 'patho-flashcards', name: 'Flashcards', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'flashcards'), keywords: 'study cards deck patho', hint: 'Tab' },
        { id: 'patho-practice', name: 'NCLEX Practice', section: 'Pathophysiology', action: () => goToModuleTab('/modules/pathophysiology.html', 'practice'), keywords: 'quiz nclex test questions', hint: 'Tab' },
        { id: 'patho-export-md', name: 'Export Pathophysiology Flashcards (MD)', section: 'Pathophysiology · Export', action: () => exportFlashcardsGlobal(), keywords: 'markdown anki deck download flashcards', hint: 'Export' },
        { id: 'patho-socratic', name: 'Socratic — Pathophysiology', section: 'Socratic', action: () => openSocraticMode('pathophysiology', 'pathophysiology'), keywords: 'tutor disease mechanism cascade inflammation' },
    ],
    maternal_child: [
        { id: 'mc-dashboard', name: 'Nursing Dashboard', section: 'Maternal-Child', action: () => location.href = '/index.html', keywords: 'home return dashboard overview', hint: 'Navigate' },
        { id: 'mc-antepartum', name: 'Antepartum', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'antepartum'), keywords: 'pregnancy trimester fetal development prenatal', hint: 'Tab' },
        { id: 'mc-intrapartum', name: 'Labor & Delivery', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'intrapartum'), keywords: 'labor stages FHR leopold decelerations', hint: 'Tab' },
        { id: 'mc-postpartum', name: 'Postpartum & Newborn', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'postpartum-newborn'), keywords: 'apgar breastfeeding bubble lochia', hint: 'Tab' },
        { id: 'mc-peds', name: 'Pediatrics', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'pediatrics'), keywords: 'milestones growth immunization fever', hint: 'Tab' },
        { id: 'mc-safety', name: 'Safety Red Flags', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'safety'), keywords: 'preeclampsia hemorrhage cord prolapse', hint: 'Tab' },
        { id: 'mc-drill', name: 'Complications Drill', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'complications-drill'), keywords: 'priority action scenario OB emergency', hint: 'Tab' },
        { id: 'mc-flashcards', name: 'Flashcards', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'flashcards'), keywords: 'study cards deck OB peds', hint: 'Tab' },
        { id: 'mc-practice', name: 'NCLEX Practice', section: 'Maternal-Child', action: () => goToModuleTab('/modules/maternal-child.html', 'practice'), keywords: 'quiz nclex test questions', hint: 'Tab' },
        { id: 'mc-export-md', name: 'Export Maternal-Child Flashcards (MD)', section: 'Maternal-Child · Export', action: () => exportFlashcardsGlobal(), keywords: 'markdown anki deck download flashcards ob peds', hint: 'Export' },
        { id: 'mc-socratic', name: 'Socratic — Maternal-Child', section: 'Socratic', action: () => openSocraticMode('maternal_child', 'assessment_finding'), keywords: 'tutor labor delivery newborn pediatric' },
    ],
};

let cmdFiltered = [];
let cmdSelectedIndex = 0;
let _registrySocraticCommands = [];

function runSocraticPaletteCommand(cmd) {
    const mod = cmd.module_id || currentModule;
    const topic = cmd.topic || undefined;
    openSocraticMode(mod, topic);
    if (cmd.intent && cmd.intent !== 'explore') {
        setTimeout(() => askSocraticIntent(cmd.intent), 50);
    }
}

function registerSocraticCommandsFromRegistry(cfg) {
    if (!cfg) return;
    const built = [];
    const palette = cfg.palette_commands || [];
    for (const cmd of palette) {
        built.push({
            id: cmd.id,
            name: cmd.name,
            section: cmd.section || 'Socratic',
            keywords: cmd.keywords || '',
            hint: 'Socratic',
            action: () => runSocraticPaletteCommand(cmd),
        });
    }
    if (cfg.modules) {
        for (const [mid, meta] of Object.entries(cfg.modules)) {
            if (mid === 'general') continue;
            const id = `socratic-registry-${mid}`;
            if (built.some(c => c.id === id)) continue;
            built.push({
                id,
                name: `Socratic — ${meta.label}`,
                section: 'Socratic',
                keywords: `socratic tutor ${mid.replace(/_/g, ' ')} ${meta.hint || ''}`,
                hint: 'Socratic',
                action: () => openSocraticMode(mid, meta.default_topic),
            });
        }
    }
    _registrySocraticCommands = built;
}

function getAllCommands() {
    const mod = MODULE_COMMANDS[currentModule] || [];
    const seen = new Set();
    const merged = [];
    for (const c of [...mod, ..._registrySocraticCommands, ...GLOBAL_COMMANDS]) {
        const key = c.id || c.name;
        if (seen.has(key)) continue;
        seen.add(key);
        merged.push(c);
    }
    return merged;
}

function scoreCommand(cmd, tokens) {
    if (!tokens.length) return 0;
    const name = cmd.name.toLowerCase();
    const keywords = (cmd.keywords || '').toLowerCase();
    const section = (cmd.section || '').toLowerCase();
    let score = 0;
    for (const t of tokens) {
        if (name === t) score += 100;
        else if (name.startsWith(t)) score += 50;
        else if (name.includes(t)) score += 30;
        if (keywords.split(/\s+/).some(k => k === t || k.startsWith(t))) score += 20;
        if (section.includes(t)) score += 10;
    }
    return score;
}

function filterCommands(query) {
    const q = query.toLowerCase().trim();
    const all = getAllCommands();
    if (!q) return all;
    const tokens = q.split(/\s+/).filter(Boolean);
    return all
        .map(c => ({ cmd: c, score: scoreCommand(c, tokens) }))
        .filter(x => x.score > 0)
        .sort((a, b) => b.score - a.score)
        .map(x => x.cmd);
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    sidebar?.classList.toggle('open');
    backdrop?.classList.toggle('open');
    backdrop?.classList.toggle('hidden');
}

function closeSidebar() {
    document.getElementById('sidebar')?.classList.remove('open');
    const backdrop = document.getElementById('sidebar-backdrop');
    backdrop?.classList.remove('open');
    backdrop?.classList.add('hidden');
}

// Close sidebar on navigation (mobile)
document.querySelectorAll('.sidebar-link[href]').forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth < 1024) closeSidebar();
    });
});

// ── Sync Progress ─────────────────────────────────────────────────────────────

async function syncProgress() {
    const btn = document.getElementById('sync-btn');
    const status = document.getElementById('sync-status');
    const statusText = document.getElementById('sync-status-text');

    if (btn) btn.classList.add('syncing');

    try {
        const res = await fetch('/api/progress/sync', { method: 'POST' });
        if (!res.ok) throw new Error('Sync failed');
        const data = await res.json();

        if (status && statusText) {
            status.classList.remove('hidden');
            const synced = new Date(data.synced_at).toLocaleString();
            statusText.textContent = `Synced ${synced}`;
        }

        showToast(data.message || 'Progress saved locally.');
    } catch {
        showToast('Sync failed — is the server running?', 'error');
    } finally {
        if (btn) btn.classList.remove('syncing');
    }
}

function showToast(message, type = 'success') {
    const existing = document.getElementById('ward-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'ward-toast';
    toast.className = `fixed bottom-4 right-4 z-50 px-4 py-2.5 rounded-lg text-sm shadow-lg transition-opacity ${
        type === 'error'
            ? 'bg-ward-danger/20 border border-ward-danger/40 text-ward-danger'
            : 'bg-ward-success/20 border border-ward-success/40 text-ward-success'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

function openCommandPalette() {
    currentModule = detectCurrentModule();
    const palette = document.getElementById('command-palette');
    palette.classList.remove('hidden');
    const input = document.getElementById('cmd-input');
    input.value = '';
    cmdSelectedIndex = 0;
    renderCommands('');
    input.focus();
    input.oninput = () => {
        cmdSelectedIndex = 0;
        renderCommands(input.value);
    };
    input.onkeydown = handleCommandInputKey;
}

function closeCommandPalette() {
    document.getElementById('command-palette').classList.add('hidden');
    const input = document.getElementById('cmd-input');
    if (input) input.onkeydown = null;
}

function renderCommands(query) {
    cmdFiltered = filterCommands(query);
    const container = document.getElementById('cmd-results');
    if (!container) return;

    if (!cmdFiltered.length) {
        container.innerHTML = '<p class="px-4 py-3 text-sm text-ward-500">No commands found</p>';
        return;
    }

    const modLabel = MODULE_LABELS[currentModule] || 'General';
    const contextChip = `<div class="cmd-context-chip">${escapeHtml(modLabel)} module</div>`;

    let lastSection = '';
    const items = cmdFiltered.map((c, i) => {
        const sectionHdr = c.section && c.section !== lastSection
            ? (lastSection = c.section, `<div class="px-4 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-ward-600">${escapeHtml(c.section)}</div>`)
            : '';
        const active = i === cmdSelectedIndex ? ' active' : '';
        const hint = c.hint ? `<span class="cmd-item-hint">${escapeHtml(c.hint)}</span>` : '';
        return `${sectionHdr}
            <button type="button" class="cmd-item w-full text-left px-4 py-2.5 text-sm hover:bg-ward-700/60 transition${active}"
                    data-cmd-index="${i}"
                    onclick="executeCommand(${i})">
                <span class="text-ward-200">${escapeHtml(c.name)}</span>
                ${hint}
            </button>`;
    }).join('');

    container.innerHTML = contextChip + items;

    const activeEl = container.querySelector('.cmd-item.active');
    activeEl?.scrollIntoView({ block: 'nearest' });
}

function executeCommand(index) {
    const cmd = cmdFiltered[index];
    if (!cmd) return;
    closeCommandPalette();
    cmd.action();
}

function handleCommandInputKey(e) {
    if (!cmdFiltered.length) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        cmdSelectedIndex = Math.min(cmdSelectedIndex + 1, cmdFiltered.length - 1);
        renderCommands(e.target.value);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        cmdSelectedIndex = Math.max(cmdSelectedIndex - 1, 0);
        renderCommands(e.target.value);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        executeCommand(cmdSelectedIndex);
    }
}

// ── Source Verification ─────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function refTypeBadge(source) {
    const style = source.reference_type_style || 'reference';
    const label = source.reference_type || REF_TYPE_LABELS[style] || 'Reference';
    return `<span class="verify-ref-badge verify-ref-${style}">${escapeHtml(label)}</span>`;
}

function renderSourceModal(source, nclexNote, verifyContext) {
    const modal = document.getElementById('source-modal');
    const content = document.getElementById('source-content');
    const citation = source.formatted_citation || source.citation || 'N/A';
    const verified = source.verified_date || '2026-06';
    const nclex = nclexNote || source.nclex_relevance || '';
    const rationale = source.rationale || (verifyContext && verifyContext.why_verify) || '';

    content.innerHTML = `
        <div class="space-y-4 text-sm">
            <div class="flex items-start gap-3 p-3 rounded-lg bg-ward-success/5 border border-ward-success/20">
                <svg class="w-5 h-5 text-ward-success shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                <div class="flex-1 min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                        <div class="text-xs text-ward-success uppercase tracking-wider font-medium">Verified Content</div>
                        ${refTypeBadge(source)}
                    </div>
                    <div class="text-ward-200 font-medium mt-1">${escapeHtml(source.title || 'Unknown')}</div>
                </div>
            </div>

            ${rationale ? `
            <div class="p-3 rounded-lg bg-ward-800/80 border border-ward-700">
                <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Why This Source</div>
                <p class="text-ward-300 text-xs leading-relaxed">${escapeHtml(rationale)}</p>
            </div>` : ''}

            <div>
                <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Citation</div>
                <div class="text-ward-300 leading-relaxed">${escapeHtml(citation)}</div>
            </div>

            ${source.url ? `
            <div>
                <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Reference URL</div>
                <a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer"
                   class="inline-flex items-center gap-1.5 text-ward-accent hover:underline break-all">
                    <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                    ${escapeHtml(source.url)}
                </a>
            </div>` : ''}

            <div class="flex items-center gap-4">
                <div>
                    <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Verified Date</div>
                    <div class="text-ward-400 font-mono text-xs">${escapeHtml(verified)}</div>
                </div>
            </div>

            ${nclex ? `
            <div class="p-3 rounded-lg bg-ward-accent/5 border border-ward-accent/20">
                <div class="text-xs text-ward-accent uppercase tracking-wider font-medium mb-1">NCLEX Relevance</div>
                <p class="text-ward-300 text-xs leading-relaxed">${escapeHtml(nclex)}</p>
            </div>` : ''}

            <p class="text-xs text-ward-500 pt-2 border-t border-ward-700 leading-relaxed">
                Content verified against nursing education standards including NCLEX test plan,
                Open RN OER textbooks, and standard nursing references.
            </p>
        </div>
    `;
    modal.classList.remove('hidden');
}

function showSource(source, moduleId) {
    const cache = window._socraticSourceCache || _sourceCache;
    if (typeof source === 'number' && cache[source]) {
        renderSourceModal(cache[source], cache[source].nclex_relevance);
        return;
    }
    const enriched = {
        ...source,
        reference_type: source.reference_type || 'Module Content',
        reference_type_style: source.reference_type_style || 'reference',
        rationale: source.rationale || '',
        formatted_citation: source.formatted_citation || source.citation,
    };
    renderSourceModal(enriched, source.nclex_relevance);
}

async function verifySource(moduleId) {
    const id = moduleId || currentModule;
    try {
        const res = await fetch(`/api/verify/sources/${encodeURIComponent(id)}`);
        if (!res.ok) throw new Error('Failed to load sources');
        const data = await res.json();

        _sourceCache = (data.sources || []).map(s => ({
            ...s,
            nclex_relevance: data.nclex_relevance,
        }));

        if (_sourceCache.length === 1) {
            showSource(0);
            return;
        }

        const modal = document.getElementById('source-modal');
        const content = document.getElementById('source-content');
        const ctx = data.verify_context || {};
        content.innerHTML = `
            <div class="space-y-4 text-sm">
                <div>
                    <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Module</div>
                    <div class="text-ward-200 font-medium">${escapeHtml(MODULE_LABELS[id] || id)}</div>
                </div>
                ${ctx.summary ? `
                <div class="p-3 rounded-lg bg-ward-800/80 border border-ward-700">
                    <div class="text-xs text-ward-500 uppercase tracking-wider mb-1">Content Rationale</div>
                    <p class="text-ward-300 text-xs leading-relaxed">${escapeHtml(ctx.summary)}</p>
                    ${ctx.why_verify ? `<p class="text-ward-400 text-xs mt-2 italic">${escapeHtml(ctx.why_verify)}</p>` : ''}
                </div>` : ''}
                ${data.nclex_relevance ? `
                <div class="p-3 rounded-lg bg-ward-accent/5 border border-ward-accent/20">
                    <div class="text-xs text-ward-accent uppercase tracking-wider font-medium mb-1">NCLEX Relevance</div>
                    <p class="text-ward-300 text-xs leading-relaxed">${escapeHtml(data.nclex_relevance)}</p>
                </div>` : ''}
                <div class="space-y-2">
                    <div class="text-xs text-ward-500 uppercase tracking-wider">Verified Sources (${data.count})</div>
                    ${_sourceCache.map((s, i) => `
                        <button onclick="showSource(${i})"
                                class="w-full text-left p-3 rounded-lg border border-ward-700 hover:border-ward-accent/40 hover:bg-ward-700/30 transition">
                            <div class="flex items-center gap-2 flex-wrap">
                                <div class="text-ward-200 font-medium text-sm">${escapeHtml(s.title)}</div>
                                ${refTypeBadge(s)}
                            </div>
                            ${s.rationale ? `<p class="text-ward-400 text-xs mt-1 line-clamp-2">${escapeHtml(s.rationale)}</p>` : ''}
                            <div class="text-ward-500 text-xs mt-1 line-clamp-2">${escapeHtml(s.citation)}</div>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        modal.classList.remove('hidden');
    } catch {
        showToast('Could not load verified sources.', 'error');
    }
}

function closeSourceModal() {
    document.getElementById('source-modal').classList.add('hidden');
}

// Socratic tutor — see static/js/socratic.js (WardSocratic component)

// ── Export ────────────────────────────────────────────────────────────────────

async function exportFlashcardsGlobal() {
    const mod = detectCurrentModule();
    const endpoints = {
        terminology: { url: '/api/terminology/export/flashcards', file: 'ward-terminology-flashcards.md' },
        microbiology: { url: '/api/microbiology/export/flashcards', file: 'ward-microbiology-flashcards.md' },
        assessment: { url: '/api/assessment/export/flashcards', file: 'ward-assessment-flashcards.md' },
        pathophysiology: { url: '/api/pathophysiology/export/flashcards', file: 'ward-pathophysiology-flashcards.md' },
        maternal_child: { url: '/api/maternal-child/export/flashcards', file: 'ward-maternal-child-flashcards.md' },
    };
    const cfg = endpoints[mod] || endpoints.terminology;
    try {
        const res = await fetch(cfg.url);
        const data = await res.json();
        if (typeof WardExport !== 'undefined') {
            WardExport.downloadText(cfg.file, data.content, 'text/markdown;charset=utf-8');
        } else {
            const blob = new Blob([data.content], { type: 'text/markdown' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = cfg.file;
            a.click();
        }
        showToast('Flashcards exported.');
    } catch {
        showToast('Export failed. Is the server running?', 'error');
    }
}

// ── Keyboard Shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    const paletteOpen = !document.getElementById('command-palette')?.classList.contains('hidden');
    if (paletteOpen && ['ArrowDown', 'ArrowUp', 'Enter'].includes(e.key)) return;

    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openCommandPalette();
    }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        openSocraticMode();
    }
    if (e.key === 'Escape') {
        closeCommandPalette();
        closeSourceModal();
        closeSocraticModal();
        closeSidebar();
    }
});

['command-palette', 'source-modal', 'socratic-modal'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', (e) => {
        if (e.target.id === id) {
            e.target.classList.add('hidden');
        }
    });
});

// ── PWA Service Worker Registration ───────────────────────────────────────────

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
    });
}