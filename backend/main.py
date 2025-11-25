from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

# -----------------------------
# 1. CLINICAL LOGIC (Pure Python)
# -----------------------------

def calculate_bleeding_risk(age, inr, anticoagulant, gi_bleed, high_bp, antiplatelet_use, gender, weight, smoking, alcohol_use, antibiotic_order, dietary_change, liver_disease, prior_stroke):
    score = 0
    score += 35 if anticoagulant else 0
    score += 40 if inr > 3.5 else 0
    score += 30 if gi_bleed else 0
    score += 15 if antiplatelet_use else 0
    score += 25 if antibiotic_order else 0 
    score += 15 if alcohol_use else 0     
    score += 20 if liver_disease else 0   
    score += 10 if dietary_change else 0  
    score += 10 if age > 70 else 0
    score += 10 if high_bp else 0
    score += 10 if smoking else 0
    score += 5 if gender == 'Female' else 0
    score += 15 if weight > 120 or weight < 50 else 0
    score += 15 if prior_stroke else 0 
    return min(score, 100)

def calculate_hypoglycemic_risk(insulin_use, renal_status, high_hba1c, neuropathy_history, gender, weight, recent_dka):
    score = 0
    score += 30 if insulin_use else 0
    score += 45 if renal_status else 0
    score += 20 if high_hba1c else 0
    score += 10 if neuropathy_history else 0
    score += 10 if weight < 60 else 0
    score += 20 if recent_dka else 0 
    return min(score, 100)

def calculate_aki_risk(age, diuretic_use, acei_arb_use, high_bp, active_chemo, gender, weight, race, baseline_creat, contrast_exposure):
    score = 0
    score += 30 if diuretic_use else 0
    score += 40 if acei_arb_use else 0
    score += 25 if contrast_exposure else 0 
    score += 20 if age > 75 else 0
    score += 10 if high_bp else 0
    score += 20 if active_chemo else 0
    score += 15 if race == 'Non-Hispanic Black' else 0
    score += 30 if baseline_creat > 1.5 else 0 
    return min(score, 100)

def calculate_comorbidity_load(prior_stroke, active_chemo, recent_dka, liver_disease, smoking, high_bp):
    load = 0
    load += 25 if prior_stroke else 0
    load += 30 if active_chemo else 0
    load += 20 if recent_dka else 0
    load += 15 if liver_disease else 0
    load += 10 if smoking else 0
    load += 10 if high_bp else 0
    return min(load, 100)

interaction_db = {
    ("warfarin", "amiodarone"): "Major: Amiodaride increases INR, high bleeding risk.",
    ("warfarin", "ibuprofen"): "Major: NSAIDs increase bleeding risk with Warfarin.",
    ("lisinopril", "spironolactone"): "Major: Risk of severe hyperkalemia.",
    ("ibuprofen", "lisinopril"): "Major: Severe AKI risk (Triple Whammy).",
}

# -----------------------------
# 2. DATA MODELS (Pydantic)
# -----------------------------

class PatientInput(BaseModel):
    age: int = Field(..., ge=18, le=100)
    gender: str
    weight: float
    race: str = 'Other'
    inr: float = 1.0
    baseline_creat: float = 0.9
    antibiotic_order: bool = False
    dietary_change: bool = False
    contrast_exposure: bool = False
    on_anticoag: bool = False
    on_antiplatelet: bool = False
    on_insulin: bool = False
    on_diuretic: bool = False
    on_acei_arb: bool = False
    prior_stroke: bool = False
    hist_gi_bleed: bool = False
    uncontrolled_bp: bool = False
    smoking_calc: bool = False
    alcohol_use: bool = False
    liver_disease: bool = False
    high_hba1c: bool = False
    neuropathy_history: bool = False
    impaired_renal: bool = False
    recent_dka: bool = False
    active_chemo: bool = False

class InteractionInput(BaseModel):
    drug1: str
    drug2: str

# -----------------------------
# 3. API APP DEFINITION
# -----------------------------
app = FastAPI(title="ADE Risk Engine")

@app.post("/calculate")
def calculate_risks(p: PatientInput):
    b_risk = calculate_bleeding_risk(p.age, p.inr, p.on_anticoag, p.hist_gi_bleed, p.uncontrolled_bp, p.on_antiplatelet, p.gender, p.weight, p.smoking_calc, p.alcohol_use, p.antibiotic_order, p.dietary_change, p.liver_disease, p.prior_stroke)
    h_risk = calculate_hypoglycemic_risk(p.on_insulin, p.impaired_renal, p.high_hba1c, p.neuropathy_history, p.gender, p.weight, p.recent_dka)
    a_risk = calculate_aki_risk(p.age, p.on_diuretic, p.on_acei_arb, p.uncontrolled_bp, p.active_chemo, p.gender, p.weight, p.race, p.baseline_creat, p.contrast_exposure)
    fragility = calculate_comorbidity_load(p.prior_stroke, p.active_chemo, p.recent_dka, p.liver_disease, p.smoking_calc, p.uncontrolled_bp)
    
    # Determine max risk
    risks = {"Bleeding": b_risk, "Hypoglycemia": h_risk, "AKI": a_risk}
    max_type = max(risks, key=risks.get)
    max_score = risks[max_type]

    return {
        "bleeding_risk": b_risk,
        "hypoglycemic_risk": h_risk,
        "aki_risk": a_risk,
        "fragility_index": fragility,
        "primary_alert": max_type,
        "primary_score": max_score
    }

@app.post("/interaction")
def check_interaction(i: InteractionInput):
    d1, d2 = i.drug1.lower().strip(), i.drug2.lower().strip()
    result = interaction_db.get((d1, d2)) or interaction_db.get((d2, d1)) or "No major interaction found."
    return {"result": result}