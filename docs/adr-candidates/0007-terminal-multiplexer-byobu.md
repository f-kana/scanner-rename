# ADR-0007: Terminal Multiplexer - byobu

## ステータス

候補（調査完了）

## コンテキスト

PBI-ph0-007-2 として、tmux の代替・補完候補として byobu を調査した。byobu は tmux（または GNU Screen）をラップする設定フレームワークであり、tmux の代替ではなく拡張層である。

### byobu の特徴

#### アーキテクチャ

```
Your shell (bash/zsh) → byobu (wrapper) → tmux/screen (backend)
```

byobu は tmux をバックエンドとして使用し、その上に以下を追加する：

- F-key ベースのキーバインディング（プレフィックスキー不要）
- 2行のリッチステータスバー（CPU、メモリ、ディスク、ネットワーク、バッテリーなど 40+ の指標）
- インタラクティブな設定 UI（F9 メニュー）
- プロファイル管理とレイアウト保存
- 自動ログイン統合（`byobu-enable`）

#### キーバインディングの違い

**tmux**：

- プレフィックスキー（`Ctrl-b`）が必要
- 新規ウィンドウ作成: `Ctrl-b` `c`
- ペイン水平分割: `Ctrl-b` `"`
- ペイン垂直分割: `Ctrl-b` `%`

**byobu**：

- F-key を直接使用（プレフィックス不要）
- 新規ウィンドウ作成: `F2`
- ペイン水平分割: `Shift-F2`
- ペイン垂直分割: `Ctrl-F2`
- 設定メニュー: `F9`
- ヘルプ: `F1`

#### ステータスバー

tmux は最小限のステータス表示のみ。byobu は 2行のリッチステータスバーを提供：

- CPU 使用率、温度、周波数
- メモリ、スワップ使用率
- ディスク使用率、I/O スループット
- ネットワーク帯域（アップロード/ダウンロード）
- バッテリー状態
- システムロードアベレージ
- 再起動要否、利用可能な更新
- カスタムスクリプト（`~/.byobu/bin/N_NAME` 形式）

各指標は F9 メニューから個別に有効化/無効化可能。

#### 設定管理

**tmux**：

- `~/.tmux.conf` を手動編集
- 設定変更には構文知識が必要

**byobu**：

- F9 で TUI（テキストベース UI）を開いて対話的に設定
- ファイル編集不要
- `~/.byobu/` ディレクトリで管理
- プロファイルとテーマの切り替えが容易

### 開発ワークフローでの位置づけ

2026年時点での評価：

**コミュニティとエコシステム**（[tmux vs byobu comparison](https://appmus.com/vs/tmux-vs-byobu), [Slant comparison](https://www.slant.co/versus/11858/11861/~tmux_vs_byobu)）：

- tmux：最大のコミュニティ、最も充実したドキュメント、ユニバーサルなサーバー可用性、成熟したプラグイン/スクリプトエコシステム
- byobu：Ubuntu Server コミュニティで人気、ドキュメントは豊富だがカスタマイズ性は低い

**学習曲線**：

- byobu：F-key バインディングとヘルプメニューで初心者に優しい。ただし、パワーユーザーにとっては F-key が邪魔になることも
- tmux：設定が必要だがカスタマイズ性が高く、他システムへの移植性が高い

**パフォーマンス**：

- byobu のステータスバーは 1秒ごとに外部スクリプトを実行（多数の fork と script 解釈）
- CPU 集約的なカスタムスクリプトはシステム全体のパフォーマンスに影響する可能性

**移植性**：

- tmux：ほぼすべての Unix/Linux システムで利用可能、設定ファイルの互換性が高い
- byobu：主に Debian/Ubuntu ベース、他ディストリビューションでは追加インストールが必要

## 決定

**byobu を DevContainer にインストールする。** tmux、byobu、zellij の3つを並行して提供し、開発者が好みのツールを選択できるようにする。

### 理由

1. **開発者の選択肢を広げる**
   - tmux：カスタマイズ性重視、プレフィックスキー方式に慣れている開発者向け
   - byobu：F-key ベースの直感的な操作、リッチなステータスバーを好む開発者向け
   - zellij：モダンな UI と操作性を好む開発者向け

2. **byobu の利点**
   - F-key で直接操作できるため、プレフィックスキーを覚える必要がない
   - F1 でヘルプが表示され、初心者に優しい
   - ステータスバーでシステムリソースを可視化できる（開発中のパフォーマンス監視に有用）
   - F9 メニューで対話的に設定変更可能

3. **tmux との共存**
   - byobu は tmux をバックエンドとして使用するため、技術的に競合しない
   - `~/.tmux.conf` と `~/.byobu/` は独立して管理される
   - ユーザーは `tmux` または `byobu` コマンドで明示的に起動方法を選択できる

4. **インストールコスト**
   - Debian パッケージで提供されており、`apt-get install byobu` で簡単にインストール可能
   - 依存関係も少なく、DevContainer のビルド時間への影響は最小限

## 実装

### Dockerfile への追加

`.devcontainer/Dockerfile` に byobu のインストールを追加：

```dockerfile
RUN apt-get update && apt-get install -y \
    byobu \
    && rm -rf /var/lib/apt/lists/*
```

### 使い分け

開発者は以下のように使い分けられる：

- tmux を使いたい場合: `tmux` コマンドで起動
- byobu を使いたい場合: `byobu` コマンドで起動
- zellij を使いたい場合: `zellij` コマンドで起動（PBI-ph0-007-3 で実装予定）

### デフォルトの挙動

自動起動は設定せず、開発者が明示的にコマンドを実行する方式とする。これにより：

- ツールの押し付けを避ける
- 各開発者が好みのツールを選択できる
- 誤って複数のマルチプレクサが入れ子になることを防ぐ

## 結果

- byobu を DevContainer にインストール
- tmux、byobu、zellij を並行提供し、開発者の選択肢を最大化
- `.devcontainer/README.md` に各ツールの基本的な使い方を記載

## 参照

- [Byobu official site](https://byobu.org/)
- [tmux vs byobu Comparison (2026)](https://appmus.com/vs/tmux-vs-byobu)
- [tmux Alternatives — tmux vs Screen vs Zellij vs Byobu (2026)](https://tmux.app/alternatives/)
- [Slant: tmux vs Byobu detailed comparison as of 2026](https://www.slant.co/versus/11858/11861/~tmux_vs_byobu)
- [Ubuntu Server docs: Terminal multiplexers](https://ubuntu.com/server/docs/reference/other-tools/terminal-multiplexers/)
