FROM debian:13-slim@sha256:def4126bd4619cd54d179f12ed9eb5438cd7b897e9cf523b5a3d3488274ed8aa

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
