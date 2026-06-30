# Design Document

## Overview

このfeatureはgit commit時のシークレット自動検出機能を提供する。既存のpre-commit framework（ruff、prettier、pyright）にgitleaksを追加し、認証情報が誤ってコミットされることを防ぐ。

既存の `.claude/hooks/post-edit-format.sh` PostToolUse hookとシームレスに統合され、Claude Code Edit/Writeツール実行時にも自動的にスキャンが実行される。

**Users**: 開発者（1名、個人プロジェクト）が使用。手動コミット時およびClaude Code経由の編集時に自動検出が働く。

**Impact**: 既存の認証情報隔離方針（`.claude/rules/security.md`）を補完し、コミットレベルでの自動防御層を追加する。

### Goals

- git commit時にステージング済みファイルから認証情報を自動検出
- 既存pre-commit workflowとの統合（ruff/prettierと同じUX）
- 設定可能な検出ルールとfalse positive管理
- 既存セキュリティポリシーとの整合性

### Non-Goals

- コミット済み履歴の遡及スキャン（別途手動実行で対応）
- CI/CDパイプラインでのスキャン（Phase 0完了後に検討）
- リアルタイムファイル監視やIDE統合

## Boundary Commitments

### This Spec Owns

- `.pre-commit-config.yaml` へのgitleaks hook追加
- `.gitleaks.toml` 設定ファイルの作成と維持
- 既存セキュリティポリシー（`.claude/rules/security.md`）との整合性確保
- pyproject.toml へのgitleaks依存関係追加（開発依存）

### Out of Boundary

- 既存pre-commit frameworkの変更（`.pre-commit-config.yaml`の既存フック、`post-edit-format.sh`のロジック）
- `.claude/rules/security.md` の内容変更
- CI/CD pipelineの構築（Phase 0スコープ外）
- git履歴の遡及スキャン実装（手動実行で対応）

### Allowed Dependencies

- pre-commit framework（既存）
- gitleaks v8.30.1（新規導入、pre-commit managed）
- `.claude/hooks/post-edit-format.sh`（既存、変更不要）
- `.claude/rules/security.md`（読み取り専用参照）

### Revalidation Triggers

- pre-commit frameworkの変更（フック実行順序、キャッシュ挙動）
- `.claude/hooks/post-edit-format.sh` の変更（gitleaks呼び出しに影響する場合）
- `.claude/rules/security.md` の更新（新しい禁止パターンの追加）

## Architecture

### Existing Architecture Analysis

**現在のpre-commit framework構成**:

- `.pre-commit-config.yaml`: ruff-check, ruff-format, prettier, pyright（manual stage）
- `.claude/hooks/post-edit-format.sh`: Edit/Write後に `uv run pre-commit run --files` を自動実行
- 設計ドキュメント: `docs/adr-candidates/0006-posttooluse-and-precommit-dual-formatting.md`

**統合ポイント**:

- gitleaksは新しいhookとして `.pre-commit-config.yaml` に追加
- 既存フックとの実行順序: gitleaks → ruff → prettier の順が推奨（セキュリティチェックを最優先）
- PostToolUse hookは変更不要（pre-commit runがgitleaksを自動的に含む）

### Architecture Pattern & Boundary Map

```mermaid
graph TB
    subgraph "Git Workflow"
        Commit[git commit]
        Edit[Claude Edit/Write]
    end

    subgraph "Pre-commit Framework"
        PreCommitHook[pre-commit hooks]
        Gitleaks[gitleaks hook]
        Ruff[ruff hook]
        Prettier[prettier hook]
    end

    subgraph "Configuration"
        PreCommitConfig[.pre-commit-config.yaml]
        GitleaksConfig[.gitleaks.toml]
        SecurityRules[.claude/rules/security.md]
    end

    subgraph "Claude Code Hooks"
        PostEditFormat[post-edit-format.sh]
    end

    Commit --> PreCommitHook
    Edit --> PostEditFormat
    PostEditFormat --> PreCommitHook

    PreCommitHook --> Gitleaks
    PreCommitHook --> Ruff
    PreCommitHook --> Prettier

    Gitleaks --> GitleaksConfig
    GitleaksConfig -.reads.-> SecurityRules

    PreCommitConfig -.defines.-> Gitleaks
    PreCommitConfig -.defines.-> Ruff
    PreCommitConfig -.defines.-> Prettier
```

**Architecture Integration**:

- Selected pattern: pre-commit framework への hook 追加（既存パターンを踏襲）
- Domain/feature boundaries: セキュリティスキャン（gitleaks）とコード品質（ruff/prettier）を分離
- Existing patterns preserved: PostToolUse hook統合、設定ファイルの一元管理
- New components rationale: `.gitleaks.toml` が必要（gitleaks固有の検出ルールと除外設定）
- Steering compliance: 既存tech stack（Python、uv、pre-commit）に整合

