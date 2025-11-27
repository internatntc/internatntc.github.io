# TowerMap/firebase_config.py
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    # Try environment variable first
    firebase_cred_json = os.environ.get('FIREBASE_CREDENTIAL_JSON')
    
    if firebase_cred_json:
        # Use environment variable (Render.com)
        try:
            cred_dict = json.loads(firebase_cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://towermap-b98ee-default-rtdb.firebaseio.com')
            })
            print("Firebase initialized from environment variable")
        except json.JSONDecodeError as e:
            print(f"Error parsing FIREBASE_CREDENTIAL_JSON: {e}")
            raise
    else:
        # Fallback to file-based approach (local development)
        cred_path = 'Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json'
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://towermap-b98ee-default-rtdb.firebaseio.com')
            })
            print(f"Firebase initialized from file: {cred_path}")
        else:
            print("Firebase credentials not found. Using environment variable approach.")
            # You might want to raise an error here or handle gracefully

# Reference to the database
db_ref = db.reference()
