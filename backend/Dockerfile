FROM python:3.10-slim

# Install system dependencies
# libgl1-mesa-glx and libgomp1 are required for OpenCV
# poppler-utils is required for PDF to image conversion if needed later
# libreoffice-writer is required for Word/Office to PDF conversion
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    poppler-utils \
    gcc \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
