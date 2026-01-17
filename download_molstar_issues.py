#!/usr/bin/env python3
"""
Download all issues and discussions from molstar/molstar GitHub repository.
Saves each as a separate .txt file with markdown preserved.

Usage:
    python download_molstar_issues.py              # Download both
    python download_molstar_issues.py --issues     # Issues only
    python download_molstar_issues.py --discussions # Discussions only

Requires GITHUB_TOKEN in environment or .env file.
Create a token at: https://github.com/settings/tokens (no scopes needed)

Output:
    - issues/issue_NNNN_title.txt       - One file per issue with comments
    - issues/_index.txt                 - Summary index of all issues
    - discussions/disc_NNNN_title.txt   - One file per discussion with comments
    - discussions/_index.txt            - Summary index of all discussions
"""

import argparse
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
ISSUES_DIR = "issues"
DISCUSSIONS_DIR = "discussions"
GRAPHQL_URL = "https://api.github.com/graphql"

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Issue-Downloader"
}

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
else:
    print("ERROR: GITHUB_TOKEN environment variable required.")
    print()
    print("Without a token, GitHub allows only 60 requests/hour, which is")
    print("insufficient to download all issues with comments.")
    print()
    print("To create a token:")
    print("  1. Go to https://github.com/settings/tokens")
    print("  2. Click 'Generate new token (classic)'")
    print("  3. Give it a name (e.g., 'issue downloader')")
    print("  4. No scopes needed - just click 'Generate token' at the bottom")
    print("  5. Copy the token and run:")
    print()
    print("     export GITHUB_TOKEN=ghp_xxxxxxxxxxxx")
    print(f"     python {os.path.basename(__file__)}")
    raise SystemExit(1)


def graphql_request(query, variables):
    """Make a GraphQL request with rate limit handling."""
    response = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables}
    )
    
    if response.status_code == 403:
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        reset_dt = datetime.fromtimestamp(reset_time).strftime("%H:%M:%S")
        print(f"\nRate limited. Resets at {reset_dt}.")
        raise SystemExit(1)
    
    response.raise_for_status()
    data = response.json()
    
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return None
    
    return data


