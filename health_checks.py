import json
import logging
import os
import random
import subprocess
from typing import Optional
import scapy.all as scapy
from scapy.error import Scapy_Exception

logger = logging.getLogger(__name__)


def get_default_gateway(interface: str) -> str:
    """Get the default gateway IP for a specific interface using ip route"""
    logger.debug("Querying default gateway for interface %s using 'ip route'", interface)
    try:
        result = subprocess.run(
            ["ip", "-json", "route", "show", "dev", interface],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug("Raw ip route output: %s", result.stdout)
        routes = json.loads(result.stdout)
        for route in routes:
            if route.get("dst") == "default":
                logger.debug("Found default gateway %s on %s", route['gateway'], interface)
                return route["gateway"]
        logger.debug("No default route in %d routes found for %s", len(routes), interface)
    except json.JSONDecodeError:
        logger.debug("Invalid JSON output from ip route: %s", result.stdout, exc_info=True)
        raise RuntimeError("Failed to parse ip route output")
    except subprocess.CalledProcessError as e:
        logger.debug("Command failed: %s (code %d). Stderr: %s", e.cmd, e.returncode, e.stderr)
        raise RuntimeError(f"Failed to get routes for {interface}: {e.stderr}") from e


def get_next_hop_mac(interface) -> Optional[str]:
    """Resolve gateway IP to MAC address using ARP"""
    try:
        # First check if interface exists and is up
        if not os.path.exists(f'/sys/class/net/{interface.name}/operstate'):
            logger.warning(f"Interface {interface.name} does not exist")
            return None
            
        with open(f'/sys/class/net/{interface.name}/operstate') as f:
            if f.read().strip() != 'up':
                logger.warning(f"Interface {interface.name} is down")
                return None

        logger.debug("Starting ARP resolution for %s", interface.name)
        gateway_ip = get_default_gateway(interface.name)
        logger.debug("Sending ARP broadcast for %s via %s", gateway_ip, interface.name)
        
        ans, _ = scapy.srp(
            scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=gateway_ip),
            timeout=2,
            verbose=0,
            iface=interface.name,
            retry=1
        )
        if ans:
            logger.debug("ARP response received from %s (IP: %s)", ans[0][1].hwsrc, gateway_ip)
        else:
            logger.debug("No ARP response received within timeout period for %s", gateway_ip)
        return ans[0][1].hwsrc if ans else None
    except OSError as e:
        logger.warning(f"Network error on {interface.name}: {str(e)}")
        return None
    except (Scapy_Exception, RuntimeError, ValueError, IndexError) as e:
        logger.debug("ARP exception details - Interface: %s, Gateway: %s", 
                    interface.name, locals().get('gateway_ip', 'Unknown'), 
                    exc_info=True)
        logger.error("ARP resolution failed for %s: %s", interface.name, str(e))
        return None


def is_interface_healthy(
    interface,
    check_ip: str = None,
    check_port: int = 80,
    timeout: int = 1
) -> bool:
    """Forced TCP connectivity test via interface's gateway"""
    try:
        logger.debug("Starting health check for %s (target IP: %s)", interface.name, check_ip)
        interface.gateway = get_default_gateway(interface.name)
        logger.debug("Resolved gateway %s for %s", interface.gateway, interface.name)
    except (RuntimeError, ValueError):
        logger.debug("Gateway resolution failed for %s", interface.name, exc_info=True)
        return False

    logger.debug("Testing next hop MAC for interface %s", interface.name)
    if (dest_mac := get_next_hop_mac(interface)) is None:
        logger.debug("Aborting health check - no next hop MAC for %s", interface.name)
        return False

    if check_ip is None:
        check_ip = interface.target_ip

    logger.debug("TCP check parameters - IP: %s, Port: %d, Timeout: %ds", check_ip, check_port, timeout)
    try:
        syn_packet = (
            scapy.Ether(dst=dest_mac) /
            scapy.IP(dst=check_ip) /
            scapy.TCP(
                sport=random.randint(1024, 65535),
                dport=check_port,
                flags="S"
            )
        )
        logger.debug("Sending SYN packet to %s:%d via %s (MAC: %s)", 
                    check_ip, check_port, interface.name, dest_mac)
        response = scapy.srp1(
            syn_packet,
            timeout=timeout,
            verbose=0,
            iface=interface.name,
            nofilter=True
        )
        if response:
            logger.debug("TCP response flags: %#04x", int(response[scapy.TCP].flags))
        else:
            logger.debug("No TCP response received")
        return (
            response and
            response.haslayer(scapy.TCP) and
            response[scapy.TCP].flags & 0x12 == 0x12  # SYN-ACK
        )
    except (Scapy_Exception, AttributeError, IndexError) as e:
        logger.debug("TCP check failed - Dest: %s:%d, Interface: %s",
                    check_ip, check_port, interface.name, exc_info=True)
        logger.error("TCP health check failed for %s: %s", interface.name, str(e))
        return False