### Technology Stack

| Layer                    | Choice / Version | Role in Feature                      | Notes                                   |
| ------------------------ | ---------------- | ------------------------------------ | --------------------------------------- |
| CLI / Tooling            | gitleaks v8.30.1 | シークレット検出エンジン             | pre-commit managed、Go バイナリ自動管理 |
| Integration Framework    | pre-commit 4.0+  | git hookオーケストレーション         | 既存、変更なし                          |
| Configuration Management | TOML             | `.gitleaks.toml` 検出ルール定義      | gitleaks標準フォーマット                |
| Package Management       | uv               | pre-commit実行環境（pyproject.toml） | 既存、gitleaks依存追加のみ              |

## File Structure Plan

### New Files

```
.gitleaks.toml                # Gitleaks detection rules and allowlist
```

### Modified Files

```
.pre-commit-config.yaml       # Add gitleaks hook entry
pyproject.toml                # Add gitleaks to dev dependencies (optional, for documentation)
```

### File Responsibilities

- `.gitleaks.toml`: 検出ルール設定、除外パターン、allowlist管理。既存 `.claude/rules/security.md` のパターンと整合させる。
- `.pre-commit-config.yaml`: gitleaks hookエントリ追加。実行順序はgitleaks → ruff → prettierを維持。
- `pyproject.toml`: 開発依存にpre-commitを追加済み。gitleaksはpre-commit managedのため追加不要（ドキュメント目的でコメント追記は可）。

## System Flows

### Secret Detection Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as git commit
    participant PreCommit as pre-commit
    participant Gitleaks as gitleaks
    participant Config as .gitleaks.toml

    Dev->>Git: git commit
    Git->>PreCommit: trigger hooks
    PreCommit->>Gitleaks: run gitleaks hook
    Gitleaks->>Config: load rules
    Gitleaks->>Gitleaks: scan staged files

    alt Secret detected
        Gitleaks-->>PreCommit: exit 1 (failure)
        PreCommit-->>Git: reject commit
        Git-->>Dev: display error + location
    else No secrets
        Gitleaks-->>PreCommit: exit 0 (success)
        PreCommit->>PreCommit: continue to ruff/prettier
        PreCommit-->>Git: all hooks passed
        Git-->>Dev: commit success
    end
```

### Claude Code Integration Flow

```mermaid
sequenceDiagram
    participant Claude as Claude Code
    participant PostHook as post-edit-format.sh
    participant PreCommit as pre-commit run
    participant Gitleaks as gitleaks

    Claude->>Claude: Edit/Write tool
    Claude->>PostHook: trigger PostToolUse hook
    PostHook->>PreCommit: uv run pre-commit run --files $FILE
    PreCommit->>Gitleaks: run gitleaks (if applicable)
    Gitleaks->>Gitleaks: scan modified file

    alt Secret in file
        Gitleaks-->>PreCommit: exit 1
        PreCommit-->>PostHook: failure (non-blocking, || true)
        PostHook-->>Claude: log warning
        Note over Claude: User sees warning in output
    else No secret
        Gitleaks-->>PreCommit: exit 0
        PreCommit-->>PostHook: success
        PostHook-->>Claude: continue
    end
