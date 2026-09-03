#!/bin/sh
# Throwaway check: the fix_refs sed expression must rewrite the path but keep
# the surrounding markdown backticks intact.
bt='`'
printf 'See %s%s%s.\n' "$bt" ".codebuddy/references/x.md" "$bt" |
  sed "s#[^[:space:]$bt]*references/x.md#../../references/x.md#g"
