#!/usr/bin/env python3
# coding=utf-8

from sys import exit  # pylint: disable=W0622
from subprocess import check_call, check_output, DEVNULL, CalledProcessError
from shutil import copy, rmtree
from os import remove
from os.path import join as pathjoin
from datetime import datetime

SHRINKWRAP_FILENAME = 'npm-shrinkwrap.json'
SHRINKWRAP_DIR = 'test-infra'
SHRINKWRAP_FILEPATH = pathjoin(SHRINKWRAP_DIR, SHRINKWRAP_FILENAME)


def log(*args):
    now = datetime.now().replace(microsecond=0).isoformat(' ')
    print(now, "gruntworker: ", end='')
    print(*args, flush=True)


def run_expecting_success(cmd):
    log("\trunning:", b' '.join(cmd).decode('utf8', 'replace'))
    check_call(cmd, stdin=DEVNULL)


def run_for_output(cmd):
    log("\trunning:", b' '.join(cmd).decode('utf8', 'replace'))
    return check_output(cmd, input=b'')


def reset_to_master_and_die():
    log("Attempting to reset current checkout & branch to local master...")
    try:
        run_expecting_success([b'git', b'checkout', b'-f', b'master'])
    except CalledProcessError:
        log("Error forcibly checking out master; Failed!")
    exit(1)


def fetch_origin():
    log("Fetching from origin...")
    try:
        run_expecting_success([b'git', b'fetch', b'origin', b'+master'])
    except CalledProcessError:
        log("Error fetching from origin; Failed!")
        exit(1)


def update_master(to_commitish=b'FETCH_HEAD'):
    log("Setting local master to {0}...".format(to_commitish.decode('utf8', 'replace')))
    try:
        run_expecting_success([b'git', b'checkout', b'-q', b'-f', to_commitish])
        run_expecting_success([b'git', b'branch', b'-f', b'master', to_commitish])
        run_expecting_success([b'git', b'checkout', b'-q', b'-f', b'master'])
    except CalledProcessError:
        log("Error setting local master to {0}!".format(to_commitish))
        reset_to_master_and_die()


def update_npm():
    try:
        copy(SHRINKWRAP_FILEPATH, SHRINKWRAP_FILENAME)
    except (OSError, IOError):
        log("Error copying shrinkwrap file into place!")
        log("Failed!")
        exit(1)

    try:
        log("Pruning unnecessary npm modules...")
        run_expecting_success([b'npm', b'prune'])
        log("Installing/updating npm modules per npm-shrinkwrap.json ...")
        run_expecting_success([b'npm', b'install'])
    except CalledProcessError:
        log("Error performing npm operations!")
        log("Purging node_modules due to errors.")
        try:
            rmtree('./node_modules', ignore_errors=True)
        except (IOError, OSError) as io_err:
            log("Error purging node_modules: {!r}".format(io_err))
        else:
            log("Successfully purged node_modules.")
        log("Failed!")
        exit(1)
    finally:
        try:
            remove(SHRINKWRAP_FILENAME)
        except:
            log("Error deleting copy of shrinkwrap file!")


def get_head_commit_sha():
    commit_sha = run_for_output([b'git', b'rev-parse', b'HEAD']).strip()
    if len(commit_sha) != 40:
        log("Got malformed commit SHA for HEAD:", commit_sha.decode('utf8'))
        log("Exiting due to insanity; Failed!")
        exit(1)
    return commit_sha


def grunt_or_err():
    log("Grunting...")
    try:
        run_expecting_success([b'grunt', b'dist', b'clean:docs', b'copy:docs'])
    except CalledProcessError:
        log("Error while grunting!")
        raise


def get_modified_files():
    output = run_for_output([b'git', b'status', b'-z', b'-uno', b'--ignore-submodules=all'])
    lines = output.split(b'\x00')
    return [line[3:] for line in lines if line[:2] == b' M']


def push_or_err():
    log("Pushing to origin...")
    try:
        run_expecting_success([b'git', b'push', b'origin', b'master'])
    except CalledProcessError:
        log("Error pushing to origin!")
        raise


def main():
    orig_commit_sha = get_head_commit_sha()
    fetch_origin()
    update_master()
    post_fetch_commit_sha = get_head_commit_sha()
    if post_fetch_commit_sha == orig_commit_sha:
        log("Fetch didn't change HEAD commit; Done.")
        return
    update_npm()
    try:
        grunt_or_err()
        modified_files = get_modified_files()
        if not modified_files:
            log("No files modified by grunt; Done.")
            return
        run_expecting_success([b'git', b'add', b'--'] + modified_files)
        run_expecting_success([b'git', b'commit', b'-m', b"automatic `grunt dist`"])
        push_or_err()
    except Exception:  # pylint: disable=W0703
        log("Resetting master branch & checkout back to commit {} ...".format(post_fetch_commit_sha))
        update_master(to_commitish=post_fetch_commit_sha)
        log("Failed!")
    else:
        log("Successfully pushed changes; Done.")


if __name__ == '__main__':
    main()
