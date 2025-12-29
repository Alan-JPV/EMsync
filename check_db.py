import os
from flask import Flask
from hosital_model import db, Hospital # Using your exact filename

app = Flask(__name__)

# This logic finds the absolute path to ensure the database opens correctly
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'instance', 'emsync_network.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def verify_hospitals():
    with app.app_context():
        try:
            hospitals = Hospital.query.all()
            if not hospitals:
                print("Database connected, but no hospitals found. Run init_db.py again.")
            else:
                print(f"Successfully connected to the Virtual Network.")
                print(f"Found {len(hospitals)} hospitals:\n")
                print(f"{'Name':<25} | {'Location':<20} | {'Beds Available'}")
                print("-" * 65)
                for h in hospitals:
                    location = f"{h.lat}, {h.lon}"
                    print(f"{h.name:<25} | {location:<20} | {h.available_icu_beds}/{h.total_icu_beds}")
        except Exception as e:
            print(f"Error: Could not access the database. Details: {e}")
            print(f"Attempted path: {db_path}")

if __name__ == '__main__':
    verify_hospitals()