# AGENTS.md

## Overview

Multi-WAN ECMP/failover daemon. Flat Python layout, no subpackages: `daemon.py` (entrypoint, control loop), `health_checks.py` (gateway discovery via `ip neigh` + scapy TCP-SYN probes to target:80), `frr.py` (vtysh backend), `kernel.py` (pyroute2 backend), `config/` (TOML loading). Backend is chosen in `[general] backend = "frr" | "kernel"`; if omitted the effective default is `"frr"` (config/**init**.py), not what the `Config` class signature suggests. `[interface.auto]` enables auto-discovery of system interfaces (excludes `lo` and `veth*`).

## Commands

- Package manager is **uv** (`uv.lock`); Python is pinned to 3.14 only (`>=3.14, <3.15`). Run `uv sync` to set up.
- Run the daemon: `uv run python -m daemon`. Config path comes from `ECMP_CONFIG_PATH` (default `config/config.toml`).
- Pre-commit hooks (gitleaks, shellcheck, end-of-file-fixer, trailing-whitespace): `pre-commit run --all-files`.
- There is no pytest, lint, or typecheck config in this repo. Do not invent such commands.

## Testing (Linux-only)

- `tests/` contains no unit tests — only TOML configs used by CI. The "tests" are the two integration jobs in `.github/workflows/test.yaml`, which run the real daemon and grep routing-table output: `vtysh -c "show ip route"` must contain `0.0.0.0/0 [10/0]` (FRR); `ip route show` must contain `metric 10 ` (kernel).
- Requires Linux + privileges: scapy probes need `CAP_NET_RAW`, the kernel backend needs `CAP_NET_ADMIN`/root, the FRR backend needs FRR running with `vtysh` in PATH. Health checks read `/sys/class/net/*/operstate`, so this does not run on macOS — local verification is limited to `uv run` import/syntax checks.
- Container test with kernel backend: `docker compose -f tests/docker-compose.yaml up` (grants NET_ADMIN/NET_RAW, mounts `tests/config_kernel.toml`).
- In CI the daemon-start steps are `continue-on-error: true`; the routing-table grep afterward is the real assertion.

## Dependency sync

Changing dependencies requires updating three files in lockstep:

1. `pyproject.toml` (source of truth for uv)
2. `uv.lock` (`uv lock` / `uv sync`)
3. `requirements.txt` — used only by the Dockerfile `pip install`, ignored by uv

## Conventions

- Commits follow Conventional Commits (`fix:`, `chore(deps):`, ...), merged via PRs.
- Renovate is active and pins actions/base images by digest — don't unpin; expect automated bump PRs.
- Docker image is Debian with FRR 9.1 from deb.frrouting.org; `entrypoint.sh` starts `watchfrr` before launching the daemon.
