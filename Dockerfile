FROM debian:12-slim

# Install FRR and dependencies
RUN apt-get update \
    && apt-get --no-install-recommends --yes install frr iproute2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /var/log/ecmp-manager \
    && mkdir -p config/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY requirements.txt .
COPY logging.ini .
COPY config/* config/

CMD ["python", "-u", "daemon.py"]
