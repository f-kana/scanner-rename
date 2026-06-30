# Requirements Document

## Project Description (Input)

Secret scanning の導入（pre-commit に gitleaks を追加）。認証情報隔離は整備済だが、git commit レベルでの自動検出がない。

## Introduction

git commit時に認証情報やシークレットが含まれていないか自動検出する仕組みを導入する。既存の認証情報隔離方針（`.claude/rules/security.md`）を補完し、意図せず認証情報がコミットされることを防ぐ。

既存のpre-commit frameworkに統合し、ruff/prettierと同様の開発体験を提供する。

## Boundary Context

- **In scope**: git commit時のシークレット自動検出、検出時のコミット拒否、gitleaksの導入と設定
- **Out of scope**: コミット済み履歴のスキャン（別途手動実行で対応）、CI/CDパイプラインでのスキャン（Phase 0完了後に検討）
- **Adjacent expectations**: 既存のpre-commit framework（ruff、prettier、pyright）が正常動作していること。`.claude/hooks/post-edit-format.sh`が既存のpre-commit runを呼び出す設計が維持されること。

## Requirements

### Requirement 1: Secret Detection at Commit Time

**Objective:** As a developer, I want secrets to be automatically detected before commit, so that I never accidentally commit credentials to the repository.

#### Acceptance Criteria

1. When developer runs `git commit`, the Secret Scanner shall scan all staged files for secrets
2. If a secret pattern is detected in staged files, then the Secret Scanner shall reject the commit and display the detected secret type and file location
3. The Secret Scanner shall detect common secret patterns including API keys, tokens, passwords, and cloud provider credentials
4. The Secret Scanner shall complete the scan within 5 seconds for commits with up to 100 files

### Requirement 2: Integration with Existing Pre-commit Framework

**Objective:** As a developer, I want secret scanning to work seamlessly with existing pre-commit hooks, so that I have a consistent development experience.

#### Acceptance Criteria

1. When pre-commit framework is installed via `pre-commit install`, the Secret Scanner shall be registered as one of the commit hooks
2. The Secret Scanner shall execute in the same workflow as ruff and prettier hooks
3. When Claude Code Edit/Write tools are used, the Secret Scanner shall run automatically via the existing PostToolUse hook (`post-edit-format.sh`)
4. The Secret Scanner shall use the same pre-commit cache mechanism as other hooks to optimize performance on repeated runs

### Requirement 3: Configurable Detection Rules

**Objective:** As a developer, I want to configure which patterns are detected and which files are excluded, so that I can avoid false positives and tune detection to project needs.

#### Acceptance Criteria

1. The Secret Scanner shall read its detection rules from a dedicated configuration file (`.gitleaks.toml`)
2. The Secret Scanner shall support excluding specific file paths or patterns from scanning
3. When a false positive is identified, the Secret Scanner shall allow marking it as allowed via configuration without requiring code changes
4. The Secret Scanner shall support custom secret patterns in addition to built-in detection rules

### Requirement 4: Alignment with Existing Security Policy

**Objective:** As a developer, I want secret detection rules to align with existing security policy, so that protection is consistent across different mechanisms.

#### Acceptance Criteria

1. The Secret Scanner shall detect patterns that would violate `.claude/rules/security.md` prohibited paths and patterns
2. The Secret Scanner shall exclude temporary directories (`tmp/`, `.venv/`, `node_modules/`) from scanning, matching project conventions
3. When scanning worktree directories (`.claude/worktrees/`), the Secret Scanner shall apply the same rules as the main repository