def get_all_issues():
    """Fetch all issues using GraphQL API."""
    issues = []
    cursor = None
    
    query = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        issues(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            number
            title
            body
            state
            author { login }
            createdAt
            updatedAt
            closedAt
            url
            labels(first: 10) { nodes { name } }
            assignees(first: 10) { nodes { login } }
            milestone { title }
            comments(first: 50) {
              nodes {
                author { login }
                body
                createdAt
              }
            }
          }
        }
      }
    }
    """
    
    page = 1
    while True:
        print(f"Fetching issues page {page}...")
        
        data = graphql_request(query, {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "cursor": cursor
        })
        
        if not data:
            break
        
        issue_data = data["data"]["repository"]["issues"]
        issues.extend(issue_data["nodes"])
        
        print(f"  Found {len(issue_data['nodes'])} issues (total: {len(issues)})")
        
        if not issue_data["pageInfo"]["hasNextPage"]:
            break
        
        cursor = issue_data["pageInfo"]["endCursor"]
        page += 1
        time.sleep(0.5)
    
    return issues


def get_all_discussions():
    """Fetch all discussions using GraphQL API."""
    discussions = []
    cursor = None
    
    query = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        discussions(first: 50, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            number
            title
            body
            author { login }
            createdAt
            updatedAt
            closed
            closedAt
            url
            category { name }
            labels(first: 10) { nodes { name } }
            comments(first: 50) {
              nodes {
                author { login }
                body
                createdAt
                replies(first: 20) {
                  nodes {
                    author { login }
                    body
                    createdAt
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    page = 1
    while True:
        print(f"Fetching discussions page {page}...")
        
        data = graphql_request(query, {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "cursor": cursor
        })
        
        if not data:
            break
        
        disc_data = data["data"]["repository"]["discussions"]
        discussions.extend(disc_data["nodes"])
        
        print(f"  Found {len(disc_data['nodes'])} discussions (total: {len(discussions)})")
        
        if not disc_data["pageInfo"]["hasNextPage"]:
            break
        
        cursor = disc_data["pageInfo"]["endCursor"]
        page += 1
        time.sleep(0.5)
    
    return discussions


def format_issue(issue):
    """Format issue and comments into a text file suitable for LLM consumption."""
    lines = []
    
    lines.append(f"# Issue #{issue['number']}: {issue['title']}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- **State**: {issue['state'].lower()}")
    lines.append(f"- **Author**: {issue['author']['login'] if issue['author'] else 'ghost'}")
    lines.append(f"- **Created**: {issue['createdAt']}")
    lines.append(f"- **Updated**: {issue['updatedAt']}")
    if issue.get('closedAt'):
        lines.append(f"- **Closed**: {issue['closedAt']}")
    lines.append(f"- **URL**: {issue['url']}")
    
    if issue.get('labels', {}).get('nodes'):
        label_names = [l['name'] for l in issue['labels']['nodes']]
        lines.append(f"- **Labels**: {', '.join(label_names)}")
    
    if issue.get('assignees', {}).get('nodes'):
        assignee_names = [a['login'] for a in issue['assignees']['nodes']]
        lines.append(f"- **Assignees**: {', '.join(assignee_names)}")
    
    if issue.get('milestone'):
        lines.append(f"- **Milestone**: {issue['milestone']['title']}")
    
    lines.append("")
    lines.append("## Description")
    lines.append("")
    lines.append(issue.get('body') or "*No description provided*")
    
    comments = issue.get('comments', {}).get('nodes', [])
    if comments:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Comments ({len(comments)})")
        
        for i, comment in enumerate(comments, 1):
            lines.append("")
            lines.append(f"### Comment {i}")
            lines.append(f"**Author**: {comment['author']['login'] if comment['author'] else 'ghost'}")
            lines.append(f"**Date**: {comment['createdAt']}")
            lines.append("")
            lines.append(comment.get('body') or "*Empty comment*")
    
    return "\n".join(lines)


def format_discussion(disc):
    """Format discussion and comments into a text file suitable for LLM consumption."""
    lines = []
    
    lines.append(f"# Discussion #{disc['number']}: {disc['title']}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- **State**: {'closed' if disc['closed'] else 'open'}")
    lines.append(f"- **Author**: {disc['author']['login'] if disc['author'] else 'ghost'}")
    lines.append(f"- **Category**: {disc['category']['name']}")
    lines.append(f"- **Created**: {disc['createdAt']}")
    lines.append(f"- **Updated**: {disc['updatedAt']}")
    if disc.get('closedAt'):
        lines.append(f"- **Closed**: {disc['closedAt']}")
    lines.append(f"- **URL**: {disc['url']}")
    
    if disc.get('labels', {}).get('nodes'):
        label_names = [l['name'] for l in disc['labels']['nodes']]
        lines.append(f"- **Labels**: {', '.join(label_names)}")
    
    lines.append("")
    lines.append("## Description")
    lines.append("")
    lines.append(disc.get('body') or "*No description provided*")
    
    comments = disc.get('comments', {}).get('nodes', [])
    if comments:
        lines.append("")
        lines.append("---")
        lines.append("")
        
        total_comments = len(comments) + sum(len(c.get('replies', {}).get('nodes', [])) for c in comments)
        lines.append(f"## Comments ({total_comments})")
        
        comment_num = 0
        for comment in comments:
            comment_num += 1
            lines.append("")
            lines.append(f"### Comment {comment_num}")
            lines.append(f"**Author**: {comment['author']['login'] if comment['author'] else 'ghost'}")
            lines.append(f"**Date**: {comment['createdAt']}")
            lines.append("")
            lines.append(comment.get('body') or "*Empty comment*")
            
            replies = comment.get('replies', {}).get('nodes', [])
            for reply in replies:
                comment_num += 1
                lines.append("")
                lines.append(f"### Comment {comment_num} (reply)")
                lines.append(f"**Author**: {reply['author']['login'] if reply['author'] else 'ghost'}")
                lines.append(f"**Date**: {reply['createdAt']}")
                lines.append("")
                lines.append(reply.get('body') or "*Empty reply*")
    
    return "\n".join(lines)


def save_items(items, output_dir, prefix, format_func, item_type):
    """Save items to files and create index."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, item in enumerate(items, 1):
        num = item['number']
        print(f"[{i}/{len(items)}] Saving {item_type} #{num}: {item['title'][:50]}...")
        
        content = format_func(item)
        
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in item['title'])
        safe_title = safe_title[:50].strip()
        filename = f"{prefix}_{num:04d}_{safe_title}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return len(items)


