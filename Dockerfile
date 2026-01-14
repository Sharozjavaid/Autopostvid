FROM python:3.11-slim

# Install system dependencies for moviepy/ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    supervisor \
    cron \
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
RUN mkdir -p generated_scripts generated_images generated_audio generated_videos generated_slideshows/gpt15 generated_videos/transitions generated_videos/clips

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set up cron job for daily production (8 AM PST = 4 PM UTC)
# Note: Uncomment to enable scheduled production
# RUN echo "0 16 * * * cd /app && python3 daily_production.py >> /var/log/daily-production.log 2>&1" | crontab -

# Expose ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8001

# Run both services via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
