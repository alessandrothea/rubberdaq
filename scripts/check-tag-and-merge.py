#!/usr/bin/env python


import sys
import re
import os
from git import Repo, GitCommandError

def get_changed_files(repo, base_branch):
    repo.git.fetch('origin', base_branch)
    # Compare base branch to HEAD (which is the PR commit)
    diff = repo.git.diff('--name-only', f'origin/{base_branch}...HEAD')
    return diff.strip().splitlines()

VERSION_REGEX = re.compile(r"project\s*\(.*VERSION\s+(\d+)\.(\d+)\.(\d+)\)", re.IGNORECASE)

def extract_version_from_cmake(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    match = VERSION_REGEX.search(content)
    if not match:
        raise ValueError("No valid project(VERSION ...) found in the file.")
    return ".".join(match.groups())

def is_valid_version(version):
    return re.match(r'^v?\d+\.\d+\.\d+$', version) is not None

def check_tag_exists(repo, version):
    repo.git.fetch('--tags')
    return version in [t.name for t in repo.tags]

def create_git_tag(repo: Repo, tag_name: str, sha:str):
    try:
        return repo.create_tag(tag_name, ref=sha)
    except GitCommandError as e:
        raise RuntimeError(f"Failed to create git tag: {e}")

def push_git_tag(repo: Repo, tag_name: str):
    try:
        origin = repo.remote(name='origin')
        origin.push(tag_name)
        print(f"Successfully pushed tag: {tag_name}")
    except GitCommandError as e:
        raise RuntimeError(f"Failed to push git tag: {e}")

def print_recent_tags(repo: Repo, count: int = 10):
    tags = sorted(
        repo.tags,
        key=lambda t: t.commit.committed_datetime if t.commit else None,
        reverse=False
    )
    if tags:
        lines = []
        for tag in tags[-count:]:
            date = tag.commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S") if tag.commit else "unknown"
            line = f"{tag.name}  ({date})"
            # if tag.name in highlights:
                # line = f"[orange]{line}[/orange]"
            lines.append(line)
        print(f"Last {len(lines)} Tags:")
        print("\n".join(lines)), 
    else:
        print("No tags found in the repository.")


def main(pr_number):
    repo = Repo(".")
    pr_branch = os.environ.get('GITHUB_HEAD_REF')
    base_branch = os.environ.get('GITHUB_BASE_REF')
    pr_head_sha = os.environ.get('PR_HEAD_SHA')


    print(f"Base branch: {base_branch}")
    print(f"PR branch: {pr_branch}")

    try:

        changed_files = get_changed_files(repo, base_branch)
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
        tag_name = f"v{version}"

        print_recent_tags(repo)

        if check_tag_exists(repo, tag_name):
            print(f"Error: Tag {version} already exists!")
            sys.exit(1)


        tag = create_git_tag(repo, tag_name, sha)
        print(f"Successfully created tag: {tag}")


        push_git_tag(repo, tag_name)

        # print(f"Merging PR #{pr_number}...")
        # os.system(f"gh pr merge {pr_number} --merge --admin --delete-branch")

        # print("Fetching merge commit SHA...")
        # sha = os.popen(f"gh pr view {pr_number} --json mergeCommit --jq .mergeCommit.oid").read().strip()

        # print(f"Creating tag {version} at {sha}...")
        # os.system(f"gh tag create {version} {sha} -m 'Tagging release {version}'")
    except Exception as e:
        console.print(f"Error: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_and_tag.py <pr_number>")
        sys.exit(1)
    main(sys.argv[1])