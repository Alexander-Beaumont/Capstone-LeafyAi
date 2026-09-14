FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/leafy
COPY sensor_ingest/requirements.txt /tmp/sensor-requirements.txt
RUN pip install --no-cache-dir -r /tmp/sensor-requirements.txt
COPY sensor_ingest ./sensor_ingest
CMD ["python", "-m", "sensor_ingest.main"]
