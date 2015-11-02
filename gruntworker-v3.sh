#!/bin/sh
cd /home/gruntworker/bootstrap-v3
flock -xn /var/lock/gruntworker-v3 /opt/gruntworker/gruntworker.py master
