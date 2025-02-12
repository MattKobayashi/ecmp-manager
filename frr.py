import logging
import subprocess

logger = logging.getLogger(__name__)


class FRRClient:
    def __init__(self):
        self.installed_routes = {}  # Interface → (gateway_ip, metric)

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
        """Store route parameters when adding routes"""
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
        self.installed_routes[interface.name] = (gateway_ip, interface.metric)
        logger.debug(
            "Route successfully added for %s",
            interface.name
        )

    def remove_route(self, interface):
        """Only remove routes we actually added"""
        route_info = self.installed_routes.pop(interface.name, None)
        if not route_info:
            logger.debug("No route present for %s", interface.name)
            return
            
        gateway_ip, metric = route_info
        self._execute_vty_command(
            f"configure terminal\n"
            f"no ip route 0.0.0.0/0 {gateway_ip} {metric}"
        )
        logger.debug("Route successfully removed for %s", interface.name)
