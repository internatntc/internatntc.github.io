# Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY TowerMap/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY TowerMap/ ./TowerMap/

# Create Firebase directory
RUN mkdir -p ./TowerMap/Firebase

# Create entrypoint script for handling Firebase credentials
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port (Django default)
EXPOSE 8000

# Use entrypoint to handle Firebase credentials
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "TowerMap/manage.py", "runserver", "0.0.0.0:8000"]
