# Headless test environment. The Windows GUI and microphone run natively.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen

WORKDIR /app
COPY requirements.txt requirements-voice.txt requirements-dev.txt ./
RUN python -m pip install --no-cache-dir -r requirements-dev.txt
COPY faro/ faro/
COPY scripts/ scripts/
COPY tests/ tests/
COPY app.py ./

CMD ["python", "-m", "pytest", "-q"]
