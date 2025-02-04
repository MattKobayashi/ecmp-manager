#!/bin/bash
source /usr/lib/frr/frrcommon.sh
/usr/lib/frr/watchfrr $(daemon_list) &
/usr/bin/python3 -u daemon.py
