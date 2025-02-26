# ecmp-manager

Multi-WAN ECMP and failover for FRRouting.

## Features

- Multi-WAN health monitoring with configurable checks
- ECMP and failover using FRRouting (FRR)
- TOML configuration for interface and check parameters
- Route persistence tracking and cleanup

## Installation

```bash
# Install pipx if not already present
sudo apt install pipx
pipx ensurepath

# Install uv
pipx install uv

# Clone and setup
git clone https://github.com/MattKobayashi/ecmp-manager.git
cd ecmp-manager
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

- FRRouting must already be installed and working on the system
- Interface names must match system interfaces (`ip link show`)
- Valid IP address for `target_ip` that allows connections to TCP port 80
- Metric values between 1-255

## Usage

### Local Execution

```bash
# Start daemon in background
uv run python -m daemon

# Foreground mode with debug output
uv run python -m daemon --foreground
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
# Validate FRR connectivity
vtysh -c "show running-config"
```

## License

See [LICENSE](LICENSE)