def create_issue_index(issues, output_dir):
    """Create index file for issues."""
    index_path = os.path.join(output_dir, "_index.txt")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# Issue Index for {REPO_OWNER}/{REPO_NAME}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total issues: {len(issues)}\n\n")
        
        open_issues = [i for i in issues if i['state'] == 'OPEN']
        closed_issues = [i for i in issues if i['state'] == 'CLOSED']
        f.write(f"Open: {len(open_issues)}\n")
        f.write(f"Closed: {len(closed_issues)}\n\n")
        
        f.write("## All Issues\n\n")
        for issue in issues:
            state = "OPEN" if issue['state'] == 'OPEN' else "CLOSED"
            labels = ", ".join(l['name'] for l in issue.get('labels', {}).get('nodes', []))
            label_str = f" [{labels}]" if labels else ""
            f.write(f"[{state}] #{issue['number']}: {issue['title']}{label_str}\n")
    
    return index_path


def create_discussion_index(discussions, output_dir):
    """Create index file for discussions."""
    index_path = os.path.join(output_dir, "_index.txt")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# Discussion Index for {REPO_OWNER}/{REPO_NAME}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total discussions: {len(discussions)}\n\n")
        
        open_disc = [d for d in discussions if not d['closed']]
        closed_disc = [d for d in discussions if d['closed']]
        f.write(f"Open: {len(open_disc)}\n")
        f.write(f"Closed: {len(closed_disc)}\n\n")
        
        categories = {}
        for disc in discussions:
            cat = disc['category']['name']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(disc)
        
        for cat, discs in sorted(categories.items()):
            f.write(f"## {cat} ({len(discs)})\n\n")
            for disc in discs:
                state = "OPEN" if not disc['closed'] else "CLOSED"
                f.write(f"[{state}] #{disc['number']}: {disc['title']}\n")
            f.write("\n")
    
    return index_path


def main():
    parser = argparse.ArgumentParser(description="Download GitHub issues and discussions")
    parser.add_argument("--issues", action="store_true", help="Download issues only")
    parser.add_argument("--discussions", action="store_true", help="Download discussions only")
    args = parser.parse_args()
    
    do_issues = args.issues or not args.discussions
    do_discussions = args.discussions or not args.issues
    
    print(f"Downloading from {REPO_OWNER}/{REPO_NAME}...")
    print()
    
    if do_issues:
        print("=" * 50)
        print("ISSUES")
        print("=" * 50)
        
        issues = get_all_issues()
        print(f"\nFound {len(issues)} total issues\n")
        
        save_items(issues, ISSUES_DIR, "issue", format_issue, "issue")
        index_path = create_issue_index(issues, ISSUES_DIR)
        
        print(f"\nDone! Downloaded {len(issues)} issues to '{ISSUES_DIR}/'")
        print(f"Created index at '{index_path}'")
    
    if do_discussions:
        print()
        print("=" * 50)
        print("DISCUSSIONS")
        print("=" * 50)
        
        discussions = get_all_discussions()
        print(f"\nFound {len(discussions)} total discussions\n")
        
        save_items(discussions, DISCUSSIONS_DIR, "disc", format_discussion, "discussion")
        index_path = create_discussion_index(discussions, DISCUSSIONS_DIR)
        
        print(f"\nDone! Downloaded {len(discussions)} discussions to '{DISCUSSIONS_DIR}/'")
        print(f"Created index at '{index_path}'")


if __name__ == "__main__":
    main()