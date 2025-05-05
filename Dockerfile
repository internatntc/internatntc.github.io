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

# Set Firebase credentials directory (expect to mount secret later)
RUN mkdir -p ./TowerMap/Firebase

# Expose port (Django default)
EXPOSE 8000

# Run server
CMD ["python", "TowerMap/manage.py", "runserver", "0.0.0.0:8000"]
