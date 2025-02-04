FROM debian:12-slim

# Install FRR and dependencies
RUN apt-get update \
    && apt-get --no-install-recommends --yes install frr iproute2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /var/log/ecmp-manager
COPY . .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

CMD ["python3", "-u", "daemon.py"]
