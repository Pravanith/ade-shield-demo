import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

# -----------------------------
# 1. SETUP & PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Clinical Risk Monitor", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# 2. XGBOOST BACKEND ENGINE
# -----------------------------
# We use st.cache_resource so the model only trains ONCE when the app starts, not every reload.
@st.cache_resource
def train_bleeding_model():
    """
    Generates synthetic clinical data and trains an XGBoost Regressor 
    to predict bleeding risk scores.
    """
    # A. Generate Synthetic Data (1,000 fake patients)
    np.random.seed(42)
    n_samples = 1000
    
    data = pd.DataFrame({
        'age': np.random.randint(18, 95, n_samples),
        'inr': np.random.uniform(0.8, 6.0, n_samples),
        'anticoagulant': np.random.randint(0, 2, n_samples),
        'gi_bleed': np.random.randint(0, 2, n_samples),
        'high_bp': np.random.randint(0, 2, n_samples),
        'antiplatelet': np.random.randint(0, 2, n_samples),
        'gender_female': np.random.randint(0, 2, n_samples), # 1=Female, 0=Male
        'weight': np.random.normal(75, 15, n_samples),
        'liver_disease': np.random.randint(0, 2, n_samples),
    })

    # B. Define "Ground Truth" Logic (The model needs something to learn from)
    # This mimics your original manual function to teach the AI your medical rules.
    def mimic_clinical_rules(row):
        score = 0
        score += 35 if row['anticoagulant'] else 0
        score += 40 if row['inr'] > 3.5 else 0
        score += 30 if row['gi_bleed'] else 0
        score += 15 if row['antiplatelet'] else 0
        score += 20 if row['liver_disease'] else 0
        score += 10 if row['age'] > 70 else 0
        score += 10 if row['high_bp'] else 0
        score += 5 if row['gender_female'] else 0
        return min(score, 100) # Cap at 100

    data['risk_score'] = data.apply(mimic_clinical_rules, axis=1)

    # C. Train XGBoost Model
    X = data.drop('risk_score', axis=1)
    y = data['risk_score']
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3
    )
    model.fit(X, y)
    
    return model

# Load the model immediately
bleeding_model = train_bleeding_model()

# -----------------------------
# 3. EXISTING FUNCTIONS & LOGIC
# -----------------------------

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

def generate_detailed_alert(risk_type, inputs):
    if risk_type == "Bleeding":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **Bleeding Risk**. Primary factors:"
        factors = []
        if inputs['inr'] > 3.5: factors.append(f"High INR ({inputs['inr']})")
        if inputs['antibiotic_order']: factors.append("New Antibiotic Order (Metabolic Interference)")
        if inputs['on_antiplatelet']: factors.append("Dual Antiplatelet/Anticoagulant Therapy")
        if inputs['alcohol_use']: factors.append("Heavy Alcohol Use")
        if inputs['hist_gi_bleed']: factors.append("History of GI Bleed")
        if inputs['prior_stroke']: factors.append("History of Stroke/TIA (Complex Management)")
        
    elif risk_type == "Hypoglycemic":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **Hypoglycemic Risk**. Primary factors:"
        factors = []
        if inputs['impaired_renal']: factors.append("Impaired Renal Status (Reduced Drug Clearance)")
        if inputs['high_hba1c']: factors.append("Poor DM Control (HbA1c > 9.0%)")
        if inputs['recent_dka']: factors.append("Recent DKA/HHS Admission (Metabolic Volatility)")
        if inputs['weight'] < 60: factors.append(f"Low Body Weight ({inputs['weight']} kg)")

    elif risk_type == "AKI":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **AKI Risk (Renal)**. Primary factors:"
        factors = []
        if inputs['baseline_creat'] > 1.5: factors.append(f"Baseline CKD (Creatinine > 1.5)")
        if inputs['active_chemo']: factors.append("Active Chemotherapy (Nephrotoxic Agent)")
        if inputs['contrast_exposure']: factors.append("Recent Contrast Dye Exposure")
        if inputs['on_acei_arb'] and inputs['on_diuretic']: factors.append("Combined ACEi/Diuretic Therapy")

    else: 
        return "HIGH RISK ALERT: Check specific patient risks."
        
    if factors:
        return base_message + " " + ", ".join(factors) + "."
    else:
        return base_message + " High risk due to combination of demographic factors."

