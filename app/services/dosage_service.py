"""NURS 145 — Drug & Dosage Calculations service with SymPy derivations."""
from __future__ import annotations

import json
from typing import Any

from sympy import Rational, latex, symbols

from app.models import DosageCalculationRequest, DosageCalculationResult, SourceRef
from app.services.content_loader import load_content

MODULE_ID = "dosage"


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("dosage", {})
    return SourceRef(
        title=s.get("title", "Calculation of Drug Dosages"),
        url=s.get("url"),
        citation=s.get("citation", "Ogden & Fluharty, 11th Ed."),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_module_content() -> dict:
    return load_content("dosage.json")


def get_first_principles(calc_type: str) -> dict[str, Any]:
    """Return first-principles dimensional analysis guide for a calculation type."""
    data = get_module_content()
    principles = data.get("first_principles", {})
    if calc_type in ("basic",):
        calc_type = "liquid"
    elif calc_type in ("iv_drip",):
        calc_type = "iv_drip_gtt"
    return principles.get(calc_type, principles.get("liquid", {}))


def _rational(value: float) -> Rational:
    return Rational(str(value))


def _work_step(
    step: int,
    title: str,
    formula: str,
    reasoning: str,
    result: str = "",
) -> dict[str, str]:
    return {
        "step": str(step),
        "title": title,
        "formula": formula,
        "reasoning": reasoning,
        "result": result,
    }


def _derivation_fields(latex_expr: str, result: str | float) -> dict[str, str]:
    """Split SymPy LaTeX and numeric result for KaTeX rendering."""
    result_str = str(result)
    return {
        "derivation_latex": latex_expr,
        "derivation_result": result_str,
        "derivation": f"{latex_expr} = {result_str}",
    }


def _round_answer(value: float, unit: str) -> float:
    if "gtt" in unit:
        return round(value, 0)
    if "tablet" in unit or "capsule" in unit:
        return round(value, 2)
    if "mL/hr" in unit:
        return round(value, 1)
    return round(value, 2)


def _missing_result(
    message: str, clinical: str, warnings: list[str] | None = None
) -> DosageCalculationResult:
    return DosageCalculationResult(
        answer=0,
        unit="",
        steps=[message],
        work_steps=[],
        derivation="",
        clinical_note=clinical,
        safety_warnings=warnings or ["Complete all required fields before calculating."],
        nursing_considerations=[],
        pharmacology_note="",
        calc_label="Incomplete calculation",
        source=default_source(),
    )


def calculate_dosage(req: DosageCalculationRequest) -> DosageCalculationResult:
    """Run a step-by-step dosage calculation with optional detailed work."""
    source = default_source()
    show_work = req.show_work
    calc_type = req.calc_type

    # Map legacy "basic" and "iv_drip" to new types
    if calc_type == "basic":
        calc_type = "liquid"
    elif calc_type == "iv_drip":
        calc_type = "iv_drip_gtt"

    handlers = {
        "tablet_capsule": _calc_tablet_capsule,
        "liquid": _calc_liquid,
        "iv_drip_gtt": _calc_iv_drip_gtt,
        "iv_drip_ml_hr": _calc_iv_drip_ml_hr,
        "weight_based": _calc_weight_based,
        "pediatric": _calc_pediatric,
        "geriatric": _calc_geriatric,
    }

    handler = handlers.get(calc_type)
    if not handler:
        return _missing_result(
            "Unknown calculation type.",
            "Select a valid calculation type from the list.",
        )

    return handler(req, source, show_work)


def _calc_tablet_capsule(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not all([req.ordered_dose, req.available_dose]):
        return _missing_result(
            "Missing required values.",
            "Enter both the ordered dose and available dose per tablet/capsule.",
        )

    desired = req.ordered_dose
    have = req.available_dose
    ratio = _rational(desired) / _rational(have)
    answer = float(ratio)
    unit = "tablet(s)" if answer != 1 else "tablet"

    steps = [
        f"1. Ordered dose: {desired}",
        f"2. Available per tablet/capsule: {have}",
        f"3. Formula: Ordered ÷ Available = {desired} ÷ {have}",
        f"4. Result: {answer:g} {unit}",
        "5. Verify: Is the dose within therapeutic range? Can tablets be split safely?",
    ]

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Identify what is ordered (Desired)",
                f"D = {desired}",
                "Read the physician/provider order carefully. Confirm the dose, route, and frequency.",
                f"Desired = {desired}",
            ),
            _work_step(
                2,
                "Identify what you have (Available)",
                f"H = {have} per tablet/capsule",
                "Check the medication label — concentration on the bottle or blister pack.",
                f"Have = {have}",
            ),
            _work_step(
                3,
                "Set up dimensional analysis",
                f"\\frac{{{desired}}}{{{have}}} = \\text{{tablets}}",
                "Same units must cancel. You want tablets, so divide ordered dose by dose per unit.",
                f"{answer:g} tablet(s)",
            ),
            _work_step(
                4,
                "Clinical sense check",
                "Answer should be ≤ reasonable daily amount",
                "Half tablets (0.5) are common. Whole numbers >10 tablets warrant re-checking the order.",
                f"Administer {answer:g} tablet(s)",
            ),
        ]

    deriv = _derivation_fields(latex(ratio), f"{answer:g}")

    warnings = []
    if answer > 3:
        warnings.append("Large number of tablets — verify order and available strength.")
    if 0 < answer < 1 and answer not in (0.25, 0.5, 0.75):
        warnings.append("Unusual fraction — confirm tablet can be split accurately.")

    return DosageCalculationResult(
        answer=_round_answer(answer, unit),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        **deriv,
        clinical_note=(
            f"Administer {answer:g} tablet(s) to deliver {desired}. "
            "Use a pill splitter for partial tablets. Right patient, right drug, right dose, right route, right time."
        ),
        safety_warnings=warnings or [
            "High-alert medications require independent double-check.",
            "Never crush enteric-coated or sustained-release tablets unless ordered.",
        ],
        nursing_considerations=[
            "Document partial doses clearly (e.g., '½ tablet').",
            "Assess swallowing ability — offer liquid alternative if needed.",
            "Teach patient what the medication looks like to prevent errors.",
        ],
        pharmacology_note=(
            "Confirm dose falls within therapeutic range and does not exceed maximum daily dose."
        ),
        calc_label=f"Tablet/Capsule: {desired} ordered, {have} available",
        source=source,
    )


