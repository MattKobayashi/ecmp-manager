import logging
from time import sleep
from frr import FRRClient
from health_checks import is_interface_healthy
from config import load_config


def main_loop() -> None:
    """ECMP Manager's main control loop.

    Responsibilities:
    - Loads routing configuration from config.toml
    - Initializes FRRouting client connection
    - Continuously monitors interface health:
      - Performs TCP connectivity checks
      - Maintains ECMP routes via FRRouting
      - Adjusts routes based on interface status changes
    - Handles graceful shutdown on interrupt signals

    The loop runs indefinitely with sleep intervals determined by the
    smallest check_interval from all configured interfaces.

    Raises:
        SystemExit: On unrecoverable configuration or routing errors
    """

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Starting ECMP Manager daemon")

    config = load_config()
    frr = FRRClient()

    try:
        while True:
            for interface in config.interfaces:
                try:
                    logger.debug("Checking interface %s", interface.name)
                    healthy, gateway_ip = is_interface_healthy(
                        interface,
                        check_ip=interface.target_ip,
                        check_port=80,
                        timeout=1
                    )
                    if healthy and gateway_ip:
                        try:
                            frr.add_route(interface, gateway_ip)
                        except Exception as e:
                            logger.error(
                                "Route add failed for %s: %s",
                                interface.name,
                                str(e)
                            )
                    elif gateway_ip is not None:  # Only remove if we had a valid gateway
                        frr.remove_route(interface)
                except Exception as e:
                    logger.error(
                        "Interface check failed for %s: %s",
                        interface.name,
                        str(e)
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
