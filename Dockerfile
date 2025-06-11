FROM debian:12-slim@sha256:e5865e6858dacc255bead044a7f2d0ad8c362433cfaa5acefb670c1edf54dfef

# Install FRR and dependencies
RUN apt-get update \
    && apt-get --no-install-recommends --yes install ca-certificates \
    && echo deb '[trusted=yes]' https://deb.frrouting.org/frr \
        bookworm frr-9.1 | tee -a /etc/apt/sources.list.d/frr.list \
    && apt-get update \
    && apt-get --no-install-recommends --yes install frr frr-pythontools iproute2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /var/log/ecmp-manager \
    && mkdir -p /var/run/frr \
    && chown -R frr:frr /var/run/frr
COPY . .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt \
    && chmod +x entrypoint.sh

CMD ["/app/entrypoint.sh"]