def _calc_liquid(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not all([req.ordered_dose, req.available_dose, req.available_volume]):
        return _missing_result(
            "Missing required values.",
            "Enter ordered dose, available dose, and available volume.",
        )

    desired, have, vol = req.ordered_dose, req.available_dose, req.available_volume
    ratio = _rational(desired) / _rational(have) * _rational(vol)
    answer = float(ratio)
    unit = "mL"

    steps = [
        f"1. Ordered dose: {desired}",
        f"2. Available: {have} in {vol} mL",
        f"3. Formula: (Ordered ÷ Available) × Volume",
        f"4. ({desired} ÷ {have}) × {vol} mL = {answer:.2f} mL",
        "5. Measure with an oral syringe — never use household spoons.",
    ]

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Desired dose (from order)",
                f"D = {desired}",
                "Convert all units to the same system before calculating (mg, mcg, units).",
                f"{desired}",
            ),
            _work_step(
                2,
                "Available concentration",
                f"H = {have} \\text{{ in }} {vol}\\,\\text{{mL}}",
                "The label tells you how much drug is in a given volume — this is your 'have'.",
                f"{have}/{vol} mL",
            ),
            _work_step(
                3,
                "Dimensional analysis",
                f"\\frac{{{desired}}}{{{have}}} \\times {vol}\\,\\text{{mL}}",
                "Units cancel to leave mL — the volume you will draw up.",
                f"{answer:.4f} mL",
            ),
            _work_step(
                4,
                "Safety check",
                "Small volumes (<1 mL) need calibrated syringes",
                "Oral syringes are more accurate than cup markings for pediatric and geriatric patients.",
                f"Draw {answer:.2f} mL",
            ),
        ]

    derivation = latex(_rational(desired) / _rational(have) * _rational(vol))

    warnings = []
    if answer < 0.5:
        warnings.append("Volume < 0.5 mL — use an insulin/oral syringe for accuracy.")
    if answer > 30:
        warnings.append("Large oral volume — assess patient tolerance and consider alternative formulation.")

    return DosageCalculationResult(
        answer=_round_answer(answer, unit),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        **_derivation_fields(derivation, f"{answer:.4f}"),
        clinical_note=f"Administer {answer:.2f} mL orally to deliver {desired}. Shake suspension before measuring.",
        safety_warnings=warnings or ["Double-check unit conversions (mg vs mcg vs g)."],
        nursing_considerations=[
            "Label syringe with medication name if not administering immediately.",
            "Stay with patient to ensure full dose is swallowed.",
            "Controlled substances require witness and waste documentation.",
        ],
        pharmacology_note="Verify therapeutic range — subtherapeutic doses are ineffective; toxic doses cause harm.",
        calc_label=f"Liquid: {desired} ordered, {have}/{vol} mL",
        source=source,
    )


