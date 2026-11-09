#!/usr/bin/env bash
# Fails if a personal email address or phone number is about to be published.
#
# Checks every tracked or new (non-ignored) file:
#   - text sources: any email address (except noreply, example and the public alias) and any UK mobile number
#   - PDF, Word and OpenDocument files: Anton's own email (the public alias excepted) and any UK mobile number
# Optional exact strings to look for, one per line, can go in local/contact-patterns.txt.
# That file is gitignored: it holds the real values, which must not be committed.
#
# Matches are reported as file:line only. CI logs of a public repo are public, so the matched text is never printed.

set -u
cd "$(git rev-parse --show-toplevel)"

EMAIL='[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
PUBLIC_ALIAS='anton\.dergunov\.public360@simplelogin\.com'
ALLOWED_EMAIL="(@(users\.noreply\.github\.com|example\.(com|org|net))|^$PUBLIC_ALIAS)\$"
OWN_EMAIL='dergunov[A-Za-z0-9._+-]*@'
PHONE='(\+|00)44[ .-]?\(?0?\)?[ .-]?7[0-9 .-]{8,12}|(^|[^0-9])07[0-9]{3}[ .-]?[0-9]{3}[ .-]?[0-9]{3}([^0-9]|$)'
LOCAL_PATTERNS=local/contact-patterns.txt

failures=0
report() { echo "private contact detail ($2): $1"; failures=$((failures + 1)); }

# Prints the lines of stdin that hold a disallowed email address.
disallowed_email_lines() {
  grep -nE "$EMAIL" | while IFS= read -r line; do
    n=${line%%:*}
    if grep -oE "$EMAIL" <<<"${line#*:}" | grep -vqE "$ALLOWED_EMAIL"; then echo "$n"; fi
  done
}

scan_stream() { # scan_stream <label> <kind: text|document>, content on stdin
  local label=$1 kind=$2 content n
  content=$(cat)
  if [ "$kind" = text ]; then
    while read -r n; do [ -n "$n" ] && report "$label:$n" email; done < <(disallowed_email_lines <<<"$content")
  else
    sed -E "s/$PUBLIC_ALIAS//g" <<<"$content" | grep -qE "$OWN_EMAIL" && report "$label" email
  fi
  while IFS=: read -r n _; do [ -n "$n" ] && report "$label:$n" phone; done < <(grep -nE "$PHONE" <<<"$content")
  if [ -f "$LOCAL_PATTERNS" ]; then
    while IFS=: read -r n _; do [ -n "$n" ] && report "$label:$n" "listed in $LOCAL_PATTERNS"; done \
      < <(grep -nFf "$LOCAL_PATTERNS" <<<"$content")
  fi
}

while IFS= read -r -d '' f; do
  [ -f "$f" ] || continue
  case "$f" in
    assets/js/*|*.min.*|node_modules/*|vendor/*) continue ;;
    *.md|*.markdown|*.html|*.yml|*.yaml|*.tex|*.txt|*.json|*.xml|*.css|*.csv|*.bib|*.rtf)
      scan_stream "$f" text < "$f" ;;
    *.pdf)
      if command -v pdftotext >/dev/null; then scan_stream "$f" document < <(pdftotext "$f" - 2>/dev/null)
      else echo "warning: pdftotext not found, skipping $f" >&2; fi ;;
    *.docx|*.odt)
      scan_stream "$f" document < <(unzip -p "$f" 2>/dev/null | tr -d '\000') ;;
  esac
done < <(git ls-files -co --exclude-standard -z)

if [ "$failures" -gt 0 ]; then
  echo "$failures private contact detail(s) found. Remove them, or use the contact page alias." >&2
  exit 1
fi
echo "No personal contact details found."
