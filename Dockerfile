# Multi-stage build: frontend (Node) -> runtime (Python). Data persist in the /data volume.
FROM node:22-bookworm-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
COPY experiment/ /app/experiment/
RUN npx vite build

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SMIT_DATA_DIR=/data
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY experiment/ experiment/
COPY research/ research/
COPY templates/ templates/
COPY pilot/ pilot/
COPY docs/ docs/
COPY --from=web /app/frontend/dist frontend/dist
RUN useradd --create-home smit && mkdir -p /data && chown -R smit /data /app/experiment/stimuli
USER smit
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
