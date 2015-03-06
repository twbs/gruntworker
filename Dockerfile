# Written against Docker v1.3.1
FROM node:0.10
MAINTAINER Chris Rebert <code@rebertia.com>

WORKDIR /

ENV DEBIAN_FRONTEND noninteractive
RUN ["apt-get", "update"]
RUN ["apt-get", "-y", "install", "apt-utils"]
RUN ["apt-get", "-y", "--no-install-recommends", "install", "build-essential", "openssh-client", "git", "python3", "python3-dev"]
# Grunt
RUN ["npm", "install", "-g", "grunt-cli"]

RUN ["useradd", "gruntworker"]

ADD gruntworker.py /app/gruntworker.py
ADD gruntworker.sh /app/gruntworker.sh
ADD git-repo /git-repo

# Setup SSH keys
ADD ssh/id_rsa.pub /home/gruntworker/.ssh/id_rsa.pub
ADD ssh/id_rsa /home/gruntworker/.ssh/id_rsa
RUN ssh-keyscan -t rsa github.com > /home/gruntworker/.ssh/known_hosts

# Fix permissions
RUN ["chown", "-R", "gruntworker:gruntworker", "/git-repo"]
RUN ["chown", "-R", "gruntworker:gruntworker", "/home/gruntworker"]
# chmod must happen AFTER chown, due to https://github.com/docker/docker/issues/6047
RUN ["chmod", "-R", "go-rwx", "/home/gruntworker/.ssh"]

USER gruntworker
WORKDIR /git-repo

RUN ["git", "remote", "set-url",           "origin", "https://github.com/twbs/bootstrap.git"]
RUN ["git", "remote", "set-url", "--push", "origin", "git@github.com:twbs/bootstrap.git"]
RUN ["git", "config", "core.fileMode", "false"]
RUN ["git", "config", "user.name", "Bootstrap's Grunt bot"]
RUN ["git", "config", "user.email", "twbs-grunt@users.noreply.github.com"]
RUN ["npm", "install"]

ENTRYPOINT ["/app/gruntworker.sh"]
