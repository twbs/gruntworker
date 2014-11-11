#!/bin/sh
flock -xn /var/lock/gruntworker /app/gruntworker.py
