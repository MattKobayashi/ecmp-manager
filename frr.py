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

    def add_route(self, interface, gateway_ip: str):
        """Log route addition attempts and parameters"""
        logger.debug(
            "Attempting to add route for %s (GW: %s, Metric: %s)",
            interface.name,
            gateway_ip,
            interface.metric
        )
        self._execute_vty_command(
            f"configure terminal\n"
            f"ip route 0.0.0.0/0 {gateway_ip} {interface.metric}"
        )
        logger.debug(
            "Route successfully added for %s",
            interface.name
        )

    def remove_route(self, interface):
        """Log route removal attempts and validation"""

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
