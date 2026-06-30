# ADR-0009: LLM 処理完了・承認待ち時の通知音

## ステータス

保留（DevContainer 環境の制約により後回し）

## コンテキスト

PBI-ph0-008 として、長い LLM 処理の完了時や承認待ちの中断時に効果音を鳴らし、ユーザーが気づけるようにしたい。

### 調査した方式

#### 1. Terminal Bell（`printf '\a'`）

Claude Code の `preferredNotifChannel terminal_bell` 設定で組み込みの BEL 文字送出を使う方式。

- VS Code 側で `accessibility.signals.terminalBell.sound` を `on` に変更する必要がある（デフォルトの `auto` はスクリーンリーダー接続時のみ有効）
- VS Code ターミナルから直接 `printf '\a'` を実行すると鳴る
- Claude Code の Bash ツール経由では鳴らない（stdout がターミナルに直接接続されていないため）
- Claude Code 組み込みの `preferredNotifChannel terminal_bell` が BEL を送れるかは未検証

#### 2. Claude Code Hooks（`Stop` / `Notification` イベント）

`Stop`（処理完了）と `Notification`（`permission_prompt`、`idle_prompt`）に hook を設定する方式。

- hook 内のコマンドも Bash ツールと同様にサブプロセスで実行されるため、BEL 文字がターミナルに届かない可能性がある
- DevContainer 内にはオーディオデバイス（`/dev/snd`）、PulseAudio、X11/Wayland いずれも存在せず、`afplay`/`paplay` 等の音声再生コマンドが使えない

#### 3. VS Code Extension「Claude Notifier」

DevContainer 対応あり（Remote audio 機能: `cn-daemon` + SSH リバースフォワード）。イベントごとに異なるサウンドプリセットを設定可能。ただし daemon のセットアップが必要。

#### 4. Host 側 HTTP サーバー方式

Host 側に簡易 HTTP サーバーを立て、DevContainer からの HTTP リクエストをトリガーに Host 側で通知音を再生する構成。DevContainer 環境での最も確実な方式。

### 根本的な制約

DevContainer（Linux コンテナ）には以下が存在しない：

- オーディオデバイス（`/dev/snd`）
- PulseAudio / PipeWire
- X11 / Wayland ディスプレイサーバー

コンテナ内から直接音声を再生する手段がなく、何らかの方法で Host 側に通知を転送する必要がある。

## 決定

後回しにする。DevContainer 環境で通知音を実現するには Host 側に HTTP サーバーを立てる構成がベストだが、現時点ではセットアップコストに見合わない。

## 今後のオプション

優先度が上がった場合の候補：

1. Host 側 HTTP サーバー + Claude Code Hooks から HTTP リクエスト
2. Claude Notifier VS Code Extension（`cn-daemon` セットアップ）
3. `preferredNotifChannel terminal_bell` の動作検証（Claude Code 組み込みの BEL 送出が DevContainer で機能するか）

## 参照

- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Configure your terminal for Claude Code](https://code.claude.com/docs/en/terminal-config)
- [Claude Notifier - VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=SingularityInc.claude-notifier)
- [Smart Notifications (wmedia.es)](https://wmedia.es/en/tips/claude-code-notify-when-done)
