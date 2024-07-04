FROM python:3.11.9-slim-bullseye AS base
# FROM base as builder

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

COPY chroma_key_api ./

# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim AS runner
# FROM base AS runner 
# WORKDIR /app

# RUN addgroup --system --gid 1001 python
# RUN adduser --system --uid 1001 api

# COPY --from=builder /app /app

# COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# COPY --from=builder /usr/local/bin /usr/local/bin

# USER api

EXPOSE 8080

CMD ["poetry", "run", "uvicorn", "chroma-key-api.main:server", "--host", "0.0.0.0", "--port", "8080"]