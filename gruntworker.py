#!/usr/bin/env python3
# coding=utf-8

from sys import exit  # pylint: disable=W0622
from subprocess import check_call, check_output, DEVNULL, CalledProcessError
from shutil import copy, rmtree
from os import remove
from os.path import join as pathjoin, exists
from datetime import datetime

SHRINKWRAP_FILENAME = 'npm-shrinkwrap.json'
SHRINKWRAP_DIRS = ['test-infra', 'grunt']
SHRINKWRAP_FILEPATHS = [pathjoin(directory, SHRINKWRAP_FILENAME) for directory in SHRINKWRAP_DIRS]


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


def reset_to_primary_and_die(primary_branch):
    log("Attempting to reset current checkout & branch to local {}...".format(primary_branch))
    try:
        run_expecting_success([b'git', b'checkout', b'-f', primary_branch.encode('utf8')])
    except CalledProcessError:
        log("Error forcibly checking out {}; Failed!".format(primary_branch))
    exit(1)


def fetch_origin(primary_branch):
    log("Fetching from origin...")
    try:
        run_expecting_success([b'git', b'fetch', b'origin', ('+' + primary_branch).encode('utf8')])
    except CalledProcessError:
        log("Error fetching from origin; Failed!")
        exit(1)


def update_primary(primary_branch, to_commitish=b'FETCH_HEAD'):
    primary_bytes = primary_branch.encode('utf8')
    log("Setting local {0} to {1}...".format(primary_branch, to_commitish.decode('utf8', 'replace')))
    try:
        run_expecting_success([b'git', b'checkout', b'-q', b'-f', to_commitish])
        run_expecting_success([b'git', b'branch', b'-f', primary_bytes, to_commitish])
        run_expecting_success([b'git', b'checkout', b'-q', b'-f', primary_bytes])
    except CalledProcessError:
        log("Error setting local {0} to {1}!".format(primary_branch, to_commitish))
        reset_to_primary_and_die(primary_branch)


def update_npm():
    found = False
    shrinkwrap_filepath = None
    for shrinkwrap_filepath in SHRINKWRAP_FILEPATHS:
        if exists(shrinkwrap_filepath):
            found = True
            break
    if not found:
        log("No shrinkwrap file found!")
        log("Failed!")
        exit(1)
    try:
        copy(shrinkwrap_filepath, SHRINKWRAP_FILENAME)
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
        except Exception: # pylint: disable=W0703
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


def push_or_err(primary_branch):
    log("Pushing to origin...")
    try:
        run_expecting_success([b'git', b'push', b'origin', primary_branch.encode('utf8')])
    except CalledProcessError:
        log("Error pushing to origin!")
        raise


def main(primary_branch):
    orig_commit_sha = get_head_commit_sha()
    fetch_origin(primary_branch)
    update_primary(primary_branch)
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
        run_expecting_success([b'git', b'commit', b'-m', b"automatic `grunt dist`\n\n[ci skip]"])
        push_or_err(primary_branch)
    except Exception:  # pylint: disable=W0703
        log("Resetting primary branch & checkout back to commit {} ...".format(post_fetch_commit_sha))
        update_primary(primary_branch, to_commitish=post_fetch_commit_sha)
        log("Failed!")
    else:
        log("Successfully pushed changes; Done.")


if __name__ == '__main__':
    from sys import argv
    argv.pop()
    if len(argv) != 1:
        log("USAGE: gruntworker.py <primary-branch-name>")
        exit(2)
    main(argv[0])
