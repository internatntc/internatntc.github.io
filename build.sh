#!/bin/bash
set -e

echo "Creating Firebase credentials file..."

# Create Firebase directory
mkdir -p Firebase

# Create the credentials file from environment variable
if [ ! -z "$FIREBASE_CREDENTIAL_JSON" ]; then
    echo "$FIREBASE_CREDENTIAL_JSON" > Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json
    echo "Firebase credentials file created successfully"
else
    echo "Warning: FIREBASE_CREDENTIAL_JSON not set"
fi

# Continue with normal build process
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