def _calc_iv_drip_gtt(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not all([req.volume_to_infuse_ml, req.time_minutes, req.drop_factor]):
        return _missing_result(
            "Missing required values.",
            "Enter volume to infuse, time in minutes, and drop factor.",
        )

    vol, time_min, df = req.volume_to_infuse_ml, req.time_minutes, req.drop_factor
    rate = _rational(vol) * _rational(df) / _rational(time_min)
    answer = float(rate)
    unit = "gtt/min"

    steps = [
        f"1. Volume to infuse: {vol} mL",
        f"2. Time: {time_min} minutes ({time_min / 60:.2f} hours)",
        f"3. Drop factor: {df} gtt/mL",
        f"4. Formula: (Volume × Drop Factor) ÷ Time (min)",
        f"5. ({vol} × {df}) ÷ {time_min} = {answer:.1f} gtt/min",
        "6. Count drops for 1 full minute; adjust roller clamp.",
    ]

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Identify volume and time",
                f"V = {vol}\\,\\text{{mL}}, \\quad T = {time_min}\\,\\text{{min}}",
                "Convert hours to minutes if needed (× 60). IV bags list total volume.",
                f"{vol} mL over {time_min} min",
            ),
            _work_step(
                2,
                "Drop factor from tubing",
                f"DF = {df}\\,\\text{{gtt/mL}}",
                "Macrodrip: 10, 15, or 20 gtt/mL. Microdrip: 60 gtt/mL (always 60).",
                f"{df} gtt/mL",
            ),
            _work_step(
                3,
                "Calculate drip rate",
                f"\\frac{{{vol} \\times {df}}}{{{time_min}}}",
                "Multiply volume by drop factor to get total drops, then divide by minutes.",
                f"{answer:.2f} gtt/min → {round(answer)} gtt/min",
            ),
            _work_step(
                4,
                "Verify at bedside",
                "Count drops × 1 minute",
                "Gravity drips vary with catheter height and patient movement — recheck frequently.",
                f"Set to ~{round(answer)} gtt/min",
            ),
        ]

    derivation = (
        r"\frac{" + latex(_rational(vol) * _rational(df)) + r"}{" + latex(_rational(time_min)) + r"}"
    )

    return DosageCalculationResult(
        answer=_round_answer(answer, unit),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        **_derivation_fields(derivation, f"{answer:.2f}"),
        clinical_note=(
            f"Set manual IV rate to approximately {round(answer)} gtt/min. "
            "Document start time, rate, and tubing drop factor."
        ),
        safety_warnings=[
            "Never rely on memory for drop factor — read the package.",
            "IV pumps are preferred when available; gravity drips need frequent reassessment.",
        ],
        nursing_considerations=[
            "Assess IV site for infiltration and phlebitis during infusion.",
            "Use roller clamp — not fingers — to adjust rate.",
            "For blood products, follow agency policy for filter and rate limits.",
        ],
        pharmacology_note="Fluid overload risk increases with rapid infusion — monitor lung sounds and I&O.",
        calc_label=f"IV gtt/min: {vol} mL over {time_min} min, DF {df}",
        source=source,
    )