```

## Requirements Traceability

| Requirement | Summary                        | Components             | Interfaces              | Flows                            |
| ----------- | ------------------------------ | ---------------------- | ----------------------- | -------------------------------- |
| 1.1         | Scan staged files              | gitleaks hook          | gitleaks CLI            | Secret Detection Flow            |
| 1.2         | Reject commit if secret found  | pre-commit + gitleaks  | exit code handling      | Secret Detection Flow            |
| 1.3         | Detect common secret patterns  | .gitleaks.toml rules   | gitleaks config         | -                                |
| 1.4         | Performance < 5s               | gitleaks --staged flag | gitleaks CLI            | -                                |
| 2.1         | Register in pre-commit install | .pre-commit-config     | pre-commit framework    | -                                |
| 2.2         | Execute with ruff/prettier     | .pre-commit-config     | pre-commit framework    | Secret Detection Flow            |
| 2.3         | Auto-run via PostToolUse       | post-edit-format.sh    | pre-commit run --files  | Claude Code Integration Flow     |
| 2.4         | Use pre-commit cache           | pre-commit framework   | pre-commit cache        | -                                |
| 3.1         | Read from .gitleaks.toml       | gitleaks config loader | TOML format             | Secret Detection Flow            |
| 3.2         | Support path exclusions        | .gitleaks.toml paths   | allowlist config        | -                                |
| 3.3         | Allowlist false positives      | .gitleaks.toml regexes | allowlist config        | -                                |
| 3.4         | Support custom patterns        | .gitleaks.toml rules   | custom rules definition | -                                |
| 4.1         | Align with security.md         | .gitleaks.toml paths   | path patterns           | -                                |
| 4.2         | Exclude tmp/.venv/node_modules | .gitleaks.toml paths   | path patterns           | -                                |
| 4.3         | Apply same rules in worktrees  | .gitleaks.toml         | git worktree context    | Secret Detection Flow (worktree) |

## Components and Interfaces

| Component           | Domain/Layer  | Intent                                  | Req Coverage            | Key Dependencies (P0/P1) | Contracts |
| ------------------- | ------------- | --------------------------------------- | ----------------------- | ------------------------ | --------- |
| gitleaks hook       | Security      | Staged file secret scanning             | 1.1, 1.2, 1.4, 2.2, 2.3 | pre-commit (P0)          | CLI       |
| .gitleaks.toml      | Configuration | Detection rules and allowlist           | 1.3, 3.1-3.4, 4.1, 4.2  | None                     | Data      |
| .pre-commit-config  | Configuration | Hook registration and ordering          | 2.1, 2.2                | pre-commit (P0)          | Data      |
| post-edit-format.sh | Integration   | Claude Code to pre-commit bridge (既存) | 2.3                     | pre-commit (P0)          | Bash      |

### Security / Detection

#### gitleaks hook

| Field        | Detail                                               |
| ------------ | ---------------------------------------------------- |
| Intent       | ステージング済みファイルからシークレットを検出       |
| Requirements | 1.1, 1.2, 1.4, 2.2, 2.3                              |
| Owner        | gitleaks (external), pre-commit framework (internal) |

**Responsibilities & Constraints**

- ステージング済みファイルのシークレットパターンマッチング
- 検出時にコミット拒否（exit 1）
- `.gitleaks.toml` からルールと除外設定を読み込み
- 5秒以内にスキャン完了（100ファイル以下）

**Dependencies**

- Inbound: pre-commit framework — hook trigger (P0)
- Outbound: `.gitleaks.toml` — configuration loading (P0)
- External: gitleaks v8.30.1 binary — detection engine (P0)

**Contracts**: CLI [x]

##### CLI Interface

```bash
gitleaks git --pre-commit --redact --staged --verbose
```

- `--pre-commit`: pre-commitモード（差分のみスキャン）
- `--redact`: 検出結果のシークレット値をマスク
- `--staged`: ステージング済みファイルのみ対象
- `--verbose`: 詳細ログ出力

**Exit Codes**:

- 0: シークレット未検出
- 1: シークレット検出（コミット拒否）
- 2: 設定エラー

**Performance**:

- ステージング済みファイルのみスキャン（`--staged`）で1秒未満（典型的コミット）
- pre-commitキャッシュは効かない（`pass_filenames: false`）が、Git差分計算が高速化に寄与

**Implementation Notes**

- Integration: `.pre-commit-config.yaml` でhook ID `gitleaks` を指定、rev `v8.30.1` でバージョン固定
- Validation: 初回 `pre-commit install` 後に `pre-commit run gitleaks --all-files` でテスト実行
- Risks: フル履歴スキャンは重いため `--staged` 必須。CI統合は別Phase。

### Configuration

#### .gitleaks.toml

| Field        | Detail                            |
| ------------ | --------------------------------- |
| Intent       | 検出ルールと除外パターンの定義    |
| Requirements | 1.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2 |
| Owner        | プロジェクトメンテナー            |

**Responsibilities & Constraints**

- デフォルトルールの継承（`[extend] useDefault = true`）
- プロジェクト固有の除外パス設定
- False positive allowlist管理
- `.claude/rules/security.md` のパターンとの整合性維持

**Dependencies**

- Inbound: gitleaks CLI — configuration loading (P0)
- Outbound: `.claude/rules/security.md` — reference for pattern alignment (P2)

**Contracts**: Data [x]

##### Configuration Schema

```toml
title = "gitleaks config"
minVersion = "v8.25.0"

[extend]
useDefault = true  # 100+ built-in rules

[allowlist]
paths = [
  '''gitleaks\.toml$''',
  '''\.env\.example$''',
  '''tmp/''',
  '''\.venv/''',
  '''node_modules/''',
  '''\.claude/worktrees/.*\.md$''',  # worktree README files
]

regexes = [
  '''\$\{?[A-Z_]+\}?''',  # Environment variable placeholders
]

