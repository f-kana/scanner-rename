# 公式候補が Fit High の場合にそのまま採用を推奨する

## Prompt

classifying-harnessでカテゴリ4（Skill新規）に分類済み。
GitHub公式のMCP serverで、要求の90%を満たす候補が見つかった。
Star 5000+、月次更新、MIT license、公式ドキュメントあり。
この候補の採用判断をしてほしい。

## Expected behavior

- Fit: High と評価する
- Trust: High と評価する（公式publisher、更新頻度、利用実績）
- Risk: Low〜Medium と評価する（MCP serverなのでMediumになりうる）
- 「そのまま採用」または「APM/Plugin経由で採用」を推奨する
- 導入方法としてPlugin MarketplaceまたはAPMを優先提案する

## Failure behavior to avoid

- 公式候補なのに「自作推奨」と判断する
- Trust/Risk評価を省略して即採用する
- supply-chain riskの言及なしに導入する

## Pass criteria

- Fit/Trust/Riskの3軸すべてで評価が出力されている
- 採用判断が6択のいずれかで明示されている
- 導入方法が提案されている

## Negative case

同じ候補だが、個人repoでStar 10、最終更新2年前、licenseなしの場合。
この場合は「直接採用しない」と判断すべき。
