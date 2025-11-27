#!/bin/bash
set -e

echo "=== Application Startup ==="

# Create Firebase credentials file from environment variable
if [ -n "$FIREBASE_CREDENTIAL_JSON" ]; then
    echo "Creating Firebase credentials file..."
    echo "$FIREBASE_CREDENTIAL_JSON" > ./TowerMap/Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json
    echo "✓ Firebase credentials file created successfully"
else
    echo "⚠ Warning: FIREBASE_CREDENTIAL_JSON environment variable not set"
    echo "If running locally, ensure the Firebase credentials file exists at:"
    echo "./TowerMap/Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json"
fi

# Run database migrations (if using database)
if command -v python >/dev/null 2>&1 && [ -f "TowerMap/manage.py" ]; then
    echo "Running database migrations..."
    python TowerMap/manage.py migrate --noinput || echo "Migrations skipped or failed"
fi

echo "=== Starting Application Server ==="
exec "$@"
