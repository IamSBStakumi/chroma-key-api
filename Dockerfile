FROM python:3.11.9-slim-bullseye AS builder

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

COPY chroma_key_api ./chroma_key_api

RUN addgroup --system --gid 1001 python
RUN adduser --system --uid 1001 api

USER api

EXPOSE 8080

CMD ["uvicorn", "chroma-key-api.main:server", "--host", "0.0.0.0", "--port", "8080"]