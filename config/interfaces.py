class Interface:
    """Represents a network interface configuration"""

    def __init__(self, name: str, metric: int,
                 if_type: str, check_interval: int, target_ip: str):
        self.name = name
        self.metric = metric
        self.if_type = if_type  # "dhcp" or "pppoe"
        self.check_interval = check_interval
        self.target_ip = target_ip
        self.gateway = None  # Dynamic gateway from health checks