def _calc_iv_drip_ml_hr(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not all([req.volume_to_infuse_ml, req.time_minutes]):
        return _missing_result(
            "Missing required values.",
            "Enter volume to infuse and time.",
        )

    vol = req.volume_to_infuse_ml
    time_hr = req.time_minutes / 60.0
    if time_hr <= 0:
        return _missing_result("Invalid time.", "Time must be greater than zero.")

    rate = _rational(vol) / _rational(str(time_hr))
    answer = float(rate)
    unit = "mL/hr"

    steps = [
        f"1. Volume to infuse: {vol} mL",
        f"2. Time: {req.time_minutes} min = {time_hr:.2f} hours",
        f"3. Formula: Volume ÷ Time (hours) = mL/hr",
        f"4. {vol} ÷ {time_hr:.2f} = {answer:.1f} mL/hr",
        "5. Program pump or calculate gravity equivalent.",
    ]

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Convert time to hours",
                f"T = {req.time_minutes} \\div 60 = {time_hr:.4f}\\,\\text{{hr}}",
                "Pump rates use mL/hr — always convert minutes to hours first.",
                f"{time_hr:.2f} hours",
            ),
            _work_step(
                2,
                "Apply formula",
                f"\\frac{{{vol}\\,\\text{{mL}}}}{{{time_hr:.4f}\\,\\text{{hr}}}}",
                "Volume divided by hours gives the hourly infusion rate.",
                f"{answer:.2f} mL/hr",
            ),
            _work_step(
                3,
                "Pump programming",
                f"Rate = {answer:.1f} mL/hr",
                "Enter VTBI (volume to be infused) and duration, or rate directly per pump model.",
                f"{round(answer, 1)} mL/hr",
            ),
        ]

    derivation = latex(_rational(vol) / _rational(str(time_hr)))

    return DosageCalculationResult(
        answer=_round_answer(answer, unit),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        **_derivation_fields(derivation, f"{answer:.2f}"),
        clinical_note=f"Program IV pump at {answer:.1f} mL/hr for {vol} mL over {time_hr:.2f} hours.",
        safety_warnings=[
            "Confirm pump settings with another nurse for high-alert infusions.",
            "Alarms must remain enabled — never silence without assessing.",
        ],
        nursing_considerations=[
            "Document pump settings in the MAR/eMAR.",
            "Assess patency before starting infusion.",
        ],
        pharmacology_note="Electrolyte solutions (KCl) have maximum infusion rates — check order limits.",
        calc_label=f"IV mL/hr: {vol} mL over {req.time_minutes} min",
        source=source,
    )


