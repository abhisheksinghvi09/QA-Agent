# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Install System Dependencies
# We need wget and unzip. We added ca-certificates for secure downloading.
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Google Chrome
# FIX: We download the .deb file directly to bypass the 'apt-key' issue
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 5. Set working directory
WORKDIR /app

# 6. Copy requirements first (for caching layers)
COPY requirements.txt .

# 7. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copy the app code
COPY . .

# 9. Create necessary directories for storage
RUN mkdir -p uploads vector_store_data

# 10. Expose the port
EXPOSE 8000

# 11. Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]