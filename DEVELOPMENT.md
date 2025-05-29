# Development Workflow Guide

## 🚀 Quick Start

### Before Making Changes
```bash
# Ensure you're on the right branch
git checkout feature/your-feature-name
```

### After Making Changes

#### Option 1: Manual Workflow (Recommended for learning)
```bash
# 1. Run quality checks and auto-fix
./scripts/pre-commit-check.sh

# 2. Add and commit your changes
git add .
git commit -m "Your commit message"

# 3. Push (pre-push hook will run automatically)
git push origin feature/your-feature-name
```

#### Option 2: Automated Safe Push (Recommended for efficiency)
```bash
# This script does everything: quality checks, auto-fix, commit, and push
./scripts/safe-push.sh
```

## 🛡️ Quality Assurance

### Automatic Enforcement
- **Pre-push hook**: Automatically runs before every `git push`
- **Cannot be skipped**: Prevents pushing code that fails quality checks
- **Comprehensive checks**: Black, isort, flake8, and tests

### Manual Quality Checks
```bash
# Run all quality checks
./scripts/pre-commit-check.sh

# Individual checks
black --check src/ tests/ --line-length=100
isort --check-only src/ tests/
flake8 src/ tests/ --count --max-complexity=10 --max-line-length=100 --statistics --extend-ignore=E501,E402,W503,F403,F405,E722,E203
python -m pytest tests/ --tb=short
```

## 🚫 What NOT to Do

### ❌ Never Skip Quality Checks
```bash
# DON'T do this:
git push --no-verify  # Skips pre-push hook
git commit --no-verify  # Skips pre-commit checks

# These commands bypass our safety mechanisms!
```

### ❌ Don't Push Without Testing
```bash
# DON'T do this:
git add .
git commit -m "quick fix"
git push  # Without running quality checks first
```

## 🔧 Troubleshooting

### If Quality Checks Fail
1. **Read the error messages carefully**
2. **Fix the issues** (most are auto-fixable)
3. **Re-run the checks** to verify fixes
4. **Then commit and push**

### If Pre-push Hook Fails
```bash
# The hook will show you exactly what failed
# Fix the issues and try pushing again
# DO NOT use --no-verify to bypass!
```

## 📋 Checklist for Every Change

- [ ] Code changes made
- [ ] Quality checks passed (`./scripts/pre-commit-check.sh`)
- [ ] Tests passing
- [ ] Commit message is descriptive
- [ ] Push successful (pre-push hook passed)

## 🎯 Why This Matters

- **Prevents CI failures**: Catch issues locally before they reach CI
- **Maintains code quality**: Consistent formatting and standards
- **Saves time**: No more back-and-forth fixing CI issues
- **Team efficiency**: Everyone follows the same standards 