import toml
from .interfaces import Interface

class Config:
    def __init__(self, interfaces):
        self.interfaces = interfaces
        self.min_check_interval = min(iface.check_interval for iface in interfaces)

def load_config():
    config_path = "config.toml"
    data = toml.load(config_path)

    interfaces = []
    for section in data:
        if section.startswith("interface."):
            interface_name = section.split(".")[1]
            iface_data = data[section]

            interfaces.append(Interface(
                name=interface_name,
                metric=iface_data["metric"],
                if_type=iface_data["type"],
                check_interval=iface_data["check_interval"],
                target_ip=iface_data["target_ip"]
            ))

    return Config(interfaces)