def chatbot_response(text):
    text = text.lower()
    responses = {
        "ibuprofen": "Ibuprofen (NSAID) poses a high risk of bleeding with anticoagulants and AKI when combined with blood pressure drugs.",
        "lisinopril": "Lisinopril (an ACE inhibitor) can cause severe hyperkalemia (high potassium) when combined with certain diuretics.",
        "statin": "Statins are critical for cardiovascular risk reduction but require monitoring for muscle pain (myopathy) and liver toxicity.",
        "beta-blocker": "Beta-blockers treat hypertension and heart conditions but can severely mask the warning signs of hypoglycemia.",
        "calcium channel blocker": "Calcium channel blockers (CCBs) lower blood pressure but carry a high risk of interaction when combined with strong antibiotics.",
        "potassium": "Potassium levels must be monitored closely when using ACE inhibitors or diuretics to prevent dangerous hyperkalemia.",
        "creatinine": "Creatinine is a key indicator of kidney function. A high level often requires immediate drug dose reduction.",
        "liver": "Liver function is essential for drug metabolism; poor liver status can increase the risk of drug toxicity and bleeding.",
        "falls": "Medications that affect the central nervous system (CNS) increase the risk of falls, a primary cause of bleeding events in the elderly.",
        "triple whammy": "The 'Triple Whammy' refers to the dangerous combination of an ACE inhibitor, a Diuretic, and an NSAID, which severely increases AKI risk.",
        "warfarin": "Warfarin interacts with several medications and increases bleeding risk.",
        "amiodarone": "Amiodarone can elevate INR when combined with Warfarin.",
        "aki": "Acute Kidney Injury risk is elevated by certain blood pressure medications (ACEi/ARBs) and diuretics.",
        "metformin": "Metformin is a first-line diabetes drug but is strictly avoided in severe kidney impairment.",
        "diabetes": "Diabetes requires strict blood sugar monitoring; poor control (high HbA1c) increases hypoglycemia risk.",
        "hypertension": "Uncontrolled hypertension increases cardiovascular risk and stresses kidney function.",
        "cancer": "Active chemotherapy treatment increases the risk of AKI and immune suppression.",
    }
    for key in responses:
        if key in text:
            return responses[key]
    
    return "I need more specific clinical context. Please refine your query using drug classifications, risk factors, or one of the major ADE categories (Bleeding, Hypoglycemia, AKI)."

interaction_db = {
    ("warfarin", "amiodarone"): "Major: Amiodaride increases INR, high bleeding risk.",
    ("warfarin", "ibuprofen"): "Major: NSAIDs increase bleeding risk with Warfarin.",
    ("apixaban", "ibuprofen"): "Moderate: NSAIDs increase bleeding risk with Apixaban.",
    ("clopidogrel", "aspirin"): "Moderate: Dual antiplatelet therapy, increases bleed risk.",
    ("rivaroxaban", "fluconazole"): "Major: Fluconazole increases Rivaroxaban levels (CYP3A4 inhibitor); high bleeding risk.",
    ("warfarin", "paracetamol"): "Major: Paracetamol increases Warfarin's effect; high bleeding risk.",
    ("sertraline", "warfarin"): "Moderate: SSRI (Sertraline) combined with Warfarin increases baseline bleeding risk.",
    ("lisinopril", "spironolactone"): "Major: Risk of severe hyperkalemia (high potassium).",
    ("ibuprofen", "lisinopril"): "Major: Severe AKI risk (Triple Whammy component).",
    ("furosemide", "lisinopril"): "Major: Diuretic + ACEi causes severe hypotension and AKI risk.",
    ("prednisone", "furosemide"): "Major: Steroid + Diuretic increases risk of severe hypokalemia (low potassium).", 
    ("lithium", "hydrochlorothiazide"): "Major: Diuretic (HCTZ) increases Lithium toxicity risk by slowing excretion.", 
    ("allopurinol", "azathioprine"): "Major: Allopurinol dramatically increases Azathioprine toxicity and risk of severe bone marrow suppression.", 
    ("glipizide", "alcohol"): "Major: Increased risk of severe hypoglycemia.",
    ("metformin", "cimetidine"): "Moderate: Cimetidine increases Metformin levels, raising hypoglycemia risk.",
    ("trimethoprim/sulfamethoxazole", "metformin"): "Major: TMP/SMX increases Metformin levels, high hypoglycemia risk.",
    ("metoprolol", "insulin"): "Moderate: Beta-blocker (Metoprolol) can mask the warning signs of hypoglycemia.", 
    ("sertraline", "sumatriptan"): "Major: Both increase serotonin levels; high risk of Serotonin Syndrome.", 
    ("azithromycin", "amiodarone"): "Major: Both prolong QT interval; high risk of fatal arrhythmia.", 
    ("metoprolol", "diltiazem"): "Major: Both slow heart rate; high risk of severe bradycardia and hypotension.", 
}

