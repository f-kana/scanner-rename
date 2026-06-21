# ADR候補 0001: Google Cloud と Cloud Run Job の使用

## ステータス

候補。

これは正規の ADR ではありません。cc-sdd がプロジェクト設計を生成した後、承認・変更・破棄のいずれかを検討します。

## コンテキスト

ソース PDF はスキャナーによって Google Drive にアップロードされます。

システムは以下を行う必要があります：

- Google Drive 上のファイルの一覧表示とリネーム
- 定期的な実行
- OCR および文書解析サービスの呼び出し
- ログとアラートの出力

## 候補の決定

Google Cloud をランタイムプラットフォームとして使用します。

Cloud Run Job を実行環境として使用します。

Cloud Scheduler を使って5分ごとにジョブを起動します。

## 根拠

Google Drive がソースシステムであるため、Google Cloud が最初の選択肢として自然です。

Google Cloud はさらに以下を提供します：

- Google Drive API 連携
- Document AI OCR
- Gemini / Vertex AI オプション
- Cloud Run Job
- Cloud Scheduler
- Cloud Logging
- Cloud Monitoring ログベースアラート

v1 では不要なクロスクラウドの複雑さを避けられます。

## 結果

ポジティブ：

- クラウド境界が少ない
- 本番での認証モデルがシンプル
- Google Drive との整合性が高い
- Cloud Scheduler で簡単なスケジュール実行が可能

ネガティブ：

- プロジェクトが Google Cloud 中心になる
- v1 では AWS Textract / Bedrock は対象外
- 一部のサービスには実装時に確認が必要なリージョン制約がある

## 未解決事項

- 最終的な GCP リージョン
- Document AI プロセッサーの種類と場所
- Gemini を Vertex AI 経由で呼び出すか Gemini API 経由で呼び出すか
- サービスアカウントの権限
