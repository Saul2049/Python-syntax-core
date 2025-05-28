#!/bin/bash
# Pre-commit check script to ensure code quality before pushing

set -e  # Exit on any error

echo "🔍 Running pre-commit checks..."

echo "📝 1. Code formatting with Black..."
black src/ tests/ --line-length=100

echo "📋 2. Import sorting with isort..."
isort src/ tests/

echo "🔍 3. Code quality check with flake8..."
flake8 src/ tests/ --count --max-complexity=10 --max-line-length=100 --statistics --extend-ignore=E501,E402,W503,F403,F405,E722,E203

echo "✅ 4. Verifying Black formatting..."
black --check src/ tests/ --line-length=100

echo "✅ 5. Verifying import sorting..."
isort --check-only src/ tests/

echo "🧪 6. Running tests..."
python -m pytest tests/ --tb=short -x

echo "🎉 All checks passed! Ready to commit and push." 