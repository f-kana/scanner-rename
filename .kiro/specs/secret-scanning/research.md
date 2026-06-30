# Research & Design Decisions

## Summary

- **Feature**: `secret-scanning`
- **Discovery Scope**: Extension (既存pre-commit frameworkへの統合)
- **Key Findings**:
  - Gitleaks v8.30.1が最新安定版（2026年3月リリース）
  - Pre-commit managed installationによりバイナリ管理が自動化
  - デフォルトルール継承（`useDefault = true`）で100+パターンをカバー

## Research Log

### Gitleaks Integration with Pre-commit

- **Context**: 既存pre-commit framework（ruff、prettier、pyright）へのgitleaks追加方法を調査
- **Sources Consulted**:
  - [gitleaks公式リポジトリ](https://github.com/gitleaks/gitleaks)
  - [gitleaks/.pre-commit-hooks.yaml](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml)
  - IBM PTC Security, Advancing Engineering Dev blog posts
- **Findings**:
  - 公式pre-commit hookが3種類提供: `gitleaks` (Go managed)、`gitleaks-docker`、`gitleaks-system`
  - 推奨は `gitleaks` (pre-commit frameworkがGoバイナリを自動管理)
  - Hook定義: `gitleaks git --pre-commit --redact --staged --verbose`
  - バージョン固定: `rev: v8.30.1` でreproducible builds確保
- **Implications**:
  - `.pre-commit-config.yaml` に1エントリ追加するのみで導入完了
  - Docker不要（pre-commitがバイナリ取得・キャッシュ）
  - 既存PostToolUse hook（`post-edit-format.sh`）は変更不要

### Gitleaks Configuration Best Practices

- **Context**: `.gitleaks.toml` の設定方針とfalse positive対策
- **Sources Consulted**:
  - [gitleaks/config/gitleaks.toml](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
  - The Ultimate Gitleaks Guide (laoutaris.org)
  - OneUpTime blog on secret scanning
- **Findings**:
  - `[extend] useDefault = true` でビルトインルール全体を継承可能
  - Allowlist機能: `paths`（ファイルパス正規表現）、`regexes`（パターン正規表現）、`stopwords`（除外キーワード）
  - 標準除外: `vendor/`, `node_modules/`, `.venv/`, lockファイル、バイナリ
  - False positive頻発パターン: 環境変数プレースホルダー（`${VAR}`）、サンプル値（"example"、"dummy"）
- **Implications**:
  - プロジェクト固有の除外（`tmp/`、`.claude/worktrees/`）をallowlistに追加
  - `.claude/rules/security.md` の禁止パスと整合性確保
  - カスタムルール追加は不要（デフォルトで十分）

### Performance Characteristics

- **Context**: コミット時のスキャン速度とパフォーマンス要件（Requirement 1.4: 5秒以内）
- **Sources Consulted**:
  - Gitleaks公式ベンチマーク
  - Pre-commit Hooks: Enforcing Quality at the Source (advancingengineering.dev)
- **Findings**:
  - `--staged` フラグによりステージング済みファイルのみスキャン（フル履歴は対象外）
  - 典型的コミット（<10ファイル）: 1秒未満
  - 中規模コミット（~100ファイル）: 2-3秒（要件5秒を満たす）
  - Pre-commitキャッシュは `pass_filenames: false` のため効かないが、Git差分計算が高速化に寄与
  - 大規模ファイル対策: `.gitleaks.toml` の `max_target_megabytes` で除外可能
- **Implications**:
  - パフォーマンス要件は標準構成で満たされる
  - 最適化設定（`max_target_megabytes`）は初期実装で不要

## Architecture Pattern Evaluation

| Option                        | Description                             | Strengths                            | Risks / Limitations                  | Notes                                         |
| ----------------------------- | --------------------------------------- | ------------------------------------ | ------------------------------------ | --------------------------------------------- |
| Pre-commit managed (selected) | `.pre-commit-config.yaml` でhook登録    | バイナリ管理自動化、既存パターン踏襲 | Goランタイム依存（pre-commitが解決） | 推奨アプローチ、既存ruff/prettierと同じ方式   |
| Docker-based                  | `gitleaks-docker` hook使用              | 環境隔離、再現性高                   | Docker必須、起動オーバーヘッド       | 個人プロジェクトには過剰                      |
| System installation           | `gitleaks-system` hook + manual install | バージョン管理柔軟                   | 手動インストール必要、環境依存       | DevContainer外では一貫性低下                  |
| CI-only scanning              | ローカルhookなし、CI pipelineのみ       | ローカル環境汚染なし                 | コミット後検出（遅い）、バイパス容易 | Phase 0スコープ外、将来的な補完手段として検討 |

## Design Decisions

### Decision: Gitleaks採用（Build vs. Adopt）

- **Context**: シークレット検出機能の実装方法
- **Alternatives Considered**:
  1. Gitleaks（業界標準ツール、pre-commit公式サポート）
  2. detect-secrets（Yelp製、Python native）
  3. trufflehog（高精度、Git履歴スキャン特化）
  4. 自作正規表現スクリプト
- **Selected Approach**: Gitleaks v8.30.1をpre-commit managed installationで導入
- **Rationale**:
  - 業界標準（GitHub、GitLabで採用実績）
  - Pre-commit公式サポート（`.pre-commit-hooks.yaml` 提供）
  - 100+ビルトインルールで主要クラウドプロバイダーカバー
  - 設定可能なallowlistでfalse positive管理容易
  - パフォーマンス要件満たす（`--staged` で高速）
- **Trade-offs**:
  - Benefits: 導入コスト最小、メンテナンス不要、実績あり
  - Compromises: Go依存（pre-commitが解決）、カスタマイズ性は中程度
- **Follow-up**: 初回コミット後にfalse positive発生状況を確認、必要に応じてallowlist追加

### Decision: デフォルトルール継承（Generalization）

- **Context**: 検出ルールの定義方針
- **Alternatives Considered**:
  1. `[extend] useDefault = true` でビルトイン継承
  2. カスタムルールのみ定義（ゼロから構築）
  3. 特定プロバイダー（GCP、GitHub）のみ有効化
- **Selected Approach**: `[extend] useDefault = true` + プロジェクト固有allowlist
- **Rationale**:
  - デフォルトルールが100+パターンをカバー（AWS、GCP、GitHub、Slack等）
  - 将来的なクラウドプロバイダー追加に対応（一般化）
  - カスタムルール定義コスト不要
  - Allowlistで誤検知を柔軟に管理
- **Trade-offs**:
  - Benefits: 広範囲カバレッジ、メンテナンス最小
  - Compromises: 未使用プロバイダーも検出（過検出傾向）
- **Follow-up**: False positive多発時はallowlistで対応、特定ルール無効化は避ける

### Decision: 実行順序（gitleaks → ruff → prettier）

- **Context**: Pre-commit hooksの実行順序
- **Alternatives Considered**:
  1. gitleaks → ruff → prettier（セキュリティ優先）
  2. ruff → prettier → gitleaks（品質優先）
  3. 並列実行（pre-commit 2.0+ feature）
- **Selected Approach**: gitleaks → ruff → prettier
- **Rationale**:
  - セキュリティチェックを最優先（fail-fast）
  - シークレット検出時に後続フック（フォーマット）を実行しない（無駄防止）
  - `.pre-commit-config.yaml` のrepos順序で制御
- **Trade-offs**:
  - Benefits: セキュリティ優先、早期失敗
  - Compromises: ruffエラーとgitleaksエラーが同時表示されない
- **Follow-up**: 並列実行は複雑性増加のため採用せず

## Risks & Mitigations

- **False Positive多発** — Mitigation: `.gitleaks.toml` allowlistで既知パターン除外、stopwords活用
- **パフォーマンス劣化（5秒超過）** — Mitigation: `--staged` フラグで差分のみスキャン、`max_target_megabytes` で巨大ファイル除外
- **Local Bypass（`--no-verify`）** — Mitigation: CI統合（Phase 0外）で補完予定、ローカルはベストエフォート
- **Configuration Drift** — Mitigation: `.gitleaks.toml` をgit管理、worktreeで同じ設定適用

## References

- [gitleaks/gitleaks - GitHub](https://github.com/gitleaks/gitleaks)
- [gitleaks/.pre-commit-hooks.yaml](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml)
- [gitleaks/config/gitleaks.toml](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
- [Securing Your Repositories with gitleaks and pre-commit | IBM PTC Security](https://medium.com/@ibm_ptc_security/securing-your-repositories-with-gitleaks-and-pre-commit-27691eca478d)
- [Pre-commit Hooks: Enforcing Quality at the Source](https://www.advancingengineering.dev/posts/2026-04-pre-commit-hooks/)
- [The Ultimate Gitleaks Guide](https://laoutaris.org/blog/gitleaks/)
