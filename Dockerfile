FROM debian:12-slim

# Install FRR and dependencies
RUN curl -s https://deb.frrouting.org/frr/keys.gpg | sudo tee /usr/share/keyrings/frrouting.gpg > /dev/null \
    && FRRVER="frr-9.1" echo deb '[signed-by=/usr/share/keyrings/frrouting.gpg]' https://deb.frrouting.org/frr \
        $(lsb_release -s -c) $FRRVER | sudo tee -a /etc/apt/sources.list.d/frr.list \
    && apt-get update \
    && apt-get --no-install-recommends --yes install frr frr-pythontools iproute2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /var/log/ecmp-manager
COPY config/config.toml ./config/
COPY . .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt \
    && chmod +x entrypoint.sh

CMD ["/app/entrypoint.sh"]
