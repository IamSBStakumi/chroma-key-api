FROM python:3.11.9-slim-bullseye AS base
FROM base AS builder

RUN pip install poetry

WORKDIR /app

RUN apt -y update && apt -y upgrade && apt -y install tar xz

RUN curl https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz > /tmp/ffmpeg-release.tar.xz \ 
    && tar xvf /tmp/ffmpeg-release.tar.xz -C /opt \ 
    && mv /opt/ffmpeg-* /opt/ffmpeg \
    && cd /opt/ffmpeg \
    && mv model /usr/local/share \
    && mv ffmpeg ffprobe qt-faststart /usr/local/bin \
    && rm /tmp/ffmpeg-release.tar.xz

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY . ./

FROM base AS runner
WORKDIR /app

RUN apt -y update && apt -y upgrade && apt install -y libopencv-dev

RUN addgroup --system --gid 1001 python && \
    adduser --system --uid 1001 api

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /opt/ffmpeg /opt/ffmpeg
COPY --from=builder /usr/local/share/model /usr/local/share
COPY --from=builder /usr/local/bin/ff* /usr/local/bin
COPY --from=builder /usr/local/bin/qt-* /usr/local/bin
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libGL.so.1 /usr/lib/x86_64-linux-gnu/libGL.so.1
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libgthread-2.0.so.0 /usr/lib/x86_64-linux-gnu/libgthread-2.0.so.0
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0 /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libGLX.so.0 /usr/lib/x86_64-linux-gnu/libGLX.so.0
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libX11.so.6 /usr/lib/x86_64-linux-gnu/libX11.so.6
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libxcb.so.1 /usr/lib/x86_64-linux-gnu/libxcb.so.1
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libXau.so.6 /usr/lib/x86_64-linux-gnu/libXau.so.6
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libXdmcp.so.6 /usr/lib/x86_64-linux-gnu/libXdmcp.so.6
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libbsd.so.0 /usr/lib/x86_64-linux-gnu/libbsd.so.0
# COPY --from=builder /usr/lib/x86_64-linux-gnu/libmd.so.0 /usr/lib/x86_64-linux-gnu/libmd.so.0

# COPY --from=builder /usr/lib/x86_64-linux-gnu/cmake/opencv4 /usr/lib/x86_64-linux-gnu/cmake/opencv4

COPY --from=builder /app /app

USER api

EXPOSE 8080

CMD ["poetry", "run", "uvicorn", "main.server:server", "--host", "0.0.0.0", "--port", "8080"]
