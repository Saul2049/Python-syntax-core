# Test Organization Checklist

## Quick Reference for Code Reviews & Development

### ✅ Pre-Development Checklist

**Before creating new tests:**
- [ ] Check if test file already exists for the module
- [ ] Follow naming convention: `test_{module_name}.py`
- [ ] Avoid creating duplicate test files
- [ ] Plan test structure before writing code

### ✅ Code Review Checklist

**When reviewing test-related PRs:**
- [ ] **No duplicate test files** - One primary test file per module
- [ ] **Proper naming** - Follows `test_{module_name}.py` convention
- [ ] **Comprehensive coverage** - All new functionality tested
- [ ] **Descriptive test names** - Clear what each test validates
- [ ] **Proper organization** - Tests grouped by functionality
- [ ] **Mock usage** - External dependencies properly mocked
- [ ] **Error handling** - Edge cases and exceptions tested
- [ ] **Documentation** - Test docstrings explain purpose

### ✅ File Structure Validation

**Check test directory structure:**
```
✅ GOOD Structure:
tests/
├── test_trading_engine.py
├── test_signal_processor.py  
├── test_broker.py
├── test_data_transformers.py
└── test_metrics_collector.py

❌ BAD Structure:
tests/
├── test_trading_engine.py
├── test_trading_engine_2.py
├── test_trading_engine_backup.py
├── trading_engine_tests.py
└── engine_test_alt.py
```

### ✅ Test Quality Standards

**Each test file should have:**
- [ ] Clear module docstring explaining purpose
- [ ] Organized test classes by functionality
- [ ] Descriptive test method names
- [ ] Proper setUp/tearDown methods
- [ ] Appropriate use of fixtures
- [ ] Error handling test cases
- [ ] Integration test scenarios

### ✅ Common Anti-Patterns to Avoid

**File Organization:**
- [ ] Multiple test files for same module ❌
- [ ] Vague file names like `test_stuff.py` ❌
- [ ] Tests scattered across random files ❌
- [ ] Backup/old test files not deleted ❌

**Test Content:**
- [ ] Duplicate test methods ❌
- [ ] Unclear test names like `test_function1()` ❌
- [ ] Missing error handling tests ❌
- [ ] Hard-coded test data without fixtures ❌

### ✅ Consolidation Readiness Check

**When consolidating existing duplicate files:**
- [ ] **Inventory complete** - All duplicate files identified
- [ ] **Conflicts resolved** - Merge strategy planned
- [ ] **Tests preserved** - No functionality lost
- [ ] **Coverage maintained** - All scenarios covered
- [ ] **Quality assured** - Full test suite passes
- [ ] **Cleanup done** - Old duplicate files removed

### ✅ Deployment Readiness

**Before merging test changes:**
- [ ] All tests pass locally
- [ ] No skipped tests without good reason
- [ ] Coverage reports generated
- [ ] Test documentation updated
- [ ] Performance impact assessed
- [ ] Integration tests validated

### ✅ Maintenance Tasks

**Regular maintenance (monthly/quarterly):**
- [ ] Scan for new duplicate test files
- [ ] Review test coverage reports
- [ ] Update test documentation
- [ ] Validate naming conventions
- [ ] Check for obsolete test files
- [ ] Review skipped tests for relevance

### 🚨 Red Flags - Stop and Review

**Immediate attention needed if you see:**
- Multiple test files with similar names for same module
- Test files with poor/unclear naming
- Very low test coverage on new modules
- Many skipped tests without documentation
- Test files with unclear purpose/documentation
- Duplicate test methods within same file

### 📊 Success Metrics

**Track these indicators:**
- **File Count**: Should trend downward (fewer duplicates)
- **Coverage**: Should maintain >80% per module  
- **Pass Rate**: Should maintain >90% passing tests
- **Skipped Tests**: Should be minimal and documented
- **Developer Feedback**: Easier to find and maintain tests

### 🛠️ Quick Fixes

**Common issues and solutions:**
1. **Found duplicate files**: Consolidate immediately
2. **Poor test names**: Rename to be descriptive
3. **Missing coverage**: Add tests for uncovered code
4. **Too many skips**: Fix or document why skipped
5. **Unclear purpose**: Add proper docstrings

---

## Usage Instructions

1. **Development Phase**: Use pre-development checklist
2. **Code Review Phase**: Use code review checklist  
3. **Maintenance Phase**: Use maintenance tasks checklist
4. **Emergency**: Check red flags section

Keep this checklist accessible during all test-related work to maintain the clean, organized test structure achieved through consolidation.

---

*Quick reference companion to TEST_ORGANIZATION_BEST_PRACTICES.md* 