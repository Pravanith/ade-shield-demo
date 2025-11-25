import streamlit as st
import requests
import os
from dotenv import load_dotenv

# -----------------------------
# 1. SETUP & CONFIGURATION
# -----------------------------
# Load environment variables from .env file
load_dotenv()

# Get the Backend URL (If not found in .env, default to localhost)
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="ADE Clinical Dashboard", layout="wide")

# -----------------------------
# 2. HELPER FUNCTIONS (API CALLS)
# -----------------------------
def fetch_risk_calculation(payload):
    """Sends patient data to the backend for processing."""
    try:
        # We send a POST request to the separate backend service
        response = requests.post(f"{API_URL}/calculate", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend Error ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to Backend at {API_URL}. Is the server running?")
        return None

def fetch_interaction(d1, d2):
    try:
        response = requests.post(f"{API_URL}/interaction", json={"drug1": d1, "drug2": d2})
        if response.status_code == 200:
            return response.json()['result']
    except:
        return "Connection Error"

# -----------------------------
# 3. USER INTERFACE
# -----------------------------
st.title("🏥 Clinical Risk Monitor")
st.caption(f"Backend Status: Connected to {API_URL}")

tabs = st.tabs(["Patient Risk Calculator", "Drug Interactions"])

with tabs[0]:
    st.subheader("Patient Admission Assessment")
    
    with st.form("risk_input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", 18, 100, 65)
            gender = st.selectbox("Gender", ["Male", "Female"])
            weight = st.number_input("Weight (kg)", 40, 150, 70)
            inr = st.number_input("INR", 0.8, 10.0, 1.0)
            creat = st.number_input("Creatinine", 0.5, 8.0, 0.9)
        
        with col2:
            st.write("**Clinical Factors**")
            anticoag = st.checkbox("Anticoagulant Use")
            antiplatelet = st.checkbox("Antiplatelet Use")
            insulin = st.checkbox("Insulin Use")
            diuretic = st.checkbox("Diuretic Use")
            acei = st.checkbox("ACEi/ARB Use")
            hbp = st.checkbox("Uncontrolled BP")
            ckd = st.checkbox("Impaired Renal Status")
            active_chemo = st.checkbox("Active Chemotherapy")

        submit = st.form_submit_button("Calculate Risks")

    if submit:
        # Prepare payload matching Backend Pydantic Model
        payload = {
            "age": age, "gender": gender, "weight": weight, "inr": inr,
            "baseline_creat": creat, "on_anticoag": anticoag, 
            "on_antiplatelet": antiplatelet, "on_insulin": insulin,
            "on_diuretic": diuretic, "on_acei_arb": acei,
            "uncontrolled_bp": hbp, "impaired_renal": ckd,
            "active_chemo": active_chemo,
            # Defaults for fields not in this simple form
            "race": "Other", "antibiotic_order": False, "dietary_change": False,
            "contrast_exposure": False, "prior_stroke": False, "hist_gi_bleed": False,
            "smoking_calc": False, "alcohol_use": False, "liver_disease": False,
            "high_hba1c": False, "neuropathy_history": False, "recent_dka": False
        }

        data = fetch_risk_calculation(payload)
        
        if data:
            st.success("Analysis Complete")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Bleeding Risk", f"{data['bleeding_risk']}%")
            kpi2.metric("Hypoglycemia", f"{data['hypoglycemic_risk']}%")
            kpi3.metric("AKI Risk", f"{data['aki_risk']}%")
            kpi4.metric("Fragility", f"{data['fragility_index']}%")
            
            if data['primary_score'] >= 70:
                st.error(f"⚠️ Primary Threat: {data['primary_alert']} ({data['primary_score']}%)")

with tabs[1]:
    st.subheader("Interaction Checker")
    d1 = st.text_input("Drug A")
    d2 = st.text_input("Drug B")
    if st.button("Check"):
        res = fetch_interaction(d1, d2)
        st.info(f"Result: {res}")