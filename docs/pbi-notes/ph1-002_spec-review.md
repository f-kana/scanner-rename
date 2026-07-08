# PBI-ph1-002: 生成スペック 4 件のレビュー

完了日: 2026-07（commit 876ffe4）

## なぜやったか

`/kiro-spec-batch`（PBI-ph1-001）が生成した 4 スペック（core-naming-engine / extraction-pipeline / gcp-test-broker / cloud-runtime-deploy）を実装着手前に人間 + Fable セッションでレビューし、クロススペックレビューで挙がっていた minor 指摘 4 件を裁定・反映するため。critical / important はゼロだったが、境界の曖昧さは実装時の手戻りになるため先に潰した。

## 選んだアプローチとその理由

Fable セッションで 4 スペックの requirements / design / tasks 全 12 ファイルを通読し、steering（roadmap の Boundary Strategy）と `docs/initial-context.md` の命名合意に突き合わせた。指摘 4 件は全件「該当あり」と確認し、いずれも design.md / tasks.md への文言修正で解決した（要件の実質変更なし）:

1. `ExtractedText.value` 非空は型レベル不変条件（`__post_init__`）と明記し、Broker の `ExtractedTextPayload` に `min_length=1` を追加（両側で契約を一致させる）
2. `tests/cloud/` の応答→DTO 変換ヘルパ二重実装は「broker のテストローカルヘルパは deploy の `broker_adapters.py` 実装後に置き換え可」の注記で解消。統合ではなく注記にしたのは、実装順が broker → deploy であり broker スペックの独立完結性を保つため
3. 日付フォールバックは命名エンジン（core Req 4.7）に一元化。mapper は `document_date=None, date_has_era=False` を渡すのみ
4. deploy タスク 7/8（`tests/cloud/`・`tests/e2e_cloud/`）に `_Boundary:` 注釈を追加

レビュー中に新規 1 件を発見・反映: gcp-test-broker の `case_id` 形式検証が schemas（Pydantic pattern）と fixtures 層で二重所有になっており、Pydantic 側で弾くと FastAPI 既定の 422 ボディになって「エラーボディは `ErrorResponse` に統一」と矛盾する。検証の正本を fixtures 層に一元化（main が `InvalidCaseIdError` を 422 `ErrorResponse` に変換）。

## 却下した代替案

- 変換ヘルパ二重実装の「deploy 実装時に統合する」案 → broker スペック単体で完結しなくなるため注記方式を採用
- extraction-pipeline Req 3.2（フォールバック挙動の EARS 文）の書き換え → システムレベルの観測可能な挙動としては正しいため、design / tasks の実装記述のみ修正

## 残った制約・注意点

- Broker 実装時、`FixtureRequest.case_id` は素の `str` とし、pattern 制約を Pydantic に再導入しないこと（422 の統一 `ErrorResponse` は例外ハンドラで実現する設計）
- ポート契約・`DocumentExtraction` の変更時は 3 スペック横断レビューが必要（各 design の Revalidation Triggers 参照）。今回の `min_length=1` はその運用の最初の実例
