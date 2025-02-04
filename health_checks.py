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
    logger.debug(f"Querying default gateway for interface {interface} using 'ip route'")
    try:
        result = subprocess.run(
            ["ip", "-json", "route", "show", "dev", interface],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Raw ip route output: {result.stdout}")
        routes = json.loads(result.stdout)
        for route in routes:
            if route.get("dst") == "default":
                logger.debug(f"Found default gateway {route['gateway']} on {interface}")
                return route["gateway"]
        logger.debug(f"No default route in {len(routes)} routes found for {interface}")
        raise ValueError(f"No default route found for {interface}")
    except json.JSONDecodeError:
        logger.debug(f"Invalid JSON output from ip route: {result.stdout}", exc_info=True)
        raise RuntimeError("Failed to parse ip route output")
    except subprocess.CalledProcessError as e:
        logger.debug(f"Command failed: {e.cmd} (code {e.returncode}). Stderr: {e.stderr}")
        raise RuntimeError(f"Failed to get routes for {interface}: {e.stderr}") from e


def get_next_hop_mac(interface) -> Optional[str]:
    """Resolve gateway IP to MAC address using ARP"""
    try:
        logger.debug(f"Starting ARP resolution for {interface.name}")
        gateway_ip = get_default_gateway(interface.name)
        logger.debug(f"Sending ARP broadcast for {gateway_ip} via {interface.name}")
        ans, _ = scapy.srp(
            scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=gateway_ip),
            timeout=1,
            verbose=0,
            iface=interface.name,
        )
        if ans:
            logger.debug(f"ARP response received from {ans[0][1].hwsrc} (IP: {gateway_ip})")
        else:
            logger.debug(f"No ARP response received within timeout period for {gateway_ip}")
        return ans[0][1].hwsrc if ans else None
    except (Scapy_Exception, RuntimeError, ValueError, IndexError) as e:
        logger.debug(f"ARP exception details - Interface: {interface.name}, "
                     f"Gateway: {gateway_ip if 'gateway_ip' in locals() else 'Unknown'}", 
                     exc_info=True)
        logger.error(f"ARP resolution failed for {interface.name}: {str(e)}")
        return None


def is_interface_healthy(
    interface,
    check_ip: str = None,
    check_port: int = 80,
    timeout: int = 1
) -> bool:
    """Forced TCP connectivity test via interface's gateway"""
    try:
        logger.debug(f"Starting health check for {interface.name} (target IP: {check_ip})")
        interface.gateway = get_default_gateway(interface.name)
        logger.debug(f"Resolved gateway {interface.gateway} for {interface.name}")
    except (RuntimeError, ValueError):
        logger.debug(f"Gateway resolution failed for {interface.name}", exc_info=True)
        return False

    logger.debug(f"Testing next hop MAC for interface {interface.name}")
    if (dest_mac := get_next_hop_mac(interface)) is None:
        logger.debug(f"Aborting health check - no next hop MAC for {interface.name}")
        return False

    if check_ip is None:
        check_ip = interface.target_ip

    logger.debug(f"TCP check parameters - IP: {check_ip}, Port: {check_port}, Timeout: {timeout}s")
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
        logger.debug(f"Sending SYN packet to {check_ip}:{check_port} via {interface.name} "
                    f"(MAC: {dest_mac})")
        response = scapy.srp1(
            syn_packet,
            timeout=timeout,
            verbose=0,
            iface=interface.name,
            nofilter=True
        )
        logger.debug(f"TCP response flags: {int(response[scapy.TCP].flags):#04x}" if response 
                    else "No TCP response received")
        return (
            response and
            response.haslayer(scapy.TCP) and
            response[scapy.TCP].flags & 0x12 == 0x12  # SYN-ACK
        )
    except (Scapy_Exception, AttributeError, IndexError) as e:
        logger.debug(f"TCP check failed - Dest: {check_ip}:{check_port}, Interface: {interface.name}",
                    exc_info=True)
        logger.error(f"TCP health check failed for {interface.name}: {str(e)}")
        return False
