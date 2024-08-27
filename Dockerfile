FROM python:3.11.9-slim-bullseye AS base
FROM base AS builder

RUN pip install poetry

WORKDIR /app

RUN apt -y update && apt -y upgrade

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY . ./

FROM base AS runner
WORKDIR /app

RUN apt -y update && apt -y upgrade && \
    apt install -y libopencv-dev

RUN addgroup --system --gid 1001 python && \
    adduser --system --uid 1001 api

USER api

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --from=builder /app /app

EXPOSE 8080

CMD ["poetry", "run", "uvicorn", "main.server:server", "--host", "0.0.0.0", "--port", "8080"]
