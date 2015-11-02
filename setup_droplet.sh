#!/bin/bash
# Step 0.0: Put SSH keys in ./ssh
# Step 0.1: Checkout git repo to /opt/gruntworker/git-repo

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

# install Node.js
aptitude install build-essential # for native addons
curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
DISTRO=$(lsb_release -c -s)
echo 'deb https://deb.nodesource.com/node_5.x ${DISTRO} main'      > /etc/apt/sources.list.d/nodesource.list
echo 'deb-src https://deb.nodesource.com/node_5.x ${DISTRO} main' >> /etc/apt/sources.list.d/nodesource.list
aptitude update
aptitude install nodejs
aptitude install nodejs-legacy # out of compatibility paranoia, though I philosophically agree with Debian here

# setup gruntworker itself
cp ./gruntworker.crontab /etc/cron.d/gruntworker
restart cron # until upstart goes away
