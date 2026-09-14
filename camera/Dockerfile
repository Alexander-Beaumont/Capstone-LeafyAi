FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/leafy
COPY requirements.txt /tmp/camera-requirements.txt
RUN pip install --no-cache-dir -r /tmp/camera-requirements.txt
COPY . ./camera
CMD ["python", "-m", "camera.main"]
