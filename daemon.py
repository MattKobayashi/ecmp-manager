"""
Main daemon process for ECMP Manager.

This module implements the core control loop that:
- Monitors network interface health status
- Manages equal-cost multi-path (ECMP) routes via FRRouting
- Dynamically updates routing tables based on interface availability
- Handles configuration changes and service lifecycle events

The daemon continuously evaluates interface connectivity using health checks
and adjusts the routing table to maintain optimal network paths.
"""

import logging
import sys
from time import sleep
from frr import FRRClient
from kernel import KernelRoutingClient
from health_checks import is_interface_healthy
from config import load_config


def main_loop() -> None:
    """ECMP Manager's main control loop.

    Responsibilities:
    - Loads routing configuration from config.toml
    - Initializes routing client connection (FRRouting or Linux kernel)
    - Continuously monitors interface health:
      - Performs TCP connectivity checks
      - Maintains ECMP routes via configured routing backend
      - Adjusts routes based on interface status changes
    - Handles graceful shutdown on interrupt signals

    The loop runs indefinitely with sleep intervals determined by the
    smallest check_interval from all configured interfaces.

    Raises:
        SystemExit: On unrecoverable configuration or routing errors
    """

    config = load_config()

    # Configure logging based on config file
    log_level = getattr(logging, config.log_level, logging.INFO)
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting ECMP Manager daemon")

    # Initialize the appropriate routing client based on configuration
    try:
        if config.routing_backend == "kernel":
            logger.info("Using Linux kernel routing backend")
            routing_client = KernelRoutingClient()
        else:  # frr
            logger.info("Using FRRouting backend")
            routing_client = FRRClient()
    except RuntimeError as e:
        logger.critical(
            "%s service unavailable: %s",
            "Kernel routing" if config.routing_backend == "kernel" else "FRRouting",
            e,
        )
        if config.routing_backend == "frr":
            logger.critical("Verify FRR is installed and vtysh is in PATH")
        else:
            logger.critical(
                "Verify pyroute2 is installed and you have sufficient permissions"
            )
        sys.exit(1)

    try:
        while True:
            for interface in config.interfaces:
                try:
                    logger.debug("Checking interface %s", interface.name)
                    healthy, gateway_ip = is_interface_healthy(
                        interface,
                        check_ip=interface.target_ip,
                        check_port=80,
                        timeout=1,
                    )
                    if healthy and gateway_ip:
                        try:
                            routing_client.add_route(interface, gateway_ip)
                        except Exception as e:
                            logger.error(
                                "Route add failed for %s: %s", interface.name, str(e)
                            )
                    elif (
                        gateway_ip is not None
                    ):  # Only remove if we had a valid gateway
                        routing_client.remove_route(interface)
                except Exception as e:
                    logger.error(
                        "Interface check failed for %s: %s", interface.name, str(e)
                    )
                    continue  # Continue with next interface
            sleep(config.min_check_interval)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.critical("Fatal error: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main_loop()
