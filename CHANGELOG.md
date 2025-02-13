# Changelog

## 1.0.0 (2025-02-13)


### Features

* Add auto-detection for system network interfaces ([cd90e81](https://github.com/MattKobayashi/ecmp-manager/commit/cd90e81265944f850655eec7b9fd2f15ec178ded))
* Add debug logging to FRRClient methods ([7e23ef2](https://github.com/MattKobayashi/ecmp-manager/commit/7e23ef2e560643d3fd57b9f3da0ec4978f58b969))
* Add detailed debug logging to network health checks ([af00d9a](https://github.com/MattKobayashi/ecmp-manager/commit/af00d9a9e926ae0bd4ccb09ed6e91a07e63dcc59))
* Add FRR service availability check during initialization ([#7](https://github.com/MattKobayashi/ecmp-manager/issues/7)) ([932a944](https://github.com/MattKobayashi/ecmp-manager/commit/932a94441a0008b73ccb89cb25b637961675c82d))


### Bug Fixes

* Add GHA workflows and renovate.json ([db2db1b](https://github.com/MattKobayashi/ecmp-manager/commit/db2db1bc06b4343c39c538f9090b9cf62528bd25))
* Add network error handling and interface state checks ([858b208](https://github.com/MattKobayashi/ecmp-manager/commit/858b208bf07c61efae8fb6fe04347f746ab73e8c))
* Convert Scapy TCP flags to int before hex formatting ([de86a7c](https://github.com/MattKobayashi/ecmp-manager/commit/de86a7cbd6a60f9246d872a5a6b86bb598fd56c4))
* Correct Dockerfile structure and module imports for runtime ([cc2afee](https://github.com/MattKobayashi/ecmp-manager/commit/cc2afee3b25f49f1ed8cf29e3f7ce3992191016c))
* Correct route removal logic to check for valid gateway IP ([bbe0cb6](https://github.com/MattKobayashi/ecmp-manager/commit/bbe0cb669443f329c993566593fe9f278743358d))
* correct TOML config parsing and add validation ([f4c3d9d](https://github.com/MattKobayashi/ecmp-manager/commit/f4c3d9dae613a42612dc980d4c3ec65cfc467c82))
* Ensure all return paths in is_interface_healthy return consistent tuple ([0c5ec82](https://github.com/MattKobayashi/ecmp-manager/commit/0c5ec8279913f42f62be18c31210004b1bf7a851))
* Fix config file path in container ([113de54](https://github.com/MattKobayashi/ecmp-manager/commit/113de5404e85dec6ee41d4061a53c5f4b44c69db))
* handle gateway detection and missing gateway errors ([de0ccfc](https://github.com/MattKobayashi/ecmp-manager/commit/de0ccfc9e703e7f8aff955acf0740155c75581db))
* Pass discovered gateway IP from health check to route addition ([792b476](https://github.com/MattKobayashi/ecmp-manager/commit/792b476aa38e373f6df71a121897db2b18e9b099))
* Replace deprecated scapy.utils.is_valid_ipv4 with ipaddress validation ([f207a59](https://github.com/MattKobayashi/ecmp-manager/commit/f207a599cca43a8fba91e32e1c3d8d0d281c3fe0))
* Track installed routes to ensure proper removal in FRRClient ([6d8a50e](https://github.com/MattKobayashi/ecmp-manager/commit/6d8a50e18a220596fbe9c615bb7f996a8a2b68c7))
* use python3 and add --break-system-packages to pip install ([de9e5bb](https://github.com/MattKobayashi/ecmp-manager/commit/de9e5bbc301b394c5570452e639a5e382a47cda8))
