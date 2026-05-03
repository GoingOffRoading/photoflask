FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir Flask==3.0.0 Werkzeug==3.0.1

# Copy application files
COPY src/ ./src/

# Create a data directory for the database
RUN mkdir -p /data

EXPOSE 5000

ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

WORKDIR /app/src

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
