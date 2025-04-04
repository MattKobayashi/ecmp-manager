"""
Network interface configuration models and utilities.

This module provides:
- Interface configuration class for representing monitored network interfaces
- System interface discovery functionality
- Data structures for tracking interface properties and health check parameters

The Interface class encapsulates configuration settings needed for monitoring
and route management, including metric values and health check targets.
"""

import os


class Interface:
    """Represents a network interface configuration"""

    def __init__(self, name: str, metric: int,
                 check_interval: int, target_ip: str):
        self.name = name
        self.metric = metric
        self.check_interval = check_interval
        self.target_ip = target_ip
        self.gateway = None  # Dynamic gateway from health checks


def get_system_interfaces():
    """Get list of system network interfaces excluding loopback"""
    net_dir = '/sys/class/net'
    if os.path.exists(net_dir):
        return [iface for iface in os.listdir(net_dir)
                if iface != 'lo' and not iface.startswith('veth')]
    return []
