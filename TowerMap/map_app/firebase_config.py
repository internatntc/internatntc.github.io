# myapp/firebase_config.py
import firebase_admin
from firebase_admin import credentials, db
from decouple import config
import os
from mapui.settings import BASE_DIR
# Load service account from .env (as JSON string)

FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH')
FIREBASE_DATABASE_URL = config('FIREBASE_DATABASE_URL')

# # Firebase API
cred = credentials.Certificate(os.path.join(
    BASE_DIR, FIREBASE_CREDENTIALS_PATH))
firebase_admin.initialize_app(
    cred, {'databaseURL': FIREBASE_DATABASE_URL})

# Reference to the database
db_ref = db.reference()
