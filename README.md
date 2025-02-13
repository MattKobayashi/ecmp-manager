# Network Interface Management Daemon

Dynamic routing daemon that monitors interface health and manages FRR (FRRouting) default routes.

## Features

- Interface health monitoring with configurable checks
- Automatic failover using FRRouting (FRR)
- TOML configuration for interface priority and check parameters
- Docker container support with health checks
- Route persistence tracking and cleanup

## Installation

```bash
# Install Poetry if not already present
curl -sSL https://install.python-poetry.org | python3 -

# Clone and setup
git clone https://github.com/yourusername/network-daemon.git
cd network-daemon
poetry install
```

## Configuration

Edit `config/config.toml` following this pattern:

```toml
[interface.eth0]
check_interval = 5    # Seconds between health checks
target_ip = "1.1.1.1" # IP for connectivity checks
metric = 100          # Lower metrics have priority

[interface.eth1]
check_interval = 5
target_ip = "8.8.8.8" 
metric = 200
```

Requirements:
- Interface names must match system interfaces (`ip link show`)
- Valid IP addresses for `target_ip`
- Metric values between 1-255

## FRR Requirements
```bash
# Ubuntu/Debian example
sudo apt install frr
sudo usermod -aG frr $USER
sudo sysctl -w net.ipv4.ip_forward=1
```

## Usage

### Local Execution
```bash
# Start daemon in background
poetry run python -m daemon

# Foreground mode with debug output
poetry run python -m daemon --foreground
```

### Docker
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Verify Routes
```bash
vtysh -c "show ip route"
```

## Troubleshooting

Common Issues:
- `vtysh` not in PATH or permissions issues
- Interface names in config don't match system interfaces
- FRR not running/installed
- Missing health check target IP connectivity

```bash
# Check daemon logs
journalctl -u your-service-name

# Validate FRR connectivity
vtysh -c "show running-config"
```

## License
MIT License - See [LICENSE](LICENSE)
