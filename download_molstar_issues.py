#!/usr/bin/env python3
"""
Download all issues (open and closed) from molstar/molstar GitHub repository.
Saves each issue as a separate .txt file with markdown preserved.

Usage:
    python download_molstar_issues.py

Optional: Set GITHUB_TOKEN environment variable for higher rate limits:
    export GITHUB_TOKEN=your_token_here
    python download_molstar_issues.py

Output:
    - issues/issue_NNNN_title.txt  - One file per issue with comments
    - issues/_index.txt            - Summary index of all issues
"""

import os
import requests
import time
from datetime import datetime
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

REPO_OWNER = "molstar"
REPO_NAME = "molstar"
OUTPUT_DIR = "issues"
API_BASE = "https://api.github.com"

# GitHub API headers
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Issue-Downloader"
}

# Check for GitHub token - required because 60 requests/hour is insufficient
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"
else:
    print("ERROR: GITHUB_TOKEN environment variable required.")
    print()
    print("Without a token, GitHub allows only 60 requests/hour, which is")
    print("insufficient to download all issues with comments.")
    print()
    print("To fix:")
    print("  1. Create a token at: https://github.com/settings/tokens")
    print("     (no special scopes needed for public repos)")
    print("  2. Run:")
    print("     export GITHUB_TOKEN=your_token_here")
    print(f"     python {os.path.basename(__file__)}")
    raise SystemExit(1)


def get_all_issues():
    """Fetch all issues (open and closed) with pagination."""
    issues = []
    page = 1
    per_page = 100
    
    while True:
        url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
        params = {
            "state": "all",
            "per_page": per_page,
            "page": page,
            "sort": "created",
            "direction": "asc"
        }
        
        print(f"Fetching issues page {page}...")
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            reset_dt = datetime.fromtimestamp(reset_time).strftime("%H:%M:%S")
            print(f"\nERROR: Rate limited by GitHub API.")
            print(f"Rate limit resets at: {reset_dt}")
            print(f"\nTo avoid this, set a GitHub token:")
            print(f"  export GITHUB_TOKEN=your_token_here")
            print(f"  python {os.path.basename(__file__)}")
            print(f"\nCreate a token at: https://github.com/settings/tokens")
            raise SystemExit(1)
        
        response.raise_for_status()
        page_issues = response.json()
        
        if not page_issues:
            break
        
        # Filter out pull requests (they also appear in issues endpoint)
        page_issues = [i for i in page_issues if "pull_request" not in i]
        issues.extend(page_issues)
        
        print(f"  Found {len(page_issues)} issues on page {page} (total: {len(issues)})")
        page += 1
        
        time.sleep(0.5)
    
    return issues


def get_issue_comments(issue_number):
    """Fetch all comments for a specific issue."""
    comments = []
    page = 1
    per_page = 100
    
    while True:
        url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments"
        params = {"per_page": per_page, "page": page}
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            wait_time = max(reset_time - time.time(), 60)
            print(f"  Rate limited. Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time)
            continue
        
        response.raise_for_status()
        page_comments = response.json()
        
        if not page_comments:
            break
        
        comments.extend(page_comments)
        page += 1
        time.sleep(0.3)
    
    return comments


def format_issue(issue, comments):
    """Format issue and comments into a text file suitable for LLM consumption."""
    lines = []
    
    # Header with key metadata
    lines.append(f"# Issue #{issue['number']}: {issue['title']}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- **State**: {issue['state']}")
    lines.append(f"- **Author**: {issue['user']['login']}")
    lines.append(f"- **Created**: {issue['created_at']}")
    lines.append(f"- **Updated**: {issue['updated_at']}")
    if issue.get('closed_at'):
        lines.append(f"- **Closed**: {issue['closed_at']}")
    lines.append(f"- **URL**: {issue['html_url']}")
    
    # Labels
    if issue.get('labels'):
        label_names = [label['name'] for label in issue['labels']]
        lines.append(f"- **Labels**: {', '.join(label_names)}")
    
    # Assignees
    if issue.get('assignees'):
        assignee_names = [a['login'] for a in issue['assignees']]
        lines.append(f"- **Assignees**: {', '.join(assignee_names)}")
    
    # Milestone
    if issue.get('milestone'):
        lines.append(f"- **Milestone**: {issue['milestone']['title']}")
    
    # Reactions summary
    if issue.get('reactions'):
        reactions = issue['reactions']
        reaction_str = []
        for key in ['+1', '-1', 'laugh', 'hooray', 'confused', 'heart', 'rocket', 'eyes']:
            if reactions.get(key, 0) > 0:
                reaction_str.append(f"{key}: {reactions[key]}")
        if reaction_str:
            lines.append(f"- **Reactions**: {', '.join(reaction_str)}")
    
    lines.append("")
    lines.append("## Description")
    lines.append("")
    
    # Issue body (preserve markdown)
    body = issue.get('body') or "*No description provided*"
    lines.append(body)
    
    # Comments section
    if comments:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Comments ({len(comments)})")
        
        for i, comment in enumerate(comments, 1):
            lines.append("")
            lines.append(f"### Comment {i}")
            lines.append(f"**Author**: {comment['user']['login']}")
            lines.append(f"**Date**: {comment['created_at']}")
            if comment.get('reactions'):
                reactions = comment['reactions']
                reaction_str = []
                for key in ['+1', '-1', 'laugh', 'hooray', 'confused', 'heart', 'rocket', 'eyes']:
                    if reactions.get(key, 0) > 0:
                        reaction_str.append(f"{key}: {reactions[key]}")
                if reaction_str:
                    lines.append(f"**Reactions**: {', '.join(reaction_str)}")
            lines.append("")
            lines.append(comment.get('body') or "*Empty comment*")
    
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Downloading all issues from {REPO_OWNER}/{REPO_NAME}...")
    print()
    
    issues = get_all_issues()
    print(f"\nFound {len(issues)} total issues")
    print()
    
    for i, issue in enumerate(issues, 1):
        issue_num = issue['number']
        print(f"[{i}/{len(issues)}] Processing issue #{issue_num}: {issue['title'][:50]}...")
        
        comments = get_issue_comments(issue_num)
        if comments:
            print(f"  - {len(comments)} comments")
        
        content = format_issue(issue, comments)
        
        # Filename: issue number padded + sanitized title
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in issue['title'])
        safe_title = safe_title[:50].strip()
        filename = f"issue_{issue_num:04d}_{safe_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        time.sleep(0.3)
    
    print()
    print(f"Done! Downloaded {len(issues)} issues to '{OUTPUT_DIR}/' directory")
    
    # Create summary index
    index_path = os.path.join(OUTPUT_DIR, "_index.txt")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# Issue Index for {REPO_OWNER}/{REPO_NAME}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total issues: {len(issues)}\n\n")
        
        open_issues = [i for i in issues if i['state'] == 'open']
        closed_issues = [i for i in issues if i['state'] == 'closed']
        f.write(f"Open: {len(open_issues)}\n")
        f.write(f"Closed: {len(closed_issues)}\n\n")
        
        f.write("## All Issues\n\n")
        for issue in issues:
            state = "OPEN" if issue['state'] == 'open' else "CLOSED"
            labels = ", ".join(l['name'] for l in issue.get('labels', []))
            label_str = f" [{labels}]" if labels else ""
            f.write(f"[{state}] #{issue['number']}: {issue['title']}{label_str}\n")
    
    print(f"Created index at '{index_path}'")


if __name__ == "__main__":
    main()