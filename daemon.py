import logging.config
from time import sleep
from frr import FRRClient
from health_checks import is_interface_healthy
from config import load_config


def main_loop():
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger(__name__)
    logger.info("Starting ECMP Manager daemon")

    config = load_config()
    frr = FRRClient()

    try:
        while True:
            for interface in config.interfaces:
                logger.debug(f"Checking interface {interface.name}")
                if is_interface_healthy(
                    interface,
                    check_ip=interface.target_ip,
                    check_port=80,
                    timeout=1
                ):
                    frr.add_route(interface)
                else:
                    frr.remove_route(interface)
            sleep(config.min_check_interval)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main_loop()
