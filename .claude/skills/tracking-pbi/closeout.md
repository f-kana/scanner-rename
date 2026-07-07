# PBI クローズアウト手順

`tracking-pbi` で `[x]` にマークした後に実行する。

## 1. PBI詳細セクションの確認

`docs/product-backlog.md` の `# PBI詳細` セクションに当該 PBI の記述があるか確認する。

### ある場合 → docs/pbi-notes/ へ移動

1. `docs/pbi-notes/<pbi-id>_<pbi-summary>.md` を新規作成（例: `docs/pbi-notes/ph0-026_pbi-notes-archive.md`）
2. 以下のテンプレートで WHY 中心のノートを書く:

```markdown
# PBI-<id>: <タイトル>

完了日: <年月>（PR #<N> または commit <hash>）

## なぜやったか
（解決した問題・動機）

## 選んだアプローチとその理由
（なぜこの実装にしたか、制約・トレードオフ）

## 却下した代替案
（試して駄目だったこと、検討したが採用しなかった選択肢）

## 残った制約・注意点
（将来の自分が同じ判断を繰り返さないための警告）
```

3. ノート作成後、`docs/product-backlog.md` の `# PBI詳細` セクションから当該 PBI の記述を削除する

### ない場合 → ノート作成は任意

cc-sdd（SDD フロー）で実装した PBI は spec が記録を担うため省略可。
ただし実装中に非自明な判断・制約・却下案があった場合はノートを残すことを推奨する。
