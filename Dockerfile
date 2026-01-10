FROM python:3.11-slim

# Install system dependencies for moviepy/ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p generated_scripts generated_images generated_audio generated_videos

# Expose port for Streamlit (optional, if you want to access the UI)
EXPOSE 8501

# Default command: run the automation agent
CMD ["python3", "auto_runner.py", "--smart"]
