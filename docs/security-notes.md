# セキュリティノート

このドキュメントは、cc-sdd が正規の設計を生成する前の合意したセキュリティ方針を記録します。

## 主なセキュリティ目標

Claude Code がローカルテストとクラウド統合テストを実行し、失敗を観察してコードを修正できるようにします。

ただし、Claude Code は生の GCP 認証情報、アクセストークン、リフレッシュトークン、またはサービスアカウントキーを読み取り、印刷、コピー、または外部に持ち出してはいけません。

## ローカル隔離モデル

ローカル開発には以下のモデルを使用します：

```text
Mac ホスト
  ├─ GCP Test Broker
  │   └─ 127.0.0.1:8765 でリッスン
  │
  └─ DevContainer
       ├─ リポジトリ
       ├─ Python / pytest / リンター
       ├─ Claude Code
       ├─ ADC（named volume gcloud-config-* 経由でコンテナ内に存在）
       └─ ブローカーのみを呼び出すテスト
```

Claude Code は DevContainer の中で実行します。

GCP Test Broker は Mac ホスト上で実行します。

ADC は `devcontainer.json` の named volume（`gcloud-config-${devcontainerId}`）を介して `/home/vscode/.config/gcloud` にマウントされ、コンテナ内に存在します。これは Claude Code 自身の Vertex 認証（`claude-personal` エイリアス等）に必要な構成です。

クラウド統合テストはブローカー経由に限定します。Claude Code が Google Cloud API を直接呼び出すことは禁止します。

## ADC のコンテナ内存在と受容済みリスク

ADC はコンテナ内に存在しますが、Claude Code による読み取りは以下の手段で抑止します：

- `settings.json` の deny リスト（`~/.config/gcloud/*` 等のパスやトークン出力コマンドを列挙）
- `.claude/rules/security.md` に記述した規範ルール（調査禁止パス・実行禁止コマンドの明示）

これらは技術的に強制するアクセス制御ではなく、ベストエフォートの列挙です。deny リストに記載のないパスやコマンドを Claude Code が意図せず参照する可能性は完全には排除できません。

防御の主軸はブローカー設計（認証情報を公開しない API 設計）・gitleaks（コミット時シークレット検出）・コードレビューです。deny リストはその補助層として位置づけます。

コンテナ内に ADC が存在することは受容済みリスクとして記録します。

## ホームディレクトリの直接マウント禁止

DevContainer はホスト側の認証情報ディレクトリをバインドマウントしてはいけません：

```text
~/.aws/
~/.ssh/
~/.docker/
~/.kube/
~/Downloads/
ホストのホームディレクトリ
.env
.env.*
secrets/
credentials.json
service-account-key.json
token.json
application_default_credentials.json
```

GCP 認証情報は named volume 経由でのみコンテナ内に存在します。ホスト側の `~/.config/gcloud/` をバインドマウントする構成は禁止します。

## ブローカー経由のクラウドアクセスのみ

Claude Code が実行するクラウド統合テストはブローカーを使用しなければなりません。

DevContainer は以下を直接呼び出してはいけません：

```text
googleapis.com
generativelanguage.googleapis.com
documentai.googleapis.com
drive.googleapis.com
```

パッケージインストールや他の開発トラフィックが必要な場合は、クラウド統合テストの実行とは分けて管理します。

## ブローカーの設計制約

ブローカーは目的を絞ったテストファサードでなければなりません。

許可される方向：

```text
POST /ocr-fixture
POST /extract-fixture
POST /drive/list-test-files
POST /drive/upload-fixture
POST /drive/rename-test-file
POST /drive/delete-test-files
```

禁止される方向：

```text
POST /raw-google-api
POST /proxy
POST /execute-arbitrary-request
```

ブローカーは生の認証情報やトークンを公開してはいけません。

ブローカーは Authorization 値を含むリクエストヘッダーを返してはいけません。

ブローカーはログからシークレットを除去しなければなりません。

## フィクスチャポリシー

クラウドテストフィクスチャはリポジトリ外および DevContainer 外に保存することがあります。

例：

```text
~/scanner-rename-cloud-fixtures/
```

Claude Code はフィクスチャを任意のローカルファイルシステムパスではなく `case_id` で参照します。

ブローカーは `case_id` を許可リスト化されたフィクスチャファイルにマッピングします。

これにより、Claude Code が任意のプロジェクトまたはホストのファイルを Google Cloud API に送信することを防ぎます。

## Claude Code が実行してはいけないコマンド

Claude Code は認証情報を露出するコマンドを実行してはいけません。

例：

```text
gcloud auth application-default print-access-token
gcloud auth print-access-token
env
printenv
cat ~/.config/gcloud/*
cat *credential*
cat *token*
```

## 本番のアイデンティティ

本番では Cloud Run のサービスアイデンティティを使用します。

本番でサービスアカウントキー JSON ファイルを使用しないでください。

Cloud Run Job は必要最小限の権限を持つ専用のサービスアカウントで実行します。

## ログ

アプリケーションログには以下を含めてはいけません：

- アクセストークン
- リフレッシュトークン
- サービスアカウント JSON
- Authorization ヘッダー
- 環境変数の完全なダンプ
- 不要かつ無害でない限り生の認証情報ファイルパス

要確認/エラーの通知には、シークレットを含まない構造化ログを出力します。

例：

```json
{
  "event": "scanner_rename_attention_required",
  "status": "needs_review",
  "file_name": "_needs_review_20260507132742_001.pdf",
  "reason": "title_confidence_below_threshold",
  "severity": "WARNING"
}
```
