#!/usr/bin/env bash
# Claude Code で比較する。中身は compare.sh。
AGENT=claude exec "$(dirname "$0")/compare.sh" "$@"
