# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "toml==0.10.2",
# ]
# ///

import os
import toml
from .interfaces import Interface, get_system_interfaces


class Config:
    """Represents the application's routing configuration.

    Attributes:
        interfaces: List[Interface] - Network interfaces being monitored
        min_check_interval: int - Smallest check interval from all interfaces
                                  (automatically calculated)
        routing_backend: str - Routing backend to use ("frr" or "kernel")
    """

    def __init__(self, interfaces, routing_backend="kernel"):
        self.interfaces = interfaces
        self.routing_backend = routing_backend
        self.min_check_interval = min(iface.check_interval for iface in interfaces)


def load_config():
    """Load and validate routing configuration from TOML file.

    The configuration file path can be specified via the ECMP_CONFIG_PATH
    environment variable. If not set, defaults to 'config/config.toml'.

    Returns:
        Config: Configured interfaces, check interval, and routing backend

    Raises:
        ValueError: For invalid configurations, including:
            - Invalid routing backend specified
            - Missing required parameters in [interface.auto]
            - No system interfaces found when using auto-config
            - No valid interfaces configured
        FileNotFoundError: If configuration file is missing

    Processes both explicitly configured interfaces and auto-detected system
    interfaces. Auto-configuration requires all interface parameters and will
    add any system interfaces not explicitly configured.
    """

    config_path = os.getenv("ECMP_CONFIG_PATH", "config/config.toml")
    data = toml.load(config_path)

    # Load routing backend configuration
    routing_config = data.get("routing", {})
    routing_backend = routing_config.get("backend", "frr")

    if routing_backend not in ("frr", "kernel"):
        raise ValueError(
            f"Invalid routing backend '{routing_backend}'. Must be 'frr' or 'kernel'"
        )

    interfaces = []
    interface_data = data.get("interface", {})
    auto_params = None

    # Process configuration entries
    for interface_name in interface_data:
        iface_data = interface_data[interface_name]

        if interface_name == "auto":
            # Validate auto configuration has all required parameters
            if not all(
                k in iface_data for k in ("metric", "check_interval", "target_ip")
            ):
                raise ValueError(
                    "Auto configuration requires metric, check_interval, and target_ip"
                )
            auto_params = iface_data
        else:
            # Existing interface processing
            interfaces.append(
                Interface(
                    name=interface_name,
                    metric=iface_data["metric"],
                    check_interval=iface_data["check_interval"],
                    target_ip=iface_data["target_ip"],
                )
            )

    # Add auto-detected interfaces if specified
    if auto_params is not None:
        system_ifaces = get_system_interfaces()
        if not system_ifaces:
            raise ValueError(
                "Auto configuration specified but no system interfaces found"
            )

        for iface_name in system_ifaces:
            # Skip interfaces already explicitly configured
            if not any(i.name == iface_name for i in interfaces):
                interfaces.append(
                    Interface(
                        name=iface_name,
                        metric=auto_params["metric"],
                        check_interval=auto_params["check_interval"],
                        target_ip=auto_params["target_ip"],
                    )
                )

    if not interfaces:
        raise ValueError(f"No interfaces defined in {config_path}")

    return Config(interfaces, routing_backend)
