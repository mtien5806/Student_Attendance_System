# Student Attendance System (SAS) - Dockerfile

# Usage:
#   docker build -t sas .
#   docker run -it --rm -v ${PWD}:/app sas
#   docker run -it --rm -v ${PWD}:/app sas python main.py --seed --reset

# Sử dụng Python 3.11 slim image làm base
FROM python:3.11-slim

# Make Python logs unbuffered & avoid .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better build cache)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Optional: common output folder
RUN mkdir -p reports

CMD ["python", "main.py"]
