# シークレットと認証情報のルール

認証情報やトークンを読み取り、印刷、要約、コピー、または外部に持ち出してはいけません。

## 調査禁止のパスとファイル

以下のパスやファイルを調査してはいけません：

```text
~/.config/gcloud/
~/.aws/
~/.ssh/
~/.docker/
~/.kube/
.env
.env.*
secrets/
credentials.json
service-account-key.json
token.json
application_default_credentials.json
```

## 実行禁止のコマンド

認証情報や環境変数のシークレットを出力するコマンドを実行してはいけません。以下を含みますが、これらに限りません：

```text
gcloud auth application-default print-access-token
gcloud auth print-access-token
env
printenv
cat ~/.config/gcloud/*
cat *credential*
cat *token*
```

## クラウド統合テストの制約

クラウド統合テストは、DevContainer から直接 Google API を呼び出してはいけません。ホスト側 GCP Test Broker のみを呼び出す必要があります。

ブローカーは目的を絞った狭い API を公開しなければなりません。生の Google API プロキシになってはいけません。

詳細は `docs/security-notes.md` を参照してください。