def _calc_weight_based(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not all([req.patient_weight_kg, req.dose_per_kg]):
        return _missing_result(
            "Missing required values.",
            "Enter patient weight (kg) and ordered dose per kg.",
        )

    weight, dpk = req.patient_weight_kg, req.dose_per_kg
    total = _rational(weight) * _rational(dpk)
    answer = float(total)
    unit = "mg"

    if req.doses_per_day and req.doses_per_day > 1:
        per_dose = answer / req.doses_per_day
        steps = [
            f"1. Patient weight: {weight} kg",
            f"2. Dose: {dpk} mg/kg",
            f"3. Daily total: {weight} × {dpk} = {answer:g} mg/day",
            f"4. Divided into {req.doses_per_day} doses: {answer:g} ÷ {req.doses_per_day} = {per_dose:g} mg/dose",
            "5. Compare to maximum safe dose in drug reference.",
        ]
        final_answer = per_dose
        unit = "mg per dose"
        calc_label = f"Weight-based: {weight} kg × {dpk} mg/kg ÷ {req.doses_per_day} doses"
        clinical = (
            f"Total daily dose = {answer:g} mg. Each dose = {per_dose:g} mg. "
            "Verify weight is current and dose is within therapeutic range."
        )
    else:
        steps = [
            f"1. Patient weight: {weight} kg",
            f"2. Ordered: {dpk} mg/kg",
            f"3. {weight} kg × {dpk} mg/kg = {answer:g} mg",
            "4. Check against maximum single dose and daily maximum.",
            "5. Recalculate if weight changes significantly.",
        ]
        final_answer = answer
        calc_label = f"Weight-based: {weight} kg × {dpk} mg/kg"
        clinical = f"Calculated dose = {answer:g} mg. Confirm against drug reference maximums."

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Confirm weight in kilograms",
                f"W = {weight}\\,\\text{{kg}}",
                "Pediatric and many adult meds use kg. Convert lbs: kg = lbs ÷ 2.2.",
                f"{weight} kg",
            ),
            _work_step(
                2,
                "Apply weight-based order",
                f"D = W \\times {dpk}\\,\\text{{mg/kg}}",
                "Multiply weight by ordered mg/kg to get total milligrams.",
                f"{answer:g} mg",
            ),
        ]
        if req.doses_per_day and req.doses_per_day > 1:
            work_steps.append(
                _work_step(
                    3,
                    "Divide for per-dose amount",
                    f"\\frac{{{answer:g}}}{{{req.doses_per_day}}}",
                    "Daily dose divided by number of administrations per 24 hours.",
                    f"{final_answer:g} mg per dose",
                )
            )

    derivation = latex(_rational(weight) * _rational(dpk))

    return DosageCalculationResult(
        answer=_round_answer(final_answer, unit),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        **_derivation_fields(derivation, f"{answer:g}"),
        clinical_note=clinical,
        safety_warnings=[
            "Estimated weight (e.g., 'broselow tape') is less accurate — weigh when possible.",
            "Never exceed published maximum dose even if calculation suggests it.",
        ],
        nursing_considerations=[
            "Document actual weight used in calculation.",
            "Renal/hepatic impairment may require dose adjustment beyond this formula.",
        ],
        pharmacology_note="Therapeutic index narrows with weight-based drugs — monitor levels when applicable.",
        calc_label=calc_label,
        source=source,
    )


