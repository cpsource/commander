#!/bin/bash

# complete-pull-request.sh - Completes the pull request workflow
#
# Usage: ./complete-pull-request.sh
#
# This script:
# 1. Stages all changes
# 2. Commits changes using commander.txt as commit message  
# 3. Pushes branch to remote
# 4. Creates a GitHub pull request
#
# Prerequisites:
# - Must be run after prepare-pull-request.sh
# - Must be on a feature branch (not main/master)
# - commander.txt must exist
# - GitHub CLI must be installed and authenticated

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0"
    echo ""
    echo "This script completes the pull request workflow started by prepare-pull-request.sh"
    echo ""
    echo "Prerequisites:"
    echo "  - Must be run after prepare-pull-request.sh"
    echo "  - Must be on a feature branch (not main/master)"
    echo "  - commander.txt must exist in current directory"
    echo "  - GitHub CLI (gh) must be installed and authenticated"
    echo "  - Git repository must be initialized"
    echo ""
    echo "What this script does:"
    echo "  1. Stages all changes with 'git add .'"
    echo "  2. Commits using commander.txt as the commit message"
    echo "  3. Pushes the branch to remote origin"
    echo "  4. Creates a GitHub pull request"
}

print_status "🚀 Complete Pull Request - Step 2"
echo "=================================================="

# Step 1: Check for commander.txt
print_status "📋 Checking for commander.txt..."
if [ ! -f "commander.txt" ]; then
    print_error "commander.txt not found in current directory!"
    echo "Please ensure commander.txt exists with your commit message."
    exit 1
fi
print_success "commander.txt found"

# Step 2: Check if we're in a Git repository
print_status "📁 Checking Git repository..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a Git repository!"
    echo "Please run this script from within a Git repository."
    exit 1
fi
print_success "Git repository detected"

# Step 3: Get current branch and validate
CURRENT_BRANCH=$(git branch --show-current)
print_status "📍 Current branch: $CURRENT_BRANCH"

# Check if we're on main/master branch
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    print_error "Cannot complete pull request from main/master branch!"
    echo "Please run prepare-pull-request.sh first to create a feature branch."
    exit 1
fi

# Step 4: Check for GitHub CLI
print_status "🔧 Checking GitHub CLI..."
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) not found!"
    echo "Please install GitHub CLI: https://cli.github.com/"
    exit 1
fi

# Check if GitHub CLI is authenticated
if ! gh auth status &> /dev/null; then
    print_error "GitHub CLI not authenticated!"
    echo "Please run: gh auth login"
    exit 1
fi
print_success "GitHub CLI is ready"

# Step 5: Check if there are any changes to commit
print_status "📝 Checking for changes..."
if git diff --quiet && git diff --cached --quiet; then
    print_warning "No changes detected!"
    echo "It appears there are no changes to commit."
    echo "Did you run prepare-pull-request.sh first?"
    exit 1
fi
print_success "Changes detected and ready for commit"

# Step 6: Stage all changes
print_status "📦 Staging all changes..."
git add .
print_success "All changes staged"

# Step 7: Read commit message from commander.txt
print_status "📄 Reading commit message from commander.txt..."
COMMIT_MESSAGE=$(cat commander.txt)
if [ -z "$COMMIT_MESSAGE" ]; then
    print_error "commander.txt is empty!"
    echo "Please add a commit message to commander.txt"
    exit 1
fi
print_success "Commit message loaded from commander.txt"

# Step 8: Commit changes
print_status "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"
print_success "Changes committed with message from commander.txt"

# Step 9: Determine the base branch (main or master)
print_status "🔍 Determining base branch..."
if git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
elif git show-ref --verify --quiet refs/heads/master; then
    BASE_BRANCH="master"
else
    print_warning "Neither 'main' nor 'master' branch found, defaulting to 'main'"
    BASE_BRANCH="main"
fi
print_status "Using base branch: $BASE_BRANCH"

# Step 10: Push branch to remote
print_status "🚀 Pushing branch to remote..."
if git push -u origin "$CURRENT_BRANCH" 2>/dev/null; then
    print_success "Branch pushed to remote"
else
    print_warning "Failed to push branch to remote (authentication required)"
    print_warning "You can push manually later with: git push -u origin $CURRENT_BRANCH"
    
    # Ask if user wants to continue with local-only workflow
    read -p "Continue without pushing? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled"
        exit 1
    fi
    
    print_warning "Skipping pull request creation (branch not pushed)"
    print_success "✨ Local workflow completed!"
    echo "Branch '$CURRENT_BRANCH' created and committed locally"
    echo "Push manually when ready: git push -u origin $CURRENT_BRANCH"
    exit 0
fi

# Step 11: Create pull request
print_status "🔀 Creating GitHub pull request..."
PR_URL=$(gh pr create --title "$CURRENT_BRANCH" --body "$COMMIT_MESSAGE" --head "$CURRENT_BRANCH" --base "$BASE_BRANCH")

if [ $? -eq 0 ]; then
    print_success "Pull request created successfully!"
    echo "🔗 PR URL: $PR_URL"
else
    print_error "Failed to create pull request"
    print_warning "Branch has been pushed, you can create the PR manually with:"
    echo "gh pr create --title \"$CURRENT_BRANCH\" --body \"$COMMIT_MESSAGE\" --head \"$CURRENT_BRANCH\" --base \"$BASE_BRANCH\""
    exit 1
fi

print_success "✨ Pull request workflow completed successfully!"
echo "=================================================="
echo "Summary:"
echo "  🌿 Branch: $CURRENT_BRANCH"
echo "  💾 Changes committed with commander.txt message"
echo "  🚀 Branch pushed to remote"
echo "  🔀 Pull request created: $PR_URL"
echo "  📊 Base branch: $BASE_BRANCH"
echo ""
echo "You can now review the PR and merge when ready."
