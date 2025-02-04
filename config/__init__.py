import toml
from .interfaces import Interface

class Config:
    def __init__(self, interfaces):
        self.interfaces = interfaces
        self.min_check_interval = min(iface.check_interval for iface in interfaces)

def load_config():
    config_path = "config/config.toml"
    data = toml.load(config_path)

    interfaces = []
    # Look for interface tables using correct TOML structure
    interface_data = data.get("interface", {})
    
    for interface_name in interface_data:
        iface_data = interface_data[interface_name]
        interfaces.append(Interface(
            name=interface_name,
            metric=iface_data["metric"],
            check_interval=iface_data["check_interval"],
            target_ip=iface_data["target_ip"]
        ))

    if not interfaces:
        raise ValueError("No interfaces defined in config.toml")

    return Config(interfaces)
