#!/bin/bash
# Safe push script that ensures quality checks before pushing

set -e

echo "🛡️ Safe Push: Ensuring code quality before push..."

# 1. Run quality checks and auto-fix
echo "🔧 Auto-fixing code quality issues..."
./scripts/pre-commit-check.sh

# 2. Add any auto-fixed files
echo "📝 Adding any auto-fixed files..."
git add -A

# 3. Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit after quality fixes"
else
    echo "📦 Committing auto-fixes..."
    git commit -m "Auto-fix: code formatting and import sorting"
fi

# 4. Push to remote
echo "🚀 Pushing to remote..."
git push origin $(git branch --show-current)

echo "✅ Safe push completed successfully!" 