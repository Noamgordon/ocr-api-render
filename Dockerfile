# Use an official Python base image with a Debian distribution (slim for smaller size)
FROM python:3.9-slim-buster

# Set environment variables to prevent interactive prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Install Tesseract OCR and its language packs, and Poppler utilities
# Poppler utilities (poppler-utils) are essential for pdf2image to work with PDFs.
# tesseract-ocr-eng for English, tesseract-ocr-heb for Hebrew.
# Add more tesseract-ocr-<lang_code> packages if you need other languages.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-heb \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that your Flask application will listen on
# Render will automatically map this to a public port.
EXPOSE 8000

# Command to run your application using Gunicorn (production web server)
# Gunicorn is robust for production. 'app:app' means 'app' Flask instance from 'app.py'
# Use the PORT environment variable provided by Render.
CMD ["gunicorn", "app:app", "-w", "4", "-b", "0.0.0.0:8000"]