def check_interaction(drug1, drug2):
    d1, d2 = drug1.lower().strip(), drug2.lower().strip()
    if (d1, d2) in interaction_db:
        return interaction_db[(d1, d2)]
    if (d2, d1) in interaction_db:
        return interaction_db[(d2, d1)]
    return "No major interaction found."

# -----------------------------
# 4. UI INTEGRATION & SESSION
# -----------------------------

if 'entered_app' not in st.session_state:
    st.session_state['entered_app'] = False
if 'patient_loaded' not in st.session_state:
    st.session_state['patient_loaded'] = False
    st.session_state['bleeding_risk'] = 0
    st.session_state['hypoglycemic_risk'] = 0
    st.session_state['aki_risk'] = 0
    st.session_state['fragility_index'] = 0
    st.session_state['patient_info'] = {'age': 70, 'gender': 'Male', 'weight': 75} 

# --- COVER PAGE ---
if not st.session_state['entered_app']:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="text-align: center; font-size: 100px;">
                🛡️
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown(
            """
            <h1 style='text-align: center; color: #2e4053;'>Clinical Risk Monitor</h1>
            <h3 style='text-align: center; color: #566573;'>AI-Driven Pharmacovigilance & Triage System</h3>
            <hr>
            <p style='text-align: center; font-size: 18px; color: #566573;'>
                A predictive analytics tool for preventing Adverse Drug Events (ADEs) 
                including Bleeding, Hypoglycemia, and Acute Kidney Injury.
            </p>
            """, 
            unsafe_allow_html=True
        )
        
        st.write("") # Spacer
        st.write("") # Spacer
        
        def enter_app():
            st.session_state['entered_app'] = True

        st.button(
            "🚀 Launch Dashboard", 
            on_click=enter_app,
            use_container_width=True,
            type="primary"
        )
        
        st.markdown(
            "<p style='text-align: center; margin-top: 20px; color: #abb2b9; font-size: 12px;'>Built with Python • Streamlit • XGBoost Logic</p>", 
            unsafe_allow_html=True
        )

