# 1. Base Image
FROM python:3.10-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set Working Directory
WORKDIR /app

# 4. Copy requirements
COPY requirements.txt .

# 5. Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy App Code
COPY . .

# 7. Expose Streamlit Port
EXPOSE 8501

# 8. Run Streamlit
# We capture the PORT environment variable for Cloud compatibility (e.g., Render/Heroku)
CMD ["streamlit", "run", "ui_app.py", "--server.port=8501", "--server.address=0.0.0.0"]