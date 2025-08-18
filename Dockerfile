FROM python:3.13.7-slim-trixie AS base
FROM base AS builder

RUN pip install poetry

WORKDIR /app

RUN apt -y update && \
    apt -y upgrade && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry sync install --without dev

COPY . ./

FROM base AS runner
WORKDIR /app

# パッケージ更新、OpenCVインストール、キャッシュ削除
RUN apt -y update && apt -y upgrade && \
    apt install -y ffmpeg libopencv-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザー作成
RUN addgroup --system --gid 1001 python && \
    adduser --system --uid 1001 --shell /usr/sbin/nologin api

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# コピーしたファイルの所有権をapiユーザーに変更
RUN chown -R api:python /app

USER api
ENV WEB_CONCURRENCY=1

EXPOSE 8080

CMD ["uvicorn", "main.server:server", "--host", "0.0.0.0", "--port", "8080"]
