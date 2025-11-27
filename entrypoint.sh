#!/bin/bash
set -e

echo "=== Application Startup ==="

# Create Firebase credentials file from environment variable
if [ -n "$FIREBASE_CREDENTIAL_JSON" ]; then
    echo "Creating Firebase credentials file..."
    mkdir -p ./TowerMap/Firebase
    echo "$FIREBASE_CREDENTIAL_JSON" > ./TowerMap/Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json
    echo "✓ Firebase credentials file created successfully"
else
    echo "⚠ Warning: FIREBASE_CREDENTIAL_JSON environment variable not set"
    echo "If running locally, ensure the Firebase credentials file exists at:"
    echo "./TowerMap/Firebase/towermap-b98ee-firebase-adminsdk-fbsvc-d502a34283.json"
fi

# Run database migrations
if command -v python >/dev/null 2>&1 && [ -f "TowerMap/manage.py" ]; then
    echo "Running database migrations..."
    python TowerMap/manage.py migrate --noinput || echo "Migrations completed with warnings"
    
    # Create superuser from environment variables
    echo "Checking superuser..."
    SUPERUSER_USERNAME="${SUPERUSER_USERNAME:-admin}"
    SUPERUSER_EMAIL="${SUPERUSER_EMAIL:-admin@example.com}"
    SUPERUSER_PASSWORD="${SUPERUSER_PASSWORD:-admin123}"
    
    python TowerMap/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$SUPERUSER_USERNAME', '$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')
    print('✓ Superuser created successfully')
    print('   Username: $SUPERUSER_USERNAME')
    print('   Password: $SUPERUSER_PASSWORD')
    print('   Email: $SUPERUSER_EMAIL')
    print('⚠ Please change the password after first login!')
else:
    print('✓ Superuser already exists')
"
fi

echo "=== Starting Application Server ==="
exec "$@"
