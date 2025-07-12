#!/bin/bash
#!/bin/bash

# git-commander.sh - Wrapper script for commander.py with Git workflow
#
# Usage: ./git-commander.sh <new-branch-name> [-x 'extension-list'] [-r]
#
# This script:
# 1. Checks for commander.txt
# 2. Creates and switches to a new Git branch
# 3. Runs commander.py with auto-confirm (-y)
# 4. Commits changes using commander.txt as commit message
# 5. Creates a GitHub pull request

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
    echo "Usage: $0 <new-branch-name> [-x 'extension-list'] [-r]"
    echo ""
    echo "Arguments:"
    echo "  new-branch-name    Name for the new Git branch"
    echo "  -x 'ext1,ext2'     Comma-separated list of file extensions (optional)"
    echo "  -r                 Process files recursively (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 feature/update-docs"
    echo "  $0 fix/json-parsing -x 'py,json'"
    echo "  $0 refactor/all-files -x 'py,js,html' -r"
    echo ""
    echo "Prerequisites:"
    echo "  - commander.txt must exist in current directory"
    echo "  - commander.py must be available"
    echo "  - GitHub CLI (gh) must be installed and authenticated"
    echo "  - Git repository must be initialized"
}

# Check if branch name is provided
if [ $# -lt 1 ]; then
    print_error "Branch name is required"
    show_usage
    exit 1
fi

BRANCH_NAME="$1"
shift  # Remove branch name from arguments

# Parse remaining arguments for commander.py
COMMANDER_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -x)
            if [ -z "$2" ]; then
                print_error "Extension list required after -x"
                exit 1
            fi
            COMMANDER_ARGS="$COMMANDER_ARGS -x \"$2\""
            shift 2
            ;;
        -r)
            COMMANDER_ARGS="$COMMANDER_ARGS -r"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

print_status "🚀 Git Commander Wrapper"
echo "=================================================="

# Step 1: Check for commander.txt
print_status "📋 Checking for commander.txt..."
if [ ! -f "commander.txt" ]; then
    print_error "commander.txt not found in current directory!"
    echo "Please create commander.txt with your processing instructions before running this script."
    exit 1
fi
print_success "commander.txt found"

# Step 2: Check for commander.py
print_status "🔍 Checking for commander.py..."
if [ ! -f "commander.py" ]; then
    print_error "commander.py not found in current directory!"
    echo "Please ensure commander.py is available in the current directory."
    exit 1
fi
print_success "commander.py found"

# Step 3: Check if we're in a Git repository
print_status "📁 Checking Git repository..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a Git repository!"
    echo "Please run this script from within a Git repository."
    exit 1
fi
print_success "Git repository detected"

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

# Step 5: Save current branch and check for uncommitted changes
CURRENT_BRANCH=$(git branch --show-current)
print_status "📍 Current branch: $CURRENT_BRANCH"

if ! git diff --quiet || ! git diff --cached --quiet; then
    print_warning "You have uncommitted changes!"
    echo "Current changes will remain on branch '$CURRENT_BRANCH'"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled"
        exit 1
    fi
fi

# Step 6: Create and switch to new branch
print_status "🌿 Creating new branch: $BRANCH_NAME"
if git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
    print_error "Branch '$BRANCH_NAME' already exists!"
    echo "Please choose a different branch name or delete the existing branch."
    exit 1
fi

git checkout -b "$BRANCH_NAME"
print_success "Switched to new branch: $BRANCH_NAME"

# Step 7: Run commander.py
print_status "🤖 Running commander.py with arguments: $COMMANDER_ARGS -y"
eval "python commander.py $COMMANDER_ARGS -y"

if [ $? -ne 0 ]; then
    print_error "commander.py failed!"
    print_warning "Switching back to original branch: $CURRENT_BRANCH"
    git checkout "$CURRENT_BRANCH"
    git branch -D "$BRANCH_NAME" 2>/dev/null || true
    exit 1
fi

print_success "commander.py completed successfully"

# Step 8: Check if there are any changes to commit
print_status "📝 Checking for changes..."
if git diff --quiet && git diff --cached --quiet; then
    print_warning "No changes detected after running commander.py"
    print_warning "Switching back to original branch and cleaning up..."
    git checkout "$CURRENT_BRANCH"
    git branch -D "$BRANCH_NAME"
    print_warning "No commit or pull request created"
    exit 0
fi

# Step 9: Stage all changes
print_status "📦 Staging all changes..."
git add .
print_success "All changes staged"

# Step 10: Read commit message from commander.txt
print_status "📄 Reading commit message from commander.txt..."
COMMIT_MESSAGE=$(cat commander.txt)
if [ -z "$COMMIT_MESSAGE" ]; then
    print_error "commander.txt is empty!"
    exit 1
fi

# Step 11: Commit changes
print_status "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"
print_success "Changes committed with message from commander.txt"

# Step 12: Push branch to remote
#print_status "🚀 Pushing branch to remote..."
#git push -u origin "$BRANCH_NAME"
#print_success "Branch pushed to remote"

# Step 12: Push branch to remote
print_status "🚀 Pushing branch to remote..."
if git push -u origin "$BRANCH_NAME" 2>/dev/null; then
    print_success "Branch pushed to remote"
else
    print_warning "Failed to push branch to remote (authentication required)"
    print_warning "You can push manually later with: git push -u origin $BRANCH_NAME"
    
    # Ask if user wants to continue with local-only workflow
    read -p "Continue without pushing? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled"
        exit 1
    fi
    
    print_warning "Skipping pull request creation (branch not pushed)"
    print_success "✨ Local workflow completed!"
    echo "Branch '$BRANCH_NAME' created and committed locally"
    exit 0
fi


# Step 13: Create pull request
print_status "🔀 Creating GitHub pull request..."
PR_URL=$(gh pr create --title "$BRANCH_NAME" --body "$COMMIT_MESSAGE" --head "$BRANCH_NAME" --base "$CURRENT_BRANCH")

if [ $? -eq 0 ]; then
    print_success "Pull request created successfully!"
    echo "🔗 PR URL: $PR_URL"
else
    print_error "Failed to create pull request"
    print_warning "Branch has been pushed, you can create the PR manually"
    exit 1
fi

print_success "✨ Workflow completed successfully!"
echo "=================================================="
echo "Summary:"
echo "  🌿 Branch created: $BRANCH_NAME"
echo "  💾 Changes committed with commander.txt message"
echo "  🚀 Branch pushed to remote"
echo "  🔀 Pull request created: $PR_URL"
echo ""
echo "You can now review the PR and merge when ready."

