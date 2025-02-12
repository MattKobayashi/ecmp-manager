import logging
import subprocess

logger = logging.getLogger(__name__)


class FRRClient:
    def _execute_vty_command(self, command):
        """Log vtysh command execution details"""
        logger.debug("Executing FRR command: %r", command)
        try:
            subprocess.run(
                ["vtysh", "-c", command],
                check=True,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.debug("FRR command executed successfully")
        except subprocess.CalledProcessError as e:
            logger.debug(
                "FRR command failed with code %d. Error: %s",
                e.returncode,
                e.stderr.strip()
            )
            raise

    def add_route(self, interface):
        """Log route addition attempts and parameters"""
        logger.debug(
            "Attempting to add route for %s (GW: %s, Metric: %s)",
            interface.name,
            interface.gateway,
            interface.metric
        )
        if not interface.gateway:
            logger.debug(
                "Route addition failed - no gateway for %s",
                interface.name
            )
            raise ValueError(f"No gateway found for {interface.name}")

        self._execute_vty_command(
            f"configure terminal\n"
            f"ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )
        logger.debug(
            "Route successfully added for %s",
            interface.name
        )

    def remove_route(self, interface):
        """Log route removal attempts and validation"""
        if not interface.gateway:
            logger.debug(
                "Skipping removal for %s - no gateway configured",
                interface.name
            )
            return

        logger.debug(
            "Attempting to remove route for %s (GW: %s, Metric: %s)",
            interface.name,
            interface.gateway,
            interface.metric
        )
        self._execute_vty_command(
            f"configure terminal\n"
            f"no ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )
        logger.debug("Route successfully removed for %s", interface.name)
