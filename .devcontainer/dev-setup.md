# DevContainer セットアップ手順

## GitHub 認証設定（Push/Pull）

DevContainer 内での Git 操作には、以下のいずれかの方法で GitHub 認証を設定する。

### 方法 1: VS Code の GitHub サインイン（推奨・最も簡単）

VS Code 上で DevContainer を使用する場合、ホスト側の VS Code で GitHub にサインインしていれば、自動的に認証が転送される。

前提条件:
- ホスト側の VS Code で GitHub アカウントにサインイン済み
- リモート URL が HTTPS 形式（`https://github.com/...`）

確認方法:
```bash
git fetch -v
git push --dry-run -v
```

この方法の制約:
- VS Code の credential helper に依存するため、CLI 単体での DevContainer 起動では動作しない
- 他のエディタや環境では使えない

### 方法 2: GitHub Personal Access Token (Fine-grained)

汎用性の高い方法。VS Code 以外の環境でも動作する。

#### PAT 発行手順

1. https://github.com/settings/tokens?type=beta にアクセス
2. "Generate new token" をクリック
3. 設定項目：
   - Token name: `scanner-rename devcontainer`
   - Expiration: 90 日など適切な期限
   - Repository access: "Only select repositories"
     - → `f-kana/scanner-rename` のみを選択
   - Repository permissions:
     - `Contents`: Read and write（必須：Push/Pull）
     - `Metadata`: Read-only（自動選択）
     - `Actions`: Read-only（CI 確認用）
     - `Issues`: Read and write（Issue 操作用）
     - `Pull requests`: Read and write（PR 操作用）
4. "Generate token" をクリック
5. 表示されたトークン（`github_pat_...`）をコピー

#### 認証情報の設定

初回の `git fetch` または `git push` 時に認証情報を求められる：
- Username: GitHub ユーザー名
- Password: 発行した PAT

Git credential helper が認証情報を保存するため、次回以降は入力不要。

#### リモート URL を HTTPS に変更

SSH 形式になっている場合は変更が必要：
```bash
git remote set-url origin https://github.com/f-kana/scanner-rename.git
git remote -v  # 確認
```

### SSH Agent 転送について

SSH 鍵を使った認証も可能だが、以下の理由で推奨しない：
- bind mount 方式だと秘密鍵がコンテナ内から読み取れるセキュリティリスク
- 設定が複雑
- HTTPS + PAT の方がシンプルで安全

## 動作確認

認証設定後、以下で動作を確認：
```bash
git fetch -v
git push --dry-run -v
```

エラーが出なければ設定完了。
