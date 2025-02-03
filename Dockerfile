FROM python:3.12-slim

# Install FRR and dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends frr curl iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /var/log/ecmp-manager && \
    chown -R 1000:1000 /var/log/ecmp-manager
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY logging.ini /app/logging.ini

CMD ["python", "-u", "daemon.py"]
