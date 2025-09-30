"""
Network interface health checking functionality.

This module provides utilities for checking interface connectivity and health by:
- Detecting gateway IP and MAC addresses from system neighbor tables
- Performing TCP connectivity checks to verify end-to-end connectivity
- Validating interface operational status

The health check implementation uses scapy to send targeted TCP SYN packets
through specific interfaces and gateways to verify route viability.
"""

import json
import logging
import os
import random
import subprocess
from typing import Optional
import ipaddress
import scapy.all as scapy
from scapy.error import Scapy_Exception

logger = logging.getLogger(__name__)


def get_gateway_info(interface) -> Optional[tuple[str, str]]:
    """Get gateway IP and MAC from neighbour table using ip command"""
    logger.debug("Querying neighbour table for interface %s", interface.name)
    try:
        result = subprocess.run(
            ["ip", "-json", "neighbour", "show", "dev", interface.name],
            capture_output=True,
            text=True,
            check=True,
        )
        neighbours = json.loads(result.stdout)

        # Find first IPv4 neighbour entry with valid MAC and state REACHABLE
        for entry in neighbours:
            dst_ip = entry.get("dst", "")
            if (
                dst_ip
                and is_valid_ipv4(dst_ip)
                and entry.get("lladdr")
                and entry.get("state") == "REACHABLE"
            ):
                logger.debug(
                    "Found gateway %s (%s) on %s",
                    dst_ip,
                    entry["lladdr"],
                    interface.name,
                )
                return (dst_ip, entry["lladdr"])

        logger.debug("No IPv4 gateway found in %d neighbour entries", len(neighbours))
        return (None, None)

    except (json.JSONDecodeError, subprocess.CalledProcessError) as e:
        logger.debug("Failed to get neighbour info: %s", str(e))
        return (None, None)


def is_valid_ipv4(address: str) -> bool:
    """Validate if a string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def is_interface_healthy(
    interface, check_ip: str = None, check_port: int = 80, timeout: int = 1
) -> tuple[bool, Optional[str]]:
    """Forced TCP connectivity test via interface's gateway"""
    # Check interface state first
    if not os.path.exists(f"/sys/class/net/{interface.name}/operstate"):
        logger.debug("Interface %s does not exist", interface.name)
        return (False, None)

    with open(f"/sys/class/net/{interface.name}/operstate", encoding="utf-8") as f:
        if f.read().strip() != "up":
            logger.debug("Interface %s is down", interface.name)
            return (False, None)

    # Get gateway info from single source
    gateway_ip, dest_mac = get_gateway_info(interface)

    if not all([gateway_ip, dest_mac]):
        logger.debug("No valid gateway info for %s", interface.name)
        return (False, None)

    if check_ip is None:
        check_ip = interface.target_ip

    logger.debug(
        "TCP check parameters - IP: %s, Port: %d, Timeout: %ds",
        check_ip,
        check_port,
        timeout,
    )
    try:
        syn_packet = (
            scapy.Ether(dst=dest_mac)
            / scapy.IP(dst=check_ip)
            / scapy.TCP(sport=random.randint(1024, 65535), dport=check_port, flags="S")
        )
        logger.debug(
            "Sending SYN packet to %s:%d via %s (MAC: %s)",
            check_ip,
            check_port,
            interface.name,
            dest_mac,
        )
        response = scapy.srp1(
            syn_packet, timeout=timeout, verbose=0, iface=interface.name, nofilter=True
        )
        if response:
            logger.debug("TCP response flags: %#04x", int(response[scapy.TCP].flags))
        else:
            logger.debug("No TCP response received")
        return (
            response
            and response.haslayer(scapy.TCP)
            and response[scapy.TCP].flags & 0x12 == 0x12,  # SYN-ACK
            gateway_ip,
        )
    except (Scapy_Exception, AttributeError, IndexError) as e:
        logger.debug(
            "TCP check failed - Dest: %s:%d, Interface: %s",
            check_ip,
            check_port,
            interface.name,
            exc_info=True,
        )
        logger.error("TCP health check failed for %s: %s", interface.name, str(e))
        return False
