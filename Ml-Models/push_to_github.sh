#!/bin/bash
# Quick script to push to GitHub
# Usage: ./push_to_github.sh <github-username> <repo-name>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <github-username> <repo-name>"
    echo "Example: $0 john-doe prescription-ml"
    exit 1
fi

USERNAME=$1
REPONAME=$2
REMOTE_URL="https://github.com/$USERNAME/$REPONAME.git"

echo "=========================================="
echo "Pushing to GitHub"
echo "=========================================="
echo ""
echo "Username: $USERNAME"
echo "Repository: $REPONAME"
echo "URL: $REMOTE_URL"
echo ""

# Add remote
echo "Adding remote..."
git remote add origin $REMOTE_URL 2>/dev/null || git remote set-url origin $REMOTE_URL

# Rename branch if needed
echo "Checking branch..."
git branch -M main

# Push
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "✓ Push complete!"
echo "=========================================="
echo ""
echo "Visit: $REMOTE_URL"
echo ""
