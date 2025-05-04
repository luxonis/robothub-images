# Stage 1: Build Python 3.12
FROM debian:bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libbz2-dev \
    liblzma-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and build Python 3.12
WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz \
    && tar xzf Python-3.12.3.tgz \
    && cd Python-3.12.3 \
    && ./configure --enable-optimizations --prefix=/usr/local/python3.12 \
    && make -j$(nproc) \
    && make altinstall \
    && cd .. \
    && rm -rf Python-3.12.3.tgz Python-3.12.3

# Stage 2: Final minimal image
FROM debian:bookworm-slim AS oakapp

# Define build argument for architecture
ARG TARGETARCH

# Copy Python from builder stage
COPY --from=builder /usr/local/python3.12 /usr/local/python3.12

# Install runtime dependencies and create symlinks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libsqlite3-0 \
    libffi8 \
    libglib2.0-0 \
    zlib1g \
    ca-certificates \
    runit \
    nginx \
    openssl \
    wget \
    curl \
    jq \
    git \
    gettext \
    && ln -s /usr/local/python3.12/bin/python3.12 /usr/local/bin/python \
    && ln -s /usr/local/python3.12/bin/python3.12 /usr/local/bin/python3 \
    && ln -s /usr/local/python3.12/bin/python3.12 /usr/local/bin/python3.12 \
    && ln -s /usr/local/python3.12/bin/pip3.12 /usr/local/bin/pip \
    && ln -s /usr/local/python3.12/bin/pip3.12 /usr/local/bin/pip3

# Install DepthAI OS dependencies
RUN apt-get install -y libgl1 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Create service directories
RUN mkdir -p /etc/service/nginx /etc/service/oak_webrtc

# Add service run scripts
COPY services/nginx-run.sh /etc/service/nginx/run
COPY services/oak_webrtc-run.sh /etc/service/oak_webrtc/run
COPY services/connection-run.sh /etc/service/connection/run
RUN chmod +x /etc/service/nginx/run /etc/service/oak_webrtc/run etc/service/connection/run

# Add oak_webrtc binary
COPY oak_webrtc/$TARGETARCH/oak_webrtc /usr/local/bin/oak_webrtc 
RUN chmod +x /usr/local/bin/oak_webrtc 

# Configure nginx and SSL
COPY /nginx/setup.sh /tmp/setup_nginx.sh
RUN chmod +x /tmp/setup_nginx.sh && \
    /tmp/setup_nginx.sh && \
    rm /tmp/setup_nginx.sh
COPY /nginx/server.template /etc/nginx/sites-available/default
COPY /nginx/nginx.conf /etc/nginx/nginx.conf

# Start runit
CMD ["/usr/bin/runsvdir", "-P", "/etc/service"]