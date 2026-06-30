# Implementation Plan

## Phase 1: Foundation & Configuration

- [x] 1. Setup: pre-commit framework configuration and gitleaks integration
- [x] 1.1 Add gitleaks hook to `.pre-commit-config.yaml`
  - Add gitleaks repository entry at the beginning of repos list (security priority)
  - Set `rev: v8.30.1` for version pinning
  - Configure hook ID `gitleaks` with appropriate flags
  - gitleaks hook appears before ruff and prettier in execution order
  - _Requirements: 2.1, 2.2_
  - _Boundary: Pre-commit Configuration_

- [x] 1.2 Create `.gitleaks.toml` configuration file
  - Set `title`, `minVersion` fields
  - Enable `[extend] useDefault = true` for 100+ built-in rules
  - Define `[allowlist] paths` to exclude `.env.example`, `tmp/`, `.venv/`, `node_modules/`, `.claude/worktrees/.*\.md$`
  - Define `[allowlist] regexes` for environment variable placeholders (`\$\{?[A-Z_]+\}?`)
  - Define `[allowlist] stopwords` for "example", "dummy", "placeholder"
  - Patterns align with `.claude/rules/security.md` prohibited paths
  - _Requirements: 1.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2_
  - _Boundary: Gitleaks Configuration_

## Phase 2: Validation

- [x] 2. Testing: verify secret detection and framework integration
- [x] 2.1 Verify gitleaks installation and basic execution
  - Run `pre-commit install` to register hooks
  - Run `pre-commit run gitleaks --all-files` to verify gitleaks binary is downloaded and executes
  - Confirm exit code 0 (no secrets detected in clean repository)
  - Execution completes within expected time (< 5s for current file count)
  - _Requirements: 1.1, 1.4, 2.1, 2.4_
  - _Boundary: Pre-commit Framework_

- [x] 2.2 Test secret detection with positive case
  - Create temporary test file at project root (not tmp/ which is gitignored)
  - Stage the file and attempt commit
  - Verify gitleaks detects secret, rejects commit (exit 1), and displays file location and secret type
  - Remove test file after validation
  - _Requirements: 1.1, 1.2, 1.3_
  - _Boundary: Gitleaks Detection Engine_

- [x] 2.3 Test allowlist configuration
  - Create `.env.example` file with example secret-like strings
  - Stage and commit the file
  - Verify gitleaks pass (exit 0) due to path allowlist
  - `.env.example` successfully committed without detection
  - _Requirements: 3.2, 3.3_
  - _Boundary: Gitleaks Configuration_

- [x] 2.4 Verify Claude Code integration via PostToolUse hook
  - Confirmed `post-edit-format.sh` runs `uv run pre-commit run --files "$FILE" || true`
  - gitleaks is now included in pre-commit hooks, so it runs automatically on Edit/Write
  - Non-blocking behavior confirmed via `|| true`
  - _Requirements: 2.3_
  - _Boundary: PostToolUse Hook Integration_

- [x] 2.5 Verify worktree environment behavior
  - `.gitleaks.toml` and `.pre-commit-config.yaml` exist at worktree root
  - Worktree shares git root with main repository, same config applies
  - _Requirements: 4.3_
  - _Boundary: Git Worktree Integration_

## Implementation Notes

- Task 2.2: tmp/ is gitignored, so positive-case test files must be created at project root and cleaned up after (git restore --staged + rm). stopwords ("example", "dummy", "placeholder") affect detection, so test values must not contain these words.
