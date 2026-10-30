#!/usr/bin/env bash
set -euo pipefail

# Mirror public pages and assets without changing the production site.
# Run on a machine with Internet access and GNU wget installed.
if [[ $# -ne 1 || -z "$1" ]]; then
  printf 'Usage: %s NEW_OUTPUT_DIRECTORY\n' "$0" >&2
  exit 2
fi
OUT="$1"
mkdir -p "$(dirname "$OUT")"
if ! mkdir "$OUT"; then
  printf 'Cannot create new capture directory: %s\n' "$OUT" >&2
  exit 1
fi

{
  printf 'Started: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'Target: https://agilewriters.com/\n'
  printf 'Options: mirror, page requisites, convert links, adjust extension, no parent, '
  printf 'domains=agilewriters.com,www.agilewriters.com, span hosts, robots=on, '
  printf 'wait=1 with random wait, timeout=20, tries=2\n'
  printf 'User agent: AgileWritersStaticArchive/1.0 (site-owner archival crawl)\n'
  wget --version | head -n 1
} > "$OUT/capture_metadata.txt"

finish() {
  status=$?
  trap - EXIT
  set +e
  printf 'Finished: %s\nWget exit status: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$status" >> "$OUT/capture_metadata.txt"
  find "$OUT" -type f | sort > "$OUT/file_inventory.txt"
  printf '\nCapture finished with status %s: %s\n' "$status" "$OUT"
  printf 'Log: %s/wget_log.txt\nInventory: %s/file_inventory.txt\n' "$OUT" "$OUT"
  if [[ -f "$OUT/wget_log.txt" ]]; then
    printf 'Possible failures in log:\n'
    grep -Ein '(^|[[:space:]])ERROR[[:space:]]|failed|timed out|unable to|HTTP request sent, awaiting response\.\.\. [45][0-9][0-9]' "$OUT/wget_log.txt" || true
  fi
  printf 'This is a capture, NOT a verified static deployment.\n'
  exit "$status"
}
trap finish EXIT

wget \
  --mirror \
  --page-requisites \
  --convert-links \
  --adjust-extension \
  --no-parent \
  --domains=agilewriters.com,www.agilewriters.com \
  --span-hosts \
  --restrict-file-names=unix \
  --execute robots=on \
  --wait=1 \
  --random-wait \
  --timeout=20 \
  --tries=2 \
  --user-agent='AgileWritersStaticArchive/1.0 (site-owner archival crawl)' \
  --directory-prefix="$OUT" \
  --output-file="$OUT/wget_log.txt" \
  https://agilewriters.com/
