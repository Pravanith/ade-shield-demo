elif menu == "Risk Calculator":
    st.subheader("Manual Multiple-Risk Calculator (High-Detail)")
    st.caption("Adjust the patient factors below to see the predicted risk scores for multiple ADEs.")

    # --- DEMOGRAPHIC & CORE INPUTS (CLEANED) ---
    st.markdown("#### 👤 Patient Demographics & Core Factors")
    
    # Core demographic inputs (only number inputs and selects remain here)
    demo_col1, demo_col2, demo_col3 = st.columns(3)
    
    # Column 1: Core Identity
    age_calc = demo_col1.number_input("Age", 18, 100, 78)
    gender_calc = demo_col1.selectbox("Gender", ['Male', 'Female'], index=1)
    race_calc = demo_col1.selectbox("Race/Ethnicity", ['Non-Hispanic Black', 'Other'], index=1)

    # Column 2: Vitals & Key Labs (INR, Weight, Height)
    weight_calc = demo_col2.number_input("Weight (kg)", 30, 150, 55)
    height_calc = demo_col2.number_input("Height (cm)", 100, 220, 175)
    baseline_creat = demo_col2.number_input("Baseline Creatinine (mg/dL)", 0.5, 5.0, 0.9, format="%.1f") 
    
    # Column 3: Acute Labs (INR Only)
    inr_calc = demo_col3.number_input("INR (if applicable)", 0.5, 10.0, 4.1, format="%.2f")

    st.markdown("---")
    
    # --- ACUTE & CHRONIC INPUTS (CHECKBOXES MOVED HERE) ---
    input_col1, input_col2, input_col3 = st.columns(3)
    
    # Column 1: Bleeding & GI Factors (Consolidated)
    st.markdown("#### 🩸 Bleeding & GI Factors")
    prior_stroke = input_col1.checkbox("History of Stroke/TIA", value=True) 
    hist_gi_bleed = input_col1.checkbox("History of GI Bleed", value=True)
    
    st.markdown("**— Medication & Lifestyle —**")
    uncontrolled_bp = input_col1.checkbox("Uncontrolled BP (Systolic > 140)", value=True) # MOVED HERE
    smoking_calc = input_col1.checkbox("Current Smoker", value=True) # MOVED HERE
    on_anticoag = input_col1.checkbox("Anticoagulant Use", value=True)
    on_antiplatelet = input_col1.checkbox("Antiplatelet Use (Aspirin/Plavix)", value=True)
    alcohol_use = input_col1.checkbox("Heavy Alcohol Use", value=True)
    antibiotic_order = input_col1.checkbox("New Antibiotic Order", value=True)
    dietary_change = input_col1.checkbox("Significant Dietary Change (Vit K)", value=False)
    liver_disease = input_col1.checkbox("History of Liver Disease", value=True)


    # Column 2: Diabetes & Renal Factors (Unmodified)
    st.markdown("#### 🦠 Diabetes & Renal Factors")
    on_insulin = input_col2.checkbox("Insulin/High-Risk DM Meds", value=True)
    high_hba1c = input_col2.checkbox("HbA1c > 9.0% (Poor DM Control)", value=True)
    neuropathy_history = input_col2.checkbox("History of Neuropathy/Ulcer", value=False)
    impaired_renal = input_col2.checkbox("Impaired Renal Status", value=True)
    recent_dka = input_col2.checkbox("Recent DKA/HHS Admission", value=True)
    
    # Column 3: Cardiovascular & Cancer Factors (Unmodified)
    st.markdown("#### ❤️ Cardio & Other Risks")
    on_acei_arb = input_col3.checkbox("ACEi/ARB Therapy", value=False)
    on_diuretic = input_col3.checkbox("Diuretic Use", value=False)
    active_chemo = input_col3.checkbox("Active Chemotherapy", value=True)
    contrast_exposure = input_col3.checkbox("Recent Contrast Dye Exposure", value=False)


    # --- CALCULATIONS ---
    # Passing the variables (order remains critical)
    bleeding_risk = calculate_bleeding_risk(age_calc, inr_calc, on_anticoag, hist_gi_bleed, uncontrolled_bp, on_antiplatelet, gender_calc, weight_calc, smoking_calc, alcohol_use, antibiotic_order, dietary_change, liver_disease, prior_stroke)
    hypoglycemia_risk = calculate_hypoglycemia_risk(on_insulin, impaired_renal, high_hba1c, neuropathy_history, gender_calc, weight_calc, recent_dka)
    aki_risk = calculate_aki_risk(age_calc, on_diuretic, on_acei_arb, uncontrolled_bp, active_chemo, gender_calc, weight_calc, race_calc, baseline_creat, contrast_exposure)
    comorbidity_load = calculate_comorbidity_load(prior_stroke, active_chemo, recent_dka, liver_disease, smoking_calc, uncontrolled_bp)


    st.markdown("---")
    
    # --- OUTPUTS ---
    output_col1, output_col2, output_col3, output_col4 = st.columns(4)
    output_col1.metric("Bleeding Risk", f"{bleeding_risk}%", "CRITICAL ALERT")
    output_col2.metric("Hypoglycemia Risk", f"{hypoglycemia_risk}%", "CRITICAL ALERT")
    output_col3.metric("AKI Risk (Renal)", f"{aki_risk}%", "HIGH ALERT")
    output_col4.metric("Clinical Fragility Index", f"{comorbidity_load}%", "CRITICAL ALERT")


    if bleeding_risk >= 70 or hypoglycemia_risk >= 70 or aki_risk >= 70:
        st.error("🚨 HIGH RISK ALERT: Check specific patient risks.")
    else:
        st.success("Patient risk is manageable. Monitoring is sufficient.")
