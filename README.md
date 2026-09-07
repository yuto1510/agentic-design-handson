# Agentic System 設計ハンズオン（論文検索）

「LLM でできる処理」と「LLM に任せるべき処理」は同じではない、
ということを Claude Code で体験する最小構成のハンズオンです。

> **このファイルと `WORKSHOP.md` は参加者（人間）向けです。**
> Claude Code からは読めないように設定してあります（`.claude/settings.json` / `AGENTS.md`）。
> Claude に渡す指示は、すべて `WORKSHOP.md` のプロンプトをコピペして与えてください。

**進行は [WORKSHOP.md](WORKSHOP.md) だけを読めば進められます。まずそこを開いてください。**

- エージェント向けのルール: [AGENTS.md](AGENTS.md)（Claude Code は [CLAUDE.md](CLAUDE.md) 経由で読み込む）
- ブランチ: `agentic`（スターター） / `deterministic`（Step 5 で見る解答例）
- 依存: Python 3 標準ライブラリのみ

## ユーザー要求（両ブランチ共通）

> 2024年以降に公開された Agent 関連の論文で、日本の研究機関に所属する著者が含まれ、
> retracted ではない論文をすべて取得してください

## データ (`data/`)

`papers.json` / `authors.json` / `retractions.json` の 3 ファイル。
参加者も Claude も中身は直接見ず、用意されたインターフェース経由でのみ触ります。
