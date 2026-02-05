FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/

# Create data directories
RUN mkdir -p /app/data/logs /app/data/notifications

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Australia/Perth

# Run both scheduler daemon and dashboard
# Using shell to run multiple processes
CMD python -u src/main.py --daemon & python -u src/dashboard.py
