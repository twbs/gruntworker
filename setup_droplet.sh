#!/bin/bash
# Step 0.0: Put SSH keys in ./ssh
# Step 0.1: Checkout git repo to ./git-repo

set -e -x

# set to Pacific Time (for @cvrebert)
# ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime

# remove useless crap
aptitude remove wpasupplicant wireless-tools
aptitude remove pppconfig pppoeconf ppp

# setup firewall
ufw default allow outgoing
ufw default deny incoming
ufw allow ssh
ufw allow www # not necessary for gruntworker itself
ufw enable
ufw status verbose

# setup Docker; written against Docker v1.2.0
docker rmi gruntworker
docker build --tag gruntworker . 2>&1 | tee docker.build.log
cp ./gruntworker.crontab /etc/cron.d/gruntworker
restart cron # until upstart goes away
