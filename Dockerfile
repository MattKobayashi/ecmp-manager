FROM debian:13-slim@sha256:c85a2732e97694ea77237c61304b3bb410e0e961dd6ee945997a06c788c545bb

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
