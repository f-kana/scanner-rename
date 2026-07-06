## apm install 後の差分確認

`apm install` 実行後は必ず `git status` で意図しないファイル生成がないか確認する。

### 背景: targets auto-detect の既知バグ (APM v0.21.0)

`apm.yml` で `targets:` を明示していても、APM が `.kiro/`、`.cursor/`、`.codex/` 等のディレクトリ存在を検知して auto-detect で追加ターゲットを active にする挙動が確認されている。このプロジェクトでは `.kiro/` が cc-sdd 用に存在するため、`apm install` で `.kiro/skills/` にもスキルが配置される。が、このプロジェクトはClaude Code専用であり、`.kiro/skills/`以下へのインストールは不要だ。

関連 issue:
- https://github.com/microsoft/apm/issues/1882 (open: auto-detect を hard error にする feature request)
- https://github.com/microsoft/apm/issues/1503 (closed: targets/target の不整合バグ)

APM のバージョンアップでこの挙動が修正された場合、この injector は不要になる。修正確認後に削除すること。

### 確認手順

1. `apm install` 実行後に `git status` を実行する
2. `.kiro/skills/` など意図しないディレクトリにファイルが生成されていないか確認する
3. 不審なファイルがあれば `apm targets` で active target を確認する
4. 意図しない target が active なら、生成されたファイルを削除する
