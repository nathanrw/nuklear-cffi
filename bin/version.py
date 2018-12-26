"""
Script to update the version and do a release.

python version.py (--major|--minor|--patch)
"""


from __future__ import print_function


import re
import os
import sys
import subprocess


def main():

    # Figure out what sort of release we are doing.
    update_idx = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--major":
            print ("Doing a major release.")
            update_idx = 0
        elif arg == "--minor":
            print ("Doing a minor release.")
            update_idx = 1
        elif arg == "--patch":
            print ("Doing a patch release.")
            update_idx = 2
        else:
            error("Unknown argument:", arg)
        i += 1
    if update_idx is None:
        error("Must specify a release type: --major, --minor or --patch.")
            
    # Go into the repository directory.
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    try:
        os.chdir(root_dir)
    except:
        error("Failed to move into repository root:", root_dir)
    
    # Make sure we can run git.
    try:
        cmd("git", "version")
    except:
        error("Failed to run git.")
    
    # Make sure we don't accidentally commit changes.
    try:
        cmd("git", "diff-index", "--quiet", "--cached", "HEAD", "--")
    except subprocess.CalledProcessError:
        error("Changes already staged for commit.")
    
    # Read the version file.
    version = open("VERSION", "r").read().strip()
    version_match = re.search("([0-9])+\\.([0-9])+\\.([0-9]+)", version)
    if not version_match:
        error("Version file does not contain a version.")
    print ("Read version:", version)
    
    # Update the version and write the file.
    version_arr = [int(version_match.group(i)) for i in range(1, 4)]
    version_arr[update_idx] += 1
    for i in range(update_idx+1, len(version_arr)):
        version_arr[i] = 0
    next_version = ".".join([str(x) for x in version_arr])
    open("VERSION", "w").write(next_version)
    print ("Wrote version:", next_version)
    
    # Commit the change and add a tag
    cmd("git", "add", "VERSION")
    cmd("git", "commit", "-m", "'Update to version %s'" % next_version)
    cmd("git", "tag", "-a", "v"+next_version, "-m", "'Tag version %s'" % next_version)
    cmd("git", "push", "origin", "--tags")
    cmd("git", "push", "origin")
    
    
def cmd(*args):
    print ("$", *args)
    subprocess.check_call([x for x in args])
    
    
def error(*args):
    print ("ERROR:", *args)
    sys.exit(1)


if __name__ == '__main__':
    main()