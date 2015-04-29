#!/bin/sh
flock -xn /var/lock/gruntworker /opt/gruntworker/gruntworker.py