# --- MAIN APPLICATION ---
else:
    # Sidebar
    with st.sidebar:
        st.title("Risk Monitor Menu")
        menu = st.radio(
            "Select View", 
            ["Live Dashboard", "Risk Calculator", "CSV Upload", "Medication Checker", "Chatbot"],
            index=1
        )

    # -----------------------------
    # PAGE: LIVE DASHBOARD
    # -----------------------------
    if menu == "Live Dashboard":
        st.subheader("General Patient Risk Overview")
        
        if st.session_state['patient_loaded']:
            br = st.session_state['bleeding_risk']
            hr = st.session_state['hypoglycemic_risk']
            ar = st.session_state['aki_risk']
            cfr = st.session_state['fragility_index']
            patient = st.session_state['patient_info']
            max_risk = max(br, hr, ar)
            
            if br == max_risk: primary_threat = "Bleeding Risk"
            elif hr == max_risk: primary_threat = "Hypoglycemic Risk"
            else: primary_threat = "AKI Risk"
            
            alert_color = "red" if max_risk >= 70 else "green"
            alert_label = "CRITICAL" if max_risk >= 90 else ("HIGH" if max_risk >= 70 else "LOW")
        else:
            br, hr, ar, cfr = 60, 92, 80, 75
            patient = {'age': 65, 'gender': 'Female', 'weight': 55}
            primary_threat = "Hypoglycemic Risk"
            alert_label = "CRITICAL"
            max_risk = hr

        col_metrics = st.columns(4)
        col_metrics[0].metric("Bleeding Risk", f"{br:.1f}%", "MED" if br < 70 else "CRITICAL")
        col_metrics[1].metric("Hypoglycemic Risk", f"{hr}%", alert_label)
        col_metrics[2].metric("AKI Risk (Renal)", f"{ar}%", "HIGH" if ar >= 70 else "LOW")
        col_metrics[3].metric("Clinical Fragility Index", f"{cfr}%", "HIGH" if cfr >= 70 else "LOW")

        st.markdown("---")
        col_left, col_right = st.columns([3, 7])

        with col_left:
            st.subheader("⚠️ Patient Queue")
            st.markdown(f'<div style="background-color:#B30000; color:white; padding:10px; border-radius:5px;">'
                        f'**Current Session Patient**<br>'
                        f'🔴 **Risk: {max_risk:.1f}% ({alert_label})**<br>'
                        f'*Issue: {primary_threat}*</div>', 
                        unsafe_allow_html=True)
            st.markdown("---")
            st.info("The remaining queue shows historical alerts (hardcoded).")
            st.markdown(f'<div style="background-color:#FF8C00; color:black; padding:10px; border-radius:5px;">**Patient B** (Room 410)<br>🟠 **Risk: 80% (HIGH)**<br>*Issue: AKI Risk*</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background-color:#A8D08D; color:black; padding:10px; border-radius:5px;">**Patient C** (Room 105)<br>🟡 **Risk: 60% (MED)**<br>*Issue: Bleeding Risk*</div>', unsafe_allow_html=True)

        with col_right:
            st.subheader(f"Analysis: Patient Profile (Age {patient['age']}/{patient['gender']})")
            st.caption(f"Risk Focus: {primary_threat}")
            
            st.markdown("#### 📋 Patient Profile")
            profile_col1, profile_col2, profile_col3 = st.columns(3)
            profile_col1.markdown(f"**Age/Gender:** {patient['age']} / {patient['gender']}")
            profile_col1.markdown(f"**Weight:** {patient['weight']} kg")
            profile_col2.markdown(f"**Fragility Index:** {cfr}%")
            profile_col3.markdown(f"**Risk Focus:** {primary_threat}")
            st.markdown("---")
            metric_col1, metric_col2 = st.columns([2, 4])
            with metric_col1:
                st.metric(label=f"{primary_threat} Probability", value=f"{max_risk:.1f}%", delta=alert_label)
            with metric_col2:
                st.markdown(f"#### 🚨 Primary Threat: {primary_threat}")
                st.markdown("Prediction window: Next 24 Hours")
            st.markdown("---")
            st.info(f"**Note:** To see the Feature Importance Chart, calculate a patient's risk in the **Risk Calculator** menu.")
            st.subheader("Recommended Action")
            st.info("💡 Recommendation: Consult Pharmacy/Endocrinology for immediate dose review.")
            st.button("✅ Approve Intervention", type="primary")
            st.button("❌ Snooze Alert")

    # -----------------------------
    # PAGE: RISK CALCULATOR (XGBoost)
    # -----------------------------
    elif menu == "Risk Calculator":
        st.subheader("AI-Powered Risk Calculator (XGBoost)")
        st.caption("This module uses a trained XGBoost Regressor to predict bleeding risk based on 1,000 synthetic patient records.")

        # INPUTS
        col1, col2 = st.columns(2)
        age = col1.number_input("Age", 18, 100, 75)
        inr = col1.number_input("INR", 0.0, 10.0, 2.5)
        weight = col1.number_input("Weight", 40, 150, 70)
        gender = col1.selectbox("Gender", ["Male", "Female"])
        
        col2.markdown("#### Clinical Factors")
        anticoag = col2.checkbox("Anticoagulant Use")
        gi_bleed = col2.checkbox("History of GI Bleed")
        high_bp = col2.checkbox("Uncontrolled Hypertension")
        antiplatelet = col2.checkbox("Antiplatelet Use")
        liver_disease = col2.checkbox("Liver Disease")
        
        # Additional inputs needed for other non-ML calculators to prevent errors if we want to save state
        # We'll just hardcode default checks for the variables not used in XGBoost but used in other risk scores
        antibiotic_order = False
        alcohol_use = False
        prior_stroke = False
        
        # Other risk factors for display purposes (dummy inputs to fill session state)
        st.markdown("---")
        st.caption("Additional factors for AKI/Hypoglycemia models (Rule-Based):")
        sub_c1, sub_c2, sub_c3 = st.columns(3)
        active_chemo = sub_c1.checkbox("Active Chemo")
        on_diuretic = sub_c2.checkbox("Diuretic Use")
        on_acei_arb = sub_c3.checkbox("ACEi/ARB Use")

        if st.button("Run Prediction Model"):
            # 1. Format input for XGBoost (Must match training columns)
            input_data = pd.DataFrame({
                'age': [age],
                'inr': [inr],
                'anticoagulant': [1 if anticoag else 0],
                'gi_bleed': [1 if gi_bleed else 0],
                'high_bp': [1 if high_bp else 0],
                'antiplatelet': [1 if antiplatelet else 0],
                'gender_female': [1 if gender == "Female" else 0],
                'weight': [weight],
                'liver_disease': [1 if liver_disease else 0]
            })

            # 2. Get Prediction
            prediction = bleeding_model.predict(input_data)[0]
            
            # 3. Calculate other rule-based risks for context
            hypo_risk = calculate_hypoglycemic_risk(False, False, False, False, gender, weight, False) # Dummy values for demo
            aki_risk = calculate_aki_risk(age, on_diuretic, on_acei_arb, high_bp, active_chemo, gender, weight, "Other", 1.0, False)
            fragility = calculate_comorbidity_load(False, active_chemo, False, liver_disease, False, high_bp)

            # 3. Display Result
            st.divider()
            c1, c2 = st.columns([1, 2])
            c1.metric("Predicted Bleeding Risk (AI)", f"{prediction:.1f}%", "High" if prediction > 50 else "Low")
            c1.metric("AKI Risk (Rule-Based)", f"{aki_risk}%")
            
            # 4. Explainability (Feature Importance)
            c2.markdown("#### Model Explainability")
            c2.write("Why did the AI predict this score?")
            
            # Simple feature importance extraction
            importance = pd.DataFrame({
                'feature': input_data.columns,
                'weight': bleeding_model.feature_importances_
            }).sort_values(by='weight', ascending=False)
            
            st.bar_chart(importance.set_index('feature'))
            
            # 5. Load to Session
            if st.button("Load Patient to Dashboard"):
                st.session_state['patient_loaded'] = True
                st.session_state['bleeding_risk'] = float(prediction)
                st.session_state['hypoglycemic_risk'] = hypo_risk
                st.session_state['aki_risk'] = aki_risk
                st.session_state['fragility_index'] = fragility
                st.session_state['patient_info'] = {'age': age, 'gender': gender, 'weight': weight}
                st.toast("Patient data loaded! Switch to Live Dashboard.")

    # -----------------------------
    # PAGE: CSV UPLOAD
    # -----------------------------
    elif menu == "CSV Upload":
        st.subheader("Bulk Patient Risk Analysis")
        st.markdown("Upload patient demographics for acute risk calculation.")
        uploaded_csv = st.file_uploader("Upload Patient Demographics (CSV)", type=["csv"])
        st.markdown("#### 🖼️ Upload Medical Images")
        st.caption("Demonstrate capacity for integrating medical documentation or imaging.")
        uploaded_image = st.file_uploader("Upload Chest X-Ray or Wound Photo (JPEG)", type=["jpg", "jpeg", "png"])
        
        if uploaded_csv:
            df = pd.read_csv(uploaded_csv)
            st.warning("Bulk analysis is highly complex due to many required columns.")
            st.dataframe(df.head())
        if uploaded_image:
            st.success(f"Image received: {uploaded_image.name}")
            st.image(uploaded_image, caption="Image Ready for Processing", use_column_width=True)

    # -----------------------------
    # PAGE: MEDICATION CHECKER
    # -----------------------------
    elif menu == "Medication Checker":
        st.subheader("Drug-Drug Interaction Checker")
        st.caption("Demo: Tests interactions against a small, hard-coded database.")
        d1 = st.text_input("Drug 1 (e.g., Warfarin)")
        d2 = st.text_input("Drug 2 (e.g., Amiodarone)")
        if d1 and d2:
            interaction = check_interaction(d1, d2)
            if "Major" in interaction:
                st.error(f"Interaction Result: {interaction}")
            elif "Moderate" in interaction:
                st.warning(f"Interaction Result: {interaction}")
            else:
                st.success(f"Interaction Result: {interaction}")

    # -----------------------------
    # PAGE: CHATBOT
    # -----------------------------
    elif menu == "Chatbot":
        st.subheader("Clinical Information Chatbot")
        st.caption("Ask quick questions about the data and model logic (e.g., 'What about bleeding risk?').")
        user_input = st.text_input("Ask a question:")
        if user_input:
            response = chatbot_response(user_input)
            st.info(response)
