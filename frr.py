import logging
import subprocess

logger = logging.getLogger(__name__)


class FRRClient:
    def _execute_vty_command(self, command):
        """Log vtysh command execution details"""
        logger.debug(f"Executing FRR command: {command!r}")
        try:
            subprocess.run(
                ["vtysh", "-c", command],
                check=True,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.debug(f"FRR command executed successfully")
        except subprocess.CalledProcessError as e:
            logger.debug(f"FRR command failed with code {e.returncode}. Error: {e.stderr.strip()}")
            raise

    def add_route(self, interface):
        """Log route addition attempts and parameters"""
        logger.debug(f"Attempting to add route for {interface.name} (GW: {interface.gateway}, Metric: {interface.metric})")
        if not interface.gateway:
            logger.debug(f"Route addition failed - no gateway for {interface.name}")
            raise ValueError(f"No gateway found for {interface.name}")

        self._execute_vty_command(
            f"configure terminal\n"
            f"ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )
        logger.debug(f"Route successfully added for {interface.name}")

    def remove_route(self, interface):
        """Log route removal attempts and validation"""
        if not interface.gateway:
            logger.debug(f"Skipping removal for {interface.name} - no gateway configured")
            return

        logger.debug(f"Attempting to remove route for {interface.name} (GW: {interface.gateway}, Metric: {interface.metric})")
        self._execute_vty_command(
            f"configure terminal\n"
            f"no ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )
        logger.debug(f"Route successfully removed for {interface.name}")
