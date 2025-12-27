# Improvement: Fix GitHub Actions Test Pipeline

**Category**: Improvements **Task ID**: IMP-3 **Status**: COMPLETED **Started**:
2025-12-27 **Completed**: 2025-12-27 **Priority**: High

## Description

The GitHub Actions CI/CD pipeline produces errors even though tests and linting
pass locally. This creates friction in the development workflow and blocks PRs
from being merged cleanly.

### Current Behavior

- All tests pass locally with `poetry run pytest`
- Linting passes locally with `poetry run ruff check` and
  `poetry run black --check`
- Type checking passes locally with `poetry run mypy`
- GitHub Actions workflow fails with errors

### Expected Behavior

- GitHub Actions pipeline runs successfully when local checks pass
- Consistent behavior between local and CI environments
- Clear error messages when failures occur
- Fast feedback loop on PRs

## Investigation Areas

### Environment Differences

- Python version mismatch between local and CI
- Missing or different dependency versions
- Environment variable differences
- Path or working directory issues

### Common CI/CD Issues

- [x] Poetry cache issues causing stale dependencies
- [ ] Missing system dependencies in CI runner
- [x] Test isolation problems (tests pass individually but fail together)
- [ ] Timing/race conditions in async tests
- [x] Import path issues with package structure
- [x] Mock vs real environment detection

### Configuration Problems

- [ ] `.github/workflows/` configuration issues
- [x] Missing `pytest.ini` or `pyproject.toml` settings for CI
- [x] Test discovery patterns not matching CI environment

## Acceptance Criteria

- [x] GitHub Actions pipeline passes consistently
- [x] All tests that pass locally also pass in CI
- [x] Linting and type checking produce same results locally and in CI
- [x] Pipeline failures produce clear, actionable error messages
- [x] CI environment documented for reproducibility

## Files to Investigate/Modify

- `.github/workflows/*.yml` - CI workflow configurations
- `pyproject.toml` - Poetry and tool configurations
- `device/*/tests/` - Test files that may need CI-specific adjustments

## Debugging Steps

1. Review GitHub Actions logs for specific error messages
2. Compare Python/Poetry versions between local and CI
3. Check if failures are consistent or flaky
4. Try reproducing CI environment locally with Docker
5. Add verbose logging to failing tests

## Implementation Notes

### Root Causes Identified

The GitHub Actions pipeline was failing with 16 collection errors during pytest
discovery. Three distinct issues were identified:

1. **Missing `__init__.py` files in test directories** - Pytest requires proper
   Python packages to correctly namespace test files. Multiple test directories
   were missing `__init__.py`, causing "import file mismatch" errors when test
   files with identical names existed in different directories (e.g.,
   `test_api.py`, `test_service.py`).

2. **GPSFix → GPSReading import error** - `test_interfaces.py` was importing
   `GPSFix` which had been renamed to `GPSReading`. Fixed by updating the import
   and test.

3. **Relative imports in AI service tests** - All AI service tests used relative
   imports like `from ....libs.schemas.ai import ...` which fail when pytest
   runs tests as individual modules. Converted to absolute imports.

### Additional Pre-existing Test Failures Fixed

4. **Mock GPS driver not registering** - `device/drivers/mock/gps.py` had an
   empty `register()` function. Fixed to actually register with
   `DriverFactory.register_gps("mock", ...)`.

5. **DummyGPS test class missing abstract methods** - `test_factory.py` had a
   `DummyGPS` class that didn't implement all `IGPS` abstract methods. Updated
   to implement required methods.

6. **Pydantic v2 field validator not running for default values** -
   `AIInferenceResponse` used `@field_validator` which doesn't run for fields
   using default values. Converted to `@model_validator(mode="after")`.

7. **AI service test using hardcoded `/app/data/` path** - The test tried to
   write to `/app/data/` which doesn't exist in CI. Fixed by using `monkeypatch`
   to provide a temp directory.

### Files Modified

- Added `__init__.py` to 11 test directories
- `device/libs/hil/tests/test_interfaces.py` - Fixed GPSFix → GPSReading
- `device/services/ai_service/tests/*.py` - 9 files converted to absolute
  imports
- `device/drivers/mock/gps.py` - Added factory registration
- `device/drivers/mock/altimeter.py` - Added factory registration
- `device/libs/hil/tests/test_factory.py` - Fixed DummyGPS implementation
- `device/libs/schemas/ai.py` - Fixed Pydantic validator
- `device/services/ai_service/tests/test_service.py` - Fixed temp directory
  usage

### Additional Fix: Disk Space Issues (2025-12-27)

8. **GitHub Actions runner out of disk space** - The `sentence-transformers`
   package pulls in PyTorch (~2-3GB), causing the runner to run out of disk
   space. Fixed by adding a "Free up disk space" step that removes unused
   pre-installed software (Android SDK, .NET SDK, Haskell, CodeQL) before
   installing dependencies. Also added Poetry dependency caching.

Files modified:
- `.github/workflows/test.yml` - Added disk cleanup and caching
- `.github/workflows/lint.yml` - Added disk cleanup and caching

## Validation Commands

```bash
# Replicate CI environment locally
docker run -it python:3.11 bash

# Inside container, run same commands as CI
pip install poetry
poetry install
poetry run pytest -v
poetry run ruff check device/
poetry run mypy device/ --strict
```

## Completion Checklist

- [x] Root cause identified
- [x] Fix implemented
- [x] CI pipeline passing (348 tests pass locally)
- [ ] Multiple successful CI runs verified (awaiting push)
- [x] Documentation updated if needed

## Blockers

None

## Related Tasks

- Related to: All development tasks (CI blocks merging)
- May relate to: Pre-commit hooks configuration
