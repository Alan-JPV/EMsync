'''import json

def generate_sbar_report(patient_info, vitals, ml_prediction, resource_needs):
    """
    Automates the creation of an SBAR report based on clinical and ML data.
    """
    
    # S - Situation
    situation = {
        "urgency": ml_prediction, # e.g., 'Critical' from Phase 1 Model
        "complaint": patient_info.get("primary_complaint", "Unknown"),
        "status_summary": f"Patient is in {ml_prediction} condition with {patient_info.get('primary_complaint')}."
    }
    
    # B - Background
    background = {
        "age": patient_info.get("age"),
        "gender": patient_info.get("gender"),
        "history": patient_info.get("history", "No known history"),
        "incident_time": patient_info.get("incident_time")
    }
    
    # A - Assessment
    # Using your engineered features logic from Phase 1
    assessment = {
        "vitals_snapshot": vitals,
        "hypoxia": "Yes" if vitals.get("o2sat", 100) < 90 else "No",
        "fever": "Yes" if vitals.get("temp", 37) >= 38 else "No",
        "predicted_needs": resource_needs # e.g., ['Ventilator', 'ICU Bed']
    }
    
    # R - Recommendation
    recommendation = {
        "suggested_unit": "ICU/Critical Care" if ml_prediction == "Critical" else "General Ward",
        "priority_action": "Requires immediate specialist review upon arrival."
    }
    
    # Return as a JSON-ready dictionary
    sbar_report = {
        "S": situation,
        "B": background,
        "A": assessment,
        "R": recommendation
    }
    
    return json.dumps(sbar_report)

# --- Simple Test Section ---
if __name__ == "__main__":
    p_info = {"age": 45, "gender": "M", "primary_complaint": "Chest Pain", "history": "Hypertension"}
    v_data = {"temp": 39.1, "heartrate": 110, "o2sat": 88}
    ml_res = "Critical"
    needs = ["Ventilator", "Cardiologist"]
    
    report = generate_sbar_report(p_info, v_data, ml_res, needs)
    print("Generated SBAR Report Object:")
    print(report)'''


import json

def generate_sbar_report(patient_info, vitals, ml_prediction, resource_needs):
    """
    Automates the creation of an SBAR report based on clinical and ML data.
    """
    
    # S - Situation
    situation = {
        "urgency": ml_prediction,
        "complaint": patient_info.get("primary_complaint", "Unknown"),
        "status_summary": f"Patient is in {ml_prediction} condition with {patient_info.get('primary_complaint')}."
    }
    
    # B - Background
    background = {
        "age": patient_info.get("age"),
        "gender": patient_info.get("gender"),
        "history": patient_info.get("history", "No known history"),
        "incident_time": patient_info.get("incident_time")
    }
    
    # A - Assessment
    # FIXED: Added float() casting to prevent TypeError between strings and integers
    assessment = {
        "vitals_snapshot": vitals,
        "hypoxia": "Yes" if float(vitals.get("o2sat", 100)) < 90 else "No",
        "fever": "Yes" if float(vitals.get("temp", 37)) >= 38 else "No",
        "predicted_needs": resource_needs 
    }
    
    # R - Recommendation
    recommendation = {
        "suggested_unit": "ICU/Critical Care" if ml_prediction == "Critical" else "General Ward",
        "priority_action": "Requires immediate specialist review upon arrival."
    }
    
    # Return as a JSON string for database storage
    sbar_report = {
        "S": situation,
        "B": background,
        "A": assessment,
        "R": recommendation
    }
    
    return json.dumps(sbar_report)