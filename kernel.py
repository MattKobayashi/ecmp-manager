"""
Linux kernel routing integration for managing dynamic routes.

This module provides a client interface to the Linux kernel routing table for:
- Adding and removing default routes with specific metrics
- Tracking installed routes to ensure proper cleanup
- Validating system capabilities for kernel route management

Commands are executed through the PyRoute2 library to make route changes
directly in the kernel routing table without requiring an external routing daemon.
"""

import logging
from pyroute2 import IPRoute

logger = logging.getLogger(__name__)


class KernelRoutingClient:
    def __init__(self):
        self.installed_routes = {}  # Interface → (gateway_ip, metric)
        if not self.check_kernel_routing():
            raise RuntimeError("Failed to initialize kernel routing client")

    def check_kernel_routing(self) -> bool:
        """Verify kernel routing is operational by testing IPRoute connection"""
        try:
            with IPRoute() as ipr:
                # Test basic connectivity by listing routes
                list(ipr.get_routes())
            logger.info("Kernel routing connection validated")
            return True
        except Exception as e:
            logger.error("Kernel routing connection failed - Error: %s", str(e))
            return False

    def add_route(self, interface, gateway_ip: str):
        """Add or update route, removing old route if gateway changed"""
        logger.debug(
            "Attempting to add route for %s (GW: %s, Metric: %s)",
            interface.name,
            gateway_ip,
            interface.metric,
        )

        # Check if route exists with different gateway
        existing_route = self.installed_routes.get(interface.name)
        if existing_route:
            existing_gateway, existing_metric = existing_route
            if existing_gateway != gateway_ip:
                logger.info(
                    "Gateway changed for %s from %s to %s, updating route",
                    interface.name,
                    existing_gateway,
                    gateway_ip,
                )
                # Remove old route first
                try:
                    with IPRoute() as ipr:
                        idx = ipr.link_lookup(ifname=interface.name)
                        if idx:
                            ipr.route(
                                "del",
                                dst="0.0.0.0",
                                mask=0,
                                gateway=existing_gateway,
                                oif=idx[0],
                                priority=existing_metric,
                            )
                except Exception as e:
                    logger.debug(
                        "Failed to remove old route (may not exist): %s", str(e)
                    )

        try:
            with IPRoute() as ipr:
                # Get the interface index
                idx = ipr.link_lookup(ifname=interface.name)
                if not idx:
                    raise RuntimeError(f"Interface {interface.name} not found")

                # Add default route (0.0.0.0/0)
                ipr.route(
                    "add",
                    dst="0.0.0.0",
                    mask=0,
                    gateway=gateway_ip,
                    oif=idx[0],
                    priority=interface.metric,
                )

            self.installed_routes[interface.name] = (gateway_ip, interface.metric)
            logger.debug("Route successfully added for %s", interface.name)
        except Exception as e:
            # Route might already exist, check if we need to replace it
            if "File exists" in str(e):
                logger.debug(
                    "Route already exists for %s, updating tracking", interface.name
                )
                self.installed_routes[interface.name] = (gateway_ip, interface.metric)
            else:
                logger.error("Failed to add route for %s: %s", interface.name, str(e))
                raise

    def remove_route(self, interface):
        """Remove a default route from the kernel routing table"""
        route_info = self.installed_routes.pop(interface.name, None)
        if not route_info:
            logger.debug("No route present for %s", interface.name)
            return

        gateway_ip, metric = route_info

        try:
            with IPRoute() as ipr:
                # Get the interface index
                idx = ipr.link_lookup(ifname=interface.name)
                if not idx:
                    logger.warning(
                        "Interface %s not found, cannot remove route", interface.name
                    )
                    return

                # Remove default route (0.0.0.0/0)
                ipr.route(
                    "del",
                    dst="0.0.0.0",
                    mask=0,
                    gateway=gateway_ip,
                    oif=idx[0],
                    priority=metric,
                )

            logger.debug("Route successfully removed for %s", interface.name)
        except Exception as e:
            logger.error("Failed to remove route for %s: %s", interface.name, str(e))
            # Don't raise - route might already be gone
