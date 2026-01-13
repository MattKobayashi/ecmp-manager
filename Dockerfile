FROM debian:13-slim@sha256:77ba0164de17b88dd0bf6cdc8f65569e6e5fa6cd256562998b62553134a00ef0

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
COPY config/ /app/config/
COPY *.lock *.py *.sh *.toml requirements.txt /app/
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt \
    && chmod +x entrypoint.sh

CMD ["/app/entrypoint.sh"]
