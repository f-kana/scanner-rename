# GCP Test Broker

このディレクトリには、ホスト側 GCP Test Broker の実装または説明が含まれます。

ブローカーは、Claude Code に直接 GCP 認証情報へのアクセスを与えることなく、Claude Code がクラウド統合テストを実行できるようにするためのものです。

## 想定するトポロジー

```text
Mac ホスト
  ├─ GCP 認証情報 / ADC
  ├─ GCP Test Broker
  │   └─ 127.0.0.1:8765
  │
  └─ DevContainer
       ├─ Claude Code
       └─ pytest クラウドテスト -> ブローカー
```

## 責務

ブローカーは以下を呼び出せます：

- Google Drive API
- Document AI OCR
- Gemini / Vertex AI

ブローカーは DevContainer に向けて目的を絞ったテストエンドポイントを公開します。

## 非目標

ブローカーは以下になってはいけません：

- 汎用 Google API プロキシ
- 汎用 HTTP プロキシ
- 認証情報共有サービス
- 任意のローカルファイルアップロードサービス

## 候補 v0 エンドポイント

```text
GET /health

POST /ocr-fixture
  input:
    { "case_id": "mortgage_balance_certificate_001" }

POST /extract-fixture
  input:
    { "case_id": "mortgage_balance_certificate_001" }
```

## 候補 v1 エンドポイント

```text
POST /drive/list-test-files
POST /drive/upload-fixture
POST /drive/rename-test-file
POST /drive/delete-test-files
```

## フィクスチャポリシー

フィクスチャはリポジトリ外に置くことを推奨します。

例：

```text
~/scanner-rename-cloud-fixtures/
```

Claude Code は `case_id` を渡します。

ブローカーは `case_id` を許可リスト化されたローカルフィクスチャにマッピングします。

## 概算サイズ

ブローカー v0 は小規模を想定：

```text
5〜6 ファイル
250〜400 行
README 50〜100 行
```

ブローカー v1 は以下程度に拡大する可能性あり：

```text
10〜12 ファイル
600〜900 行
README 100〜200 行
```

## 起動コマンドの概念例

正確なコマンドはまだ確定していません。

想定する形：

```bash
cd broker
uv sync
gcloud auth application-default login
export GCP_PROJECT_ID=...
export GCP_LOCATION=asia-northeast1
export DOCUMENT_AI_PROCESSOR_ID=...
export FIXTURE_DIR=~/scanner-rename-cloud-fixtures

uv run uvicorn gcp_test_broker.main:app \
  --host 127.0.0.1 \
  --port 8765
```

DevContainer 側のテストは以下を使用：

```bash
export GCP_TEST_BROKER_URL=http://host.docker.internal:8765
make test-cloud
```
