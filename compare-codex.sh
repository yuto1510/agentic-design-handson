#!/usr/bin/env bash
# Codex で比較する。中身は compare.sh。
AGENT=codex exec "$(dirname "$0")/compare.sh" "$@"
