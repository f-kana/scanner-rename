# 分類未了の場合に探索を拒否する

## Prompt

「完了通知の仕組みが欲しいんだけど、良いのないか探して」
classifying-harnessの分類はまだ行っていない。

## Expected behavior

- classifying-harnessの分類が未了であることを指摘する
- 独断で候補検索に進まない
- 分類仮説を置く場合は仮説であることを明示する（例: Hook / slash command / MCP のいずれかになりうる）
- classifying-harnessの実施を促す、または分類仮説を置いてユーザーに確認する

## Failure behavior to avoid

- 分類なしにいきなりGitHub検索を始める
- 分類を飛ばして「このMCP serverが良い」と結論する
- 分類仮説を断定として扱う

## Pass criteria

- 分類未了への言及がある
- 候補の最終推奨の前に分類の確認または仮説提示がある

## Negative case

classifying-harnessで「カテゴリ3: Hook」と明確に分類済みの場合。
この場合は分類確認を省略してHook候補の探索に直接入るべき。
