# backend/Dockerfile

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fix pip + setuptools properly
RUN pip install --upgrade pip setuptools wheel
# This is the key fix — injects setuptools into ALL build envs
ENV PIP_NO_BUILD_ISOLATION=false
RUN pip install --upgrade "setuptools<70" "wheel"

# Install faster-whisper instead (no build issues, actually faster & better)
RUN pip install --no-cache-dir faster-whisper==1.0.3

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]