"""
Network interface health checking functionality.

This module provides utilities for checking interface connectivity and health by:
- Detecting gateway IP and MAC addresses from system neighbour tables
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


def get_all_neighbours(interface) -> list[tuple[str, str]]:
    """Get all IPv4 neighbours (IP, MAC) from neighbour table using ip command"""
    logger.debug("Querying neighbour table for interface %s", interface.name)
    try:
        result = subprocess.run(
            ["ip", "-json", "neigh", "show", "dev", interface.name],
            capture_output=True,
            text=True,
            check=True,
        )
        neighbours_raw = json.loads(result.stdout)

        # Find all IPv4 neighbour entries with valid MAC
        neighbours = []
        for entry in neighbours_raw:
            dst_ip = entry.get("dst", "")
            if dst_ip and is_valid_ipv4(dst_ip) and entry.get("lladdr"):
                neighbours.append((dst_ip, entry["lladdr"]))
                logger.debug(
                    "Found neighbour %s (%s) on %s",
                    dst_ip,
                    entry["lladdr"],
                    interface.name,
                )

        logger.debug(
            "Found %d IPv4 neighbour(s) on %s",
            len(neighbours),
            interface.name,
        )
        return neighbours

    except (json.JSONDecodeError, subprocess.CalledProcessError) as e:
        logger.debug("Failed to get neighbour info: %s", str(e))
        return []


def is_valid_ipv4(address: str) -> bool:
    """Validate if a string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def test_connectivity_via_neighbour(
    interface,
    neighbour_ip: str,
    dest_mac: str,
    check_ip: str,
    check_port: int = 80,
    timeout: int = 1,
) -> bool:
    """Test connectivity through a specific neighbour by sending a TCP SYN packet"""
    logger.debug(
        "Testing connectivity via neighbour %s (MAC: %s) on %s to %s:%d",
        neighbour_ip,
        dest_mac,
        interface.name,
        check_ip,
        check_port,
    )
    try:
        syn_packet = (
            scapy.Ether(dst=dest_mac)
            / scapy.IP(dst=check_ip)
            / scapy.TCP(sport=random.randint(1024, 65535), dport=check_port, flags="S")
        )
        response = scapy.srp1(
            syn_packet, timeout=timeout, verbose=0, iface=interface.name, nofilter=True
        )

        if response:
            logger.debug("TCP response flags: %#04x", int(response[scapy.TCP].flags))
            # Check for SYN-ACK (flags = 0x12)
            if (
                response.haslayer(scapy.TCP)
                and response[scapy.TCP].flags & 0x12 == 0x12
            ):
                logger.info(
                    "Neighbour %s on %s successfully passed connectivity test",
                    neighbour_ip,
                    interface.name,
                )
                return True
        else:
            logger.debug("No TCP response received from neighbour %s", neighbour_ip)
        return False

    except (Scapy_Exception, AttributeError, IndexError) as e:
        logger.debug(
            "Connectivity test failed via neighbour %s: %s",
            neighbour_ip,
            str(e),
            exc_info=True,
        )
        return False


def is_interface_healthy(
    interface, check_ip: str = None, check_port: int = 80, timeout: int = 1
) -> tuple[bool, Optional[str]]:
    """
    Test interface health by attempting connectivity through each neighbour.

    Returns the first gateway that successfully passes the connectivity test.
    If the interface already has a gateway assigned, test that gateway first.
    """
    # Check interface state first
    if not os.path.exists(f"/sys/class/net/{interface.name}/operstate"):
        logger.debug("Interface %s does not exist", interface.name)
        return (False, None)

    with open(f"/sys/class/net/{interface.name}/operstate", encoding="utf-8") as f:
        if f.read().strip() != "up":
            logger.debug("Interface %s is down", interface.name)
            return (False, None)

    # Get all neighbours
    neighbours = get_all_neighbours(interface)

    if not neighbours:
        logger.debug("No neighbours for %s", interface.name)
        return (False, None)

    if check_ip is None:
        check_ip = interface.target_ip

    logger.debug(
        "TCP check parameters - IP: %s, Port: %d, Timeout: %ds",
        check_ip,
        check_port,
        timeout,
    )

    # If interface already has a gateway, test it first
    if interface.gateway:
        logger.debug("Testing existing gateway %s first", interface.gateway)
        for neighbour_ip, dest_mac in neighbours:
            if neighbour_ip == interface.gateway:
                if test_connectivity_via_neighbour(
                    interface, neighbour_ip, dest_mac, check_ip, check_port, timeout
                ):
                    return (True, neighbour_ip)
                logger.info(
                    "Existing gateway %s failed connectivity test, trying other neighbours",
                    interface.gateway,
                )
                break

    # Test each neighbour sequentially until one succeeds
    for neighbour_ip, dest_mac in neighbours:
        # Skip if this was the existing gateway (already tested above)
        if interface.gateway and neighbour_ip == interface.gateway:
            continue

        if test_connectivity_via_neighbour(
            interface, neighbour_ip, dest_mac, check_ip, check_port, timeout
        ):
            # Found a working gateway
            if interface.gateway != neighbour_ip:
                logger.info(
                    "Selected new gateway %s for interface %s",
                    neighbour_ip,
                    interface.name,
                )
            return (True, neighbour_ip)

    logger.debug(
        "No working gateway found for %s (tested %d neighbour(s))",
        interface.name,
        len(neighbours),
    )
    return (False, None)
