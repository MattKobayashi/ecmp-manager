# ecmp-manager

Multi-WAN ECMP and failover with support for FRRouting or Linux kernel routing.

## Features

- Multi-WAN health monitoring with configurable checks
- ECMP and failover using FRRouting (FRR) or Linux kernel routing
- Flexible routing backend selection via configuration
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

### Environment Variables

- `ECMP_CONFIG_PATH`: Path to the configuration file (default: `config/config.toml`)

### Configuration File

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

[routing]
backend = "kernel"
# backend = "frr"
```

### Routing Backend Options

**FRRouting (frr):**

- Uses FRRouting daemon for route management
- Requires FRRouting to be installed and running
- Routes managed via `vtysh` command interface
- Best for complex routing scenarios and BGP integration

**Linux Kernel (kernel):**

- Uses Linux kernel routing table directly
- Requires `pyroute2` Python library (installed automatically)
- No external routing daemon needed
- Simpler setup for basic ECMP scenarios

### Requirements

Common requirements:

- Interface names must match system interfaces (`ip link show`)
- Valid IP address for `target_ip` that allows connections to TCP port 80
- Metric values between 1-255

Backend-specific requirements:

- **FRR backend**: FRRouting must be installed and working on the system
- **Kernel backend**: Sufficient permissions to modify routing table (typically root)

## Usage

### Local Execution

```bash
# Start daemon in background
uv run python -m daemon

# Foreground mode with debug output
uv run python -m daemon --foreground

# Use custom config path
ECMP_CONFIG_PATH=/etc/ecmp/config.toml uv run python -m daemon
```

### Verify Routes

**FRR backend:**

```bash
vtysh -c "show ip route"
```

**Kernel backend:**

```bash
ip route show
```

## Troubleshooting

### Common Issues

- Interface names in config don't match system interfaces
- Missing health check target IP connectivity
- Insufficient permissions to modify routing table

### FRR Backend Issues

- `vtysh` not in PATH or permissions issues
- FRR not running/installed

```bash
# Validate FRR connectivity
vtysh -c "show running-config"
```

### Kernel Backend Issues

- Insufficient permissions (requires root or appropriate capabilities)
- `pyroute2` library not installed

```bash
# Verify routing permissions
ip route add 192.0.2.1 via 192.0.2.254 metric 999 # Should not error
ip route del 192.0.2.1 via 192.0.2.254 metric 999
```

## License

See [LICENSE](LICENSE)
