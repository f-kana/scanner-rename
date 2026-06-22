# 開発環境セットアップ

## Claude Code

### サンドボックス設定

uv のキャッシュディレクトリへの書き込みを許可するため、ユーザーレベルの設定ファイル `~/.claude/settings.json` に以下を追加してください。

```json
{
  "sandbox": {
    "permissions": {
      "filesystem": {
        "write": {
          "allow": ["~/.cache/uv"]
        }
      }
    }
  }
}
```

この設定がないと、`uv add` 等のコマンド実行時にサンドボックスが `~/.cache/uv/` への書き込みをブロックし、`dangerouslyDisableSandbox` が都度必要になります。
