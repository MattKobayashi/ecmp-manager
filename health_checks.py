import json
import logging
import random
import subprocess
from typing import Optional
import scapy.all as scapy
from scapy.error import Scapy_Exception

logger = logging.getLogger(__name__)


def get_default_gateway(interface: str) -> str:
    """Get the default gateway IP for a specific interface using ip route"""
    try:
        result = subprocess.run(
            ["ip", "-json", "route", "show", "dev", interface],
            capture_output=True,
            text=True,
            check=True
        )
        routes = json.loads(result.stdout)
        for route in routes:
            if route.get("dst") == "default":
                return route["gateway"]
        raise ValueError(f"No default route found for {interface}")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse ip route output")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get routes for {interface}: {e.stderr}") from e


def get_next_hop_mac(interface) -> Optional[str]:
    """Resolve gateway IP to MAC address using ARP"""
    try:
        # Get dynamic gateway first
        gateway_ip = get_default_gateway(interface.name)
        ans, _ = scapy.srp(
            scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=gateway_ip),
            timeout=1,
            verbose=0,
            iface=interface.name,
        )
        return ans[0][1].hwsrc if ans else None
    except (Scapy_Exception, RuntimeError, ValueError, IndexError) as e:
        logger.error(f"ARP resolution failed for {interface.name}: {str(e)}")
        return None


def is_interface_healthy(
    interface,
    check_ip: str = None,
    check_port: int = 80,
    timeout: int = 2
) -> bool:
    """Forced TCP connectivity test via interface's gateway"""
    try:
        get_default_gateway(interface.name)
    except (RuntimeError, ValueError):
        return False

    if (dest_mac := get_next_hop_mac(interface)) is None:
        return False

    if check_ip is None:
        check_ip = interface.target_ip

    try:
        syn_packet = (
            scapy.Ether(dst=dest_mac)/
            scapy.IP(dst=check_ip)/
            scapy.TCP(
                sport=random.randint(1024, 65535),
                dport=check_port,
                flags="S"
            )
        )
        response = scapy.srp1(
            syn_packet,
            timeout=timeout,
            verbose=0,
            iface=interface.name,
            nofilter=True
        )
        return (
            response and
            response.haslayer(scapy.TCP) and
            response[scapy.TCP].flags & 0x12 == 0x12  # SYN-ACK
        )
    except (Scapy_Exception, AttributeError, IndexError) as e:
        logger.error(f"TCP health check failed for {interface.name}: {str(e)}")
        return False
