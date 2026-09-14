FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/leafy
COPY powerboard_control/requirements.txt /tmp/powerboard-requirements.txt
RUN pip install --no-cache-dir -r /tmp/powerboard-requirements.txt
COPY powerboard_control ./powerboard_control
EXPOSE 8010
CMD ["uvicorn", "powerboard_control.main:app", "--host", "0.0.0.0", "--port", "8010"]
