#!/bin/bash
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
apt-get -y --no-install-recommends install openssh-client git python3 python3-dev # other dependencies
npm install -g grunt-cli # dependency
git clone git@github.com:twbs/gruntworker.git ~/gruntworker
mkdir -p /usr/local/bin
cp ~/gruntworker/gruntworker.sh /usr/local/bin/
cp ~/gruntworker/gruntworker.py /usr/local/bin/
chmod u=rwx,go=rx /usr/local/bin/gruntworker.*
useradd gruntworker

# setup SSH keys
su gruntworker # USER: gruntworker
mkdir ~/.ssh
ssh-keyscan -t rsa github.com > ~gruntworker/.ssh/known_hosts
# MANUAL STEP: Put SSH keys in /home/gruntworker/.ssh
chmod -R go-rwx ~/.ssh
# setup git & repo
git clone git@github.com:twbs/bootstrap.git ~/git-repo
cd ~/git-repo
git remote set-url origin https://github.com/twbs/bootstrap.git
git remote set-url --push origin git@github.com:twbs/bootstrap.git
git config core.fileMode false
git config user.name "Bootstrap's Grunt bot"
git config user.email 'twbs-grunt@users.noreply.github.com'
# setup Bootstrap
npm install

# setup cron
exit # USER: root
cp ~/gruntworker/gruntworker.crontab /etc/cron.d/gruntworker
restart cron # until upstart goes away
