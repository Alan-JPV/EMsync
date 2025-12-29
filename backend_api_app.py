import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from hosital_model import db, Hospital, TransferSession
from security import encrypt_patient_data
from sbar_logic import generate_sbar_report # Import the new logic
from flask_socketio import SocketIO, emit
import uuid
from security import decrypt_patient_data # Ensure this is imported
import json  # Add this import

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*") # <--- Add this

# Database Configuration
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'instance', 'emsync_network.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- RE-ADDED GET ENDPOINT ---
@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Returns a list of all hospitals and their current resource status."""
    hospitals = Hospital.query.all()
    output = []
    for h in hospitals:
        output.append({
            'id': h.id,
            'name': h.name,
            'lat': h.lat,
            'lon': h.lon,
            'available_beds': h.available_icu_beds,
            'has_ventilator': h.has_ventilator,
            'has_specialist': h.has_specialist
        })
    return jsonify(output)

'''@app.route('/api/request_transfer', methods=['POST'])
def request_transfer():
    data = request.get_json()
    
    # 1. Gather inputs for the SBAR Report
    # These would normally come from your Phase 1 Model and Phase 2 Sensors
    patient_info = data.get('patient_info', {})
    vitals = data.get('vitals', {})
    ml_prediction = data.get('severity', 'Moderate') # Phase 1 output
    needs = data.get('resource_needs', [])
    
    # 2. Generate the SBAR JSON
    sbar_report_json = generate_sbar_report(patient_info, vitals, ml_prediction, needs)
    
    # 3. Encrypt sensitive identity
    raw_info = f"Patient: {patient_info.get('name')} | DOB: {patient_info.get('dob')}"
    encrypted_id = encrypt_patient_data(raw_info)
    
    # 4. Update Registry & Save Session
    target_hospital = Hospital.query.get(data['destination_id'])
    if target_hospital and target_hospital.available_icu_beds > 0:
        target_hospital.available_icu_beds -= 1
        
        new_session = TransferSession(
            transfer_id_encrypted=encrypted_id,
            origin_hospital_id=1,
            destination_hospital_id=target_hospital.id,
            status='PENDING',
            sbar_json=sbar_report_json # Save the generated report
        )
        
        db.session.add(new_session)
        db.session.commit()

        # --- FIXED SOCKETIO EMIT ---
        socketio.emit('new_transfer_alert', {
            "transfer_id": encrypted_id,
            "hospital_id": target_hospital.id,
            "hospital_name": target_hospital.name,
            "sbar": sbar_report_json
        })
        # ---------------------------
        
        return jsonify({
            "status": "success",
            "transfer_id": encrypted_id,
            "sbar_preview": sbar_report_json 
        }), 201
    
    return jsonify({"status": "error", "message": "No beds available"}), 400'''

@app.route('/api/request_transfer', methods=['POST'])
def request_transfer():
    data = request.get_json()
    
    # 1. Gather inputs
    patient_info = data.get('patient_info', {})
    vitals = data.get('vitals', {})
    ml_prediction = data.get('severity', 'Moderate')
    needs = data.get('resource_needs', [])
    
    # 2. Generate SBAR and Encrypt
    sbar_report_json = generate_sbar_report(patient_info, vitals, ml_prediction, needs)
    raw_info = f"Patient: {patient_info.get('name')} | DOB: {patient_info.get('dob')}"
    encrypted_id = encrypt_patient_data(raw_info)
    
    # 3. Create Session (DO NOT SUBTRACT BED HERE)
    new_session = TransferSession(
        transfer_id_encrypted=encrypted_id,
        origin_hospital_id=1,
        destination_hospital_id=data['destination_id'],
        status='PENDING',
        sbar_json=sbar_report_json
    )
    
    db.session.add(new_session)
    db.session.commit()

    # 4. Notify Hospital
    socketio.emit('new_transfer_alert', {
        "transfer_id": encrypted_id,
        "hospital_id": data['destination_id'],
        "hospital_name": Hospital.query.get(data['destination_id']).name,
        "sbar": sbar_report_json
    })
    
    return jsonify({"status": "success", "transfer_id": encrypted_id}), 201

@app.route('/api/accept_transfer', methods=['POST'])
def accept_transfer():
    data = request.get_json()
    hospital_id = data.get('hospital_id')
    token = data.get('token')

    hospital = Hospital.query.get(hospital_id)
    session = TransferSession.query.filter_by(transfer_id_encrypted=token).first()

    if hospital and hospital.available_icu_beds > 0:
        # OFFICIAL BED REDUCTION
        hospital.available_icu_beds -= 1
        if session:
            session.status = 'ACCEPTED'
        
        db.session.commit()
        
        # Broadcast to update all Paramedic views instantly
        socketio.emit('resource_update', {"hospital_id": hospital_id})
        
        return jsonify({"status": "success", "new_count": hospital.available_icu_beds}), 200
    
    return jsonify({"status": "error", "message": "No beds available"}), 400

'''@app.route('/api/update_beds', methods=['POST'])
def update_beds():
    data = request.get_json()
    hospital_id = data.get('id')
    new_count = data.get('beds')
    
    hospital = Hospital.query.get(hospital_id)
    if hospital:
        hospital.available_icu_beds = int(new_count)
        db.session.commit()
        
        # Optional: Broadcast to all UIs that beds have changed
        socketio.emit('resource_update', {"hospital_id": hospital_id, "new_beds": new_count})
        
        return jsonify({"status": "success", "new_count": hospital.available_icu_beds}), 200
    return jsonify({"status": "error", "message": "Hospital not found"}), 404'''

'''@app.route('/api/decrypt', methods=['POST'])
def decrypt_token():
    data = request.get_json()
    token = data.get('token')
    
    # 1. Decrypt the PII from the token
    decrypted_text = decrypt_patient_data(token)
    
    # 2. Fetch the most recent session for this token to show the SBAR
    session = TransferSession.query.filter_by(transfer_id_encrypted=token).first()
    
    return jsonify({
        "plain_text": decrypted_text,
        "sbar": eval(session.sbar_json) if session else "No SBAR found"
    })'''

'''@app.route('/api/decrypt', methods=['POST'])
def decrypt_token():
    data = request.get_json()
    token = data.get('token')
    
    # 1. Decrypt the PII from the token
    decrypted_text = decrypt_patient_data(token)
    
    # 2. Fetch the session
    session = TransferSession.query.filter_by(transfer_id_encrypted=token).first()
    
    # 3. Use json.loads instead of eval to safely handle 'null' and JSON formatting
    sbar_data = json.loads(session.sbar_json) if session and session.sbar_json else "No SBAR found"
    
    return jsonify({
        "plain_text": decrypted_text,
        "sbar": sbar_data
    })'''

@app.route('/api/update_beds', methods=['POST'])
def update_beds():
    data = request.get_json()
    h_id = data.get('id')
    new_count = data.get('beds')
    
    hospital = db.session.get(Hospital, h_id) # Using modern Session.get()
    if hospital:
        hospital.available_icu_beds = int(new_count)
        db.session.commit()
        
        # Broadcast the manual change to the whole network
        socketio.emit('resource_update', {"hospital_id": h_id})
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 404

@app.route('/api/decrypt', methods=['POST'])
def decrypt_token():
    data = request.get_json()
    token = data.get('token')
    decrypted_text = decrypt_patient_data(token)
    session = TransferSession.query.filter_by(transfer_id_encrypted=token).first()
    
    # Use json.loads to prevent the 'null' NameError
    sbar_data = json.loads(session.sbar_json) if session and session.sbar_json else "No SBAR found"
    
    return jsonify({
        "plain_text": decrypted_text,
        "sbar": sbar_data
    })

@app.route('/api/reset_simulation', methods=['POST'])
def reset_simulation():
    try:
        # 1. Clear all previous transfer sessions
        TransferSession.query.delete()
        
        # 2. Reset beds to original values (e.g., Aster=10, Lourdes=8, Rajagiri=20)
        hospitals = Hospital.query.all()
        for h in hospitals:
            if "Aster" in h.name: h.available_icu_beds = 10
            elif "Lourdes" in h.name: h.available_icu_beds = 8
            elif "Rajagiri" in h.name: h.available_icu_beds = 20
            else: h.available_icu_beds = 5
            
        db.session.commit()
        
        # 3. Broadcast update to all connected UIs
        socketio.emit('resource_update', {"status": "reset"})
        
        return jsonify({"status": "success", "message": "Simulation Reset Complete"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    #app.run(debug=True, port=5000)
    socketio.run(app, debug=True, port=5000)