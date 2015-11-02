#!/bin/sh
cd /home/gruntworker/bootstrap-v4
flock -xn /var/lock/gruntworker-v4 /opt/gruntworker/gruntworker.py v4-dev
