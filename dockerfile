
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# System setup
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install Python 3.11 and pip

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    build-essential \
    curl \
    git && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install pip deps including CUDA-compatible torch
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir tensorflow && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir python-dotenv


# Copy rest of app
COPY app /app/app
COPY config /app/config
COPY data /app/data



# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
