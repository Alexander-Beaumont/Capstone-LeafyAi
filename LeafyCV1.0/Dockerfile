FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
# CPU wheels keep the MVP image much smaller than CUDA-enabled PyPI wheels.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch>=2.6,<3" "torchvision>=0.21,<1"
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py", "run-loop", "--poll-seconds", "15"]
