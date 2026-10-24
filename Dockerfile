FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY data/ ./data/
ENV MODEL_DIR=/app/models
RUN mkdir -p /app/models && python -m backend.train && mkdir -p /app/outputs
COPY --from=web /web/dist ./frontend/dist
ENV DB_PATH=/app/outputs/carecompass.db
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
