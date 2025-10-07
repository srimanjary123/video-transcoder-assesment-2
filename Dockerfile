
FROM python:3.11-slim

# Install ffmpeg CPU work
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
  && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Expose API port
EXPOSE 8080

ENV JWT_SECRET=supersecret

# Run API
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

