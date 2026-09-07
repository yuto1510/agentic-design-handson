#!/usr/bin/env bash
# 同じ要求を、同じエージェントに 2 通りの道具立てで解かせて並べる。
#   改善前: エージェント + tools.py（低レベル。判断はすべてエージェント側）
#   改善後: エージェント + 参加者が作った仕組み（判断の一部が Python 側）
# どちらもエージェントを通す。違うのは渡す道具だけ。
#
#   ./compare-claude.sh "python3 pipeline.py --query-file query.json"   # Windows は python
#   ./compare-codex.sh  "python3 pipeline.py --query-file query.json"
#
# 直接 ./compare.sh を呼んでもよい（既定は claude、AGENT=... で切り替え）。
set -u
# mktemp -d は BSD（macOS）だとテンプレート必須の場合があるのでフォールバックする
OUT=$(mktemp -d 2>/dev/null || mktemp -d -t compare)

# python の名前は環境で違う（Windows は python3 が無い）。PY=python などで上書きできる。
if [ -z "${PY:-}" ]; then
  if command -v python3 >/dev/null; then PY=python3
  elif command -v python >/dev/null; then PY=python
  else echo "python が見つかりません。PY=<コマンド名> で指定してください。" >&2; exit 1; fi
fi
AGENT=${AGENT:-claude}

REQUEST='「2024年以降に公開された Agent 関連の論文で、日本の研究機関に所属する著者が含まれ、
retracted ではない論文をすべて取得してください」'
COMMON='制約: data/ の中身を直接見ない。内部実装から答えを導かない。他ブランチや WORKSHOP.md / README.md を見ない。
最終行に "paper_id: ..." の形で結果を出力してください。'

BEFORE="このリポジトリの tools.py が提供するインターフェースだけを使って、次の要求に答えてください。
${REQUEST}
${COMMON}
コマンドは \"${PY} tools.py ...\" の単一コマンドだけを使い、パイプ・ループ・${PY} -c は使わないこと。"

if ! command -v "$AGENT" >/dev/null; then
  echo "$AGENT コマンドが見つかりません。" >&2; exit 1
fi
if [ ! -d data ]; then
  echo "data/ が見つかりません。リポジトリのルートで実行してください。" >&2; exit 1
fi

ids() {   # 最終回答行から paper_id を拾う
  local line
  line=$(grep -i 'paper_id' "$1" | tail -1)
  [ -z "$line" ] && line=$(cat "$1")
  grep -oE 'p0[0-9]{2}' <<<"$line" | sort -u | tr '\n' ' '
}

# $1=タグ  $2=プロンプト  $3=許可する Bash コマンドの接頭辞
run_agent() {
  local tag=$1 prompt=$2 pattern=$3 start
  start=$(date +%s)
  case "$AGENT" in
    claude)
      claude -p "$prompt" --allowedTools "Bash(${pattern}:*),Bash(echo:*)" --permission-mode acceptEdits \
        --output-format json > "$OUT/$tag.json" 2>"$OUT/$tag.err" || true
      "$PY" - "$OUT/$tag.json" "$OUT/$tag.txt" "$OUT/$tag.turns" <<'PYJSON' || true
import json, sys
d = json.load(open(sys.argv[1]))
open(sys.argv[2], "w").write(d.get("result") or "")
open(sys.argv[3], "w").write(str(d.get("num_turns", "?")))
PYJSON
      ;;
    codex) codex exec "$prompt" > "$OUT/$tag.txt" 2>&1 || true ;;
    *)     "$AGENT" "$prompt" > "$OUT/$tag.txt" 2>&1 || true ;;
  esac
  echo $(( $(date +%s) - start )) > "$OUT/$tag.sec"
}

report() {  # $1=見出し  $2=タグ
  local turns sec got
  turns=$(cat "$OUT/$2.turns" 2>/dev/null || echo "計測不可（${AGENT} は回数を出力しない）")
  sec=$(cat "$OUT/$2.sec" 2>/dev/null || echo "?")
  got=$(ids "$OUT/$2.txt")
  echo "=== $1 ==="
  printf 'エージェントのやりとり %s 回 / 所要 %s 秒\n' "$turns" "$sec"
  printf '結果: %s\n' "${got:-（結果なし: $OUT/$2.txt を確認）}"
}

echo "改善前を実行中（1〜2 分）..."
run_agent before "$BEFORE" "$PY tools.py"

if [ $# -ge 1 ]; then
  AFTER="このリポジトリには、次のコマンドで動く論文検索の仕組みがあります。
  $1
この仕組みを使って、次の要求に答えてください。
${REQUEST}
仕組みが必要とする入力（構造化クエリなど）が要るなら、あなたが用意してください。
${COMMON}"
  echo "改善後を実行中..."
  run_agent after "$AFTER" "$(echo "$1" | awk '{print $1" "$2}')"
fi

echo
report "改善前: ${AGENT} + tools.py（低レベル）" before
if [ $# -ge 1 ]; then
  echo
  report "改善後: ${AGENT} + $(echo "$1" | awk '{print $2}')（高レベル）" after
  echo
  if [ "$(ids "$OUT/before.txt")" = "$(ids "$OUT/after.txt")" ]; then
    echo "結果は同じ。違うのは、エージェントが判断した回数。"
  else
    echo "結果が違う。出力の除外理由を読んで、どちらが要求に合っているか確認する。"
  fi
fi
echo
echo "出力は $OUT に残してあります"
