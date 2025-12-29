from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Location data for Phase 2 Routing integration
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    
    # Resource tracking for Phase 3 logic
    total_icu_beds = db.Column(db.Integer, default=10)
    available_icu_beds = db.Column(db.Integer, default=5)
    has_ventilator = db.Column(db.Boolean, default=True)
    has_specialist = db.Column(db.Boolean, default=True) # e.g., Cardiologist/Neurologist

    def __repr__(self):
        return f'<Hospital {self.name}>'

class TransferSession(db.Model):
    """
    Tracks the lifecycle of a patient transfer
    """
    id = db.Column(db.Integer, primary_key=True)
    transfer_id_encrypted = db.Column(db.String(255), unique=True, nullable=False)
    origin_hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    destination_hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    
    # State Machine: PENDING -> ACCEPTED -> EN_ROUTE -> COMPLETED
    status = db.Column(db.String(50), default='PENDING')
    
    # SBAR Report Data (Stored as a text blob or JSON)
    sbar_json = db.Column(db.Text, nullable=True)