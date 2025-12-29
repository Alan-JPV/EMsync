import os
from flask import Flask
from hosital_model import db, Hospital

app = Flask(__name__)

# Ensure the database is created in the existing 'instance' folder
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'instance', 'emsync_network.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def seed_data():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Clear existing data if any, so we can replace with Phase 2 hospitals
        db.session.query(Hospital).delete()

        # Phase 2 Hospitals in Kerala
        hospitals = [
            Hospital(name="Aster Medicity", lat=10.0526, lon=76.2694, total_icu_beds=30, available_icu_beds=12, has_ventilator=True, has_specialist=True),
            Hospital(name="Lourdes Hospital", lat=9.9961, lon=76.2843, total_icu_beds=25, available_icu_beds=5, has_ventilator=True, has_specialist=True),
            Hospital(name="Rajagiri Hospital", lat=10.1082, lon=76.3507, total_icu_beds=40, available_icu_beds=18, has_ventilator=True, has_specialist=True),
            Hospital(name="General Hospital Ernakulam", lat=9.9774, lon=76.2807, total_icu_beds=20, available_icu_beds=0, has_ventilator=False, has_specialist=True)
        ]
        
        db.session.bulk_save_objects(hospitals)
        db.session.commit()
        print(f"Virtual Registry updated with: {[h.name for h in hospitals]}")

if __name__ == '__main__':
    seed_data()