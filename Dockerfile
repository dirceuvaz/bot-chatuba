# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for PyNaCl, ffmpeg, and mysql client if needed
# libffi-dev, libnacl-dev, python3-dev, gcc are often needed for building wheels
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Expose port for health check
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