stopwords = [
  "example",
  "dummy",
  "placeholder",
]
```

**Validation**:

- `gitleaks git --config .gitleaks.toml --verbose` で設定検証
- `.claude/rules/security.md` の禁止パス（`~/.config/gcloud/`, `~/.ssh/` など）をパターンマッチで検出

**Implementation Notes**

- Integration: プロジェクトルートに配置、gitleaks が自動検出
- Validation: 既知の非シークレット文字列（"example"、"dummy"）を stopwords に追加
- Risks: False positiveが多い場合はallowlistの定期メンテナンスが必要

#### .pre-commit-config.yaml

| Field        | Detail                            |
| ------------ | --------------------------------- |
| Intent       | gitleaks hookの登録と実行順序制御 |
| Requirements | 2.1, 2.2                          |
| Owner        | プロジェクトメンテナー            |

**Responsibilities & Constraints**

- gitleaks hookエントリの追加
- 実行順序: gitleaks → ruff → prettier（セキュリティ優先）
- バージョン固定（`rev: v8.30.1`）

**Dependencies**

- Inbound: pre-commit framework — hook definition (P0)
- Outbound: gitleaks hook — hook registration (P0)

**Contracts**: Data [x]

##### Configuration Entry

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

**Hook Ordering**:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks  # 1st: security
    ...
  - repo: https://github.com/astral-sh/ruff-pre-commit  # 2nd: linting
    ...
  - repo: https://github.com/pre-commit/mirrors-prettier  # 3rd: formatting
    ...
```

**Implementation Notes**

- Integration: 既存 `.pre-commit-config.yaml` の先頭に追加（セキュリティチェック優先）
- Validation: `pre-commit run --all-files` で全hookの正常動作を確認
- Risks: バージョン更新時は `pre-commit autoupdate` 実行後に動作確認必須

## Data Models

このfeatureはデータモデルを持たない（設定ファイルのみ）。

## Error Handling

### Error Strategy

Gitleaksの検出結果はexit codeで制御され、pre-commit frameworkがエラーハンドリングを担当する。

### Error Categories and Responses

**Secret Detected (exit 1)**:

- Context: ステージング済みファイルにシークレットパターンが検出された
- Response: コミット拒否、検出箇所をターミナルに表示（ファイルパス、行番号、シークレットタイプ）
- User Action: 該当行を修正してre-commit、または `.gitleaks.toml` allowlistに追加（false positiveの場合）

**Configuration Error (exit 2)**:

- Context: `.gitleaks.toml` のシンタックスエラーまたは不正な設定
- Response: pre-commit失敗、エラーメッセージ表示
- User Action: `.gitleaks.toml` を修正

**Performance Timeout (rare)**:

- Context: 大量ファイルで5秒を超過
- Response: pre-commit継続（timeoutは設定されていない）
- User Action: `.gitleaks.toml` で `max_target_megabytes` を設定して巨大ファイルを除外

### Monitoring

- ローカル環境: ターミナル出力のみ
- Claude Code統合: PostToolUse hookのログに検出結果が記録される（`post-edit-format.sh` の `|| true` により非ブロッキング）

## Testing Strategy

### Unit Tests

該当なし（設定ファイルのみ、実行可能コードなし）

### Integration Tests

1. **正常系: シークレットなしコミット**
   - Setup: 通常のPythonコードをステージング
   - Execute: `git commit`
   - Expected: gitleaks pass、コミット成功

2. **異常系: シークレット検出**
   - Setup: `AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE` を含むファイルをステージング
   - Execute: `git commit`
   - Expected: gitleaks fail、コミット拒否、検出箇所表示

3. **Allowlist動作確認**
   - Setup: `.env.example` にシークレット風文字列を含む
   - Execute: `git commit`
   - Expected: gitleaks pass（pathsでallowlistされている）

4. **Claude Code統合**
   - Setup: Edit toolで認証情報を含むファイルを編集
   - Execute: Edit tool実行
   - Expected: PostToolUse hookでgitleaks実行、警告表示（非ブロッキング）

5. **Worktree環境**
   - Setup: `.claude/worktrees/feature-x/` でコミット実施
   - Execute: `git commit`
   - Expected: メインリポジトリと同じgitleaks設定が適用される

### Performance Tests

1. **小規模コミット（< 10ファイル）**
   - Expected: < 1秒

2. **中規模コミット（~100ファイル）**
   - Expected: < 5秒（Requirement 1.4）

3. **pre-commit cache動作確認**
   - Setup: 同じファイルで2回目のコミット
   - Expected: gitleaksキャッシュは効かないが、Git差分計算により高速

## Optional Sections

### Security Considerations

- Gitleaks自体のセキュリティ: 公式リポジトリから取得、SHA検証はpre-commit frameworkが実施
- False negative risk: デフォルトルールは100+パターンをカバーするが、カスタムシークレットは `.gitleaks.toml` に追加必要
- Bypass risk: pre-commit hookはローカルで `git commit --no-verify` でバイパス可能。CI統合（Phase 0外）で補完予定。

### Performance & Scalability

- Target: 100ファイル以下で5秒以内（Requirement 1.4）
- Scaling approach: `--staged` フラグにより差分のみスキャン、フル履歴は対象外
- Optimization: `.gitleaks.toml` の `max_target_megabytes` で巨大ファイルをスキップ可能
