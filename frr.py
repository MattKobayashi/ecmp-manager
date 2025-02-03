import subprocess


class FRRClient:
    def _execute_vty_command(self, command):
        subprocess.run(
            ["vtysh", "-c", command],
            check=True
        )

    def add_route(self, interface):
        self._execute_vty_command(
            f"configure terminal\n"
            f"ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )

    def remove_route(self, interface):
        self._execute_vty_command(
            f"configure terminal\n"
            f"no ip route 0.0.0.0/0 {interface.gateway} {interface.metric}"
        )
