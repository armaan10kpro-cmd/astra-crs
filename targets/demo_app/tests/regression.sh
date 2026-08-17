#!/usr/bin/env bash
# Regression tests for demo_vuln — legitimate behaviour only
set -euo pipefail
BIN="${1:-./demo_vuln}"

pass=0
fail=0

check() {
  local input="$1"
  local expected="$2"
  set +e
  "$BIN" "$input" >/dev/null 2>&1
  local rc=$?
  set -e
  if [[ "$rc" == "$expected" ]]; then
    echo "PASS: len=${#input} rc=$rc"
    pass=$((pass + 1))
  else
    echo "FAIL: input='$input' expected=$expected got=$rc"
    fail=$((fail + 1))
  fi
}

check "OK" "$(printf '%d' "'O")"
check "PING" "$(printf '%d' "'P")"
check "STATUS" "$(printf '%d' "'S")"
check "HELLO" "$(printf '%d' "'H")"

long31=$(python3 -c "print('A'*31)")
check "$long31" "$(printf '%d' "'A")"

echo "Regression: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
