# Two-stage build: wheels in the builder, a slim runtime with a non-root user.
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim
ARG COMMIT_SHA=dev
ENV CB_COMMIT_SHA=$COMMIT_SHA \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
# Alembic runs from the image too (deploy step), so ship the migrations.
COPY alembic.ini ./
COPY migrations ./migrations
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health').status==200 else 1)"
CMD ["sh", "-c", "uvicorn chops_buddy.api.main:app --host 0.0.0.0 --port ${PORT}"]
