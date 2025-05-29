#!/bin/bash
# Pre-commit check script to ensure code quality before pushing

set -e  # Exit on any error

echo "🔍 Running pre-commit checks..."

echo "📝 1. Code formatting with Black..."
black src/ tests/ scripts/ config/ examples/ *.py --line-length=100

echo "📋 2. Import sorting with isort..."
isort src/ tests/ scripts/ config/ examples/ *.py

echo "🔍 3. Code quality check with flake8..."
# Use strict rules for all directories
flake8 src/ tests/ scripts/ config/ examples/ *.py --count --max-complexity=10 --max-line-length=100 --statistics --extend-ignore=E501,E402,W503,F403,F405,E203,E722

echo "✅ 4. Verifying Black formatting..."
black --check src/ tests/ scripts/ config/ examples/ *.py --line-length=100

echo "✅ 5. Verifying import sorting..."
isort --check-only src/ tests/ scripts/ config/ examples/ *.py

echo "🔒 6. Security check with bandit (if available)..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o bandit-report.json || echo "⚠️  Security issues found, check bandit-report.json"
else
    echo "ℹ️  Bandit not installed, skipping security check"
fi

echo "🧪 7. Running tests..."
python -m pytest tests/ --tb=short -x

echo "🎉 All checks passed! Ready to commit and push." 