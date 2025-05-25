#!/usr/bin/env python


import sys
import re
import os
from git import Repo

def get_changed_files(repo, base_branch, pr_branch):
    repo.git.fetch('origin', base_branch)
    diff = repo.git.diff('--name-only', f'origin/{base_branch}..{pr_branch}')
    return diff.strip().splitlines()

def extract_version_from_cmake(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    match = re.search(r'project\([^)]*VERSION\s+([0-9]+\.[0-9]+\.[0-9]+)', content, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def is_valid_version(version):
    return re.match(r'^v?\d+\.\d+\.\d+$', version) is not None

def tag_exists(repo, version):
    repo.git.fetch('--tags')
    return version in [t.name for t in repo.tags]

def main(pr_number):
    repo = Repo(".")
    pr_branch = repo.active_branch.name
    base_branch = repo.git.rev_parse('origin/HEAD').split("/")[-1]

    print(f"Base branch: {base_branch}")
    print(f"PR branch: {pr_branch}")

    changed_files = get_changed_files(repo, base_branch, pr_branch)
    print(f"Changed files: {changed_files}")

    if changed_files != ['CMakeLists.txt']:
        print("Error: PR must only modify CMakeLists.txt.")
        sys.exit(1)

    version = extract_version_from_cmake("CMakeLists.txt")
    if not version:
        print("Error: Could not find version in CMakeLists.txt.")
        sys.exit(1)

    print(f"Extracted version: {version}")

    if not is_valid_version(version):
        print(f"Error: Invalid version format: {version}")
        sys.exit(1)

    if tag_exists(repo, version):
        print(f"Error: Tag {version} already exists!")
        sys.exit(1)

    # print(f"Merging PR #{pr_number}...")
    # os.system(f"gh pr merge {pr_number} --merge --admin --delete-branch")

    # print("Fetching merge commit SHA...")
    # sha = os.popen(f"gh pr view {pr_number} --json mergeCommit --jq .mergeCommit.oid").read().strip()

    # print(f"Creating tag {version} at {sha}...")
    # os.system(f"gh tag create {version} {sha} -m 'Tagging release {version}'")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_and_tag.py <pr_number>")
        sys.exit(1)
    main(sys.argv[1])