def _calc_pediatric(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    result = _calc_weight_based(req, source, show_work)
    result.safety_warnings = [
        "Pediatric dosing requires current weight — do not use adult doses.",
        "Children are not small adults — pharmacokinetics differ by age.",
        *result.safety_warnings,
    ]
    result.nursing_considerations = [
        "Use family-centered teaching appropriate to developmental age.",
        "Liquid formulations preferred when tablet splitting is impractical.",
        "Verify with pharmacist for neonates and infants.",
        *result.nursing_considerations,
    ]
    result.pharmacology_note = (
        "Check pediatric-specific references (Harriet Lane, Lexicomp). "
        "Off-label use is common — follow evidence and provider order."
    )
    if result.calc_label:
        result.calc_label = "Pediatric: " + result.calc_label.replace("Weight-based: ", "")
    return result


def _calc_geriatric(
    req: DosageCalculationRequest, source: SourceRef, show_work: bool
) -> DosageCalculationResult:
    if not req.ordered_dose:
        return _missing_result(
            "Missing ordered dose.",
            "Enter the standard adult dose to adjust.",
        )

    adult_dose = req.ordered_dose
    factor = req.geriatric_factor if req.geriatric_factor in (0.5, 0.75) else 0.75
    adjusted = float(_rational(adult_dose) * _rational(str(factor)))
    pct = int(factor * 100)
    unit = f"mg ({pct}% adjusted)"

    steps = [
        f"1. Standard adult dose: {adult_dose} mg",
        "2. Geriatric principle: 'Start low, go slow'",
        f"3. Adjustment factor: {factor} ({pct}% of adult dose)",
        f"4. {adult_dose} × {factor} = {adjusted:.1f} mg",
        "5. Titrate based on response, renal/hepatic function, and Beers Criteria.",
    ]

    work_steps: list[dict[str, str]] = []
    if show_work:
        work_steps = [
            _work_step(
                1,
                "Identify standard adult dose",
                f"D_{{adult}} = {adult_dose}",
                "This is the 'usual' dose for a healthy adult — not always safe for older adults.",
                f"{adult_dose} mg",
            ),
            _work_step(
                2,
                "Apply geriatric reduction",
                f"D_{{geriatric}} = {adult_dose} \\times {factor}",
                "Older adults have ↓ lean mass, ↓ renal clearance, ↑ sensitivity. Start at 50–75%.",
                f"{adjusted:.1f} mg",
            ),
            _work_step(
                3,
                "Monitor and titrate",
                "Assess for adverse effects",
                "Polypharmacy increases interaction risk. Review Beers Criteria for potentially inappropriate meds.",
                f"Starting dose ≈ {adjusted:.1f} mg",
            ),
        ]

    derivation_latex = f"D_{{\\text{{geriatric}}}} = {adult_dose} \\times {factor}"
    derivation_result = f"{adjusted:.1f}"

    return DosageCalculationResult(
        answer=round(adjusted, 1),
        unit=unit,
        steps=steps,
        work_steps=work_steps,
        derivation=f"{derivation_latex} = {derivation_result}",
        derivation_latex=derivation_latex,
        derivation_result=derivation_result,
        clinical_note=(
            f"Consider starting at {adjusted:.1f} mg ({pct}% of adult dose). "
            "Titrate slowly. Monitor for orthostatic hypotension, sedation, and falls."
        ),
        safety_warnings=[
            "Beers Criteria: review for potentially inappropriate medications in older adults.",
            "Renal function (eGFR/CrCl) may require further dose reduction.",
        ],
        nursing_considerations=[
            "Assess cognition — simplified regimens improve adherence.",
            "Fall risk increases with sedating medications.",
            "Involve caregiver in medication teaching.",
        ],
        pharmacology_note="Altered absorption, distribution, metabolism, and excretion (ADME) change drug response.",
        calc_label=f"Geriatric: {adult_dose} mg × {factor}",
        source=source,
    )


def get_pharmacology_safety() -> list[dict[str, Any]]:
    return get_module_content().get("pharmacology_safety", [])


def get_drug_classes() -> list[dict[str, Any]]:
    return get_module_content().get("drug_classes", [])


def get_pharm_categories() -> list[dict[str, Any]]:
    return get_module_content().get("pharm_categories", [])


def get_drug_class(class_id: str) -> dict[str, Any] | None:
    return next((dc for dc in get_drug_classes() if dc.get("id") == class_id), None)


def get_practice_problems() -> list[dict[str, Any]]:
    data = get_module_content()
    return data.get("practice_problems", [])


def check_practice_answer(problem_id: str, selected_index: int) -> dict[str, Any]:
    problems = get_practice_problems()
    problem = next((p for p in problems if p.get("id") == problem_id), None)
    if not problem:
        return {"correct": False, "message": "Problem not found."}

    correct = selected_index == problem.get("correct_index", -1)
    return {
        "correct": correct,
        "correct_index": problem.get("correct_index"),
        "explanation": problem.get("explanation", ""),
        "answer": problem.get("answer", ""),
        "trap": problem.get("trap", ""),
        "nursing_note": problem.get("nursing_note", ""),
        "work_steps": problem.get("work_steps", []),
    }


def serialize_calc_inputs(req: DosageCalculationRequest) -> str:
    return json.dumps(req.model_dump(exclude_none=True))


def serialize_calc_result(result: DosageCalculationResult) -> str:
    return result.model_dump_json()