# Private bundle ownership uses SHA-256 followed by a relative path (spaces allowed).
resource_sha256() (
  if command -v sha256sum >/dev/null 2>&1; then
    resource_digest=$(sha256sum "$1") || exit 1
  else
    resource_digest=$(shasum -a 256 "$1") || exit 1
  fi
  printf '%s\n' "${resource_digest%% *}"
)
sync_agent_resources() (
  resource_source=$1
  resource_destination=$2
  [ -d "$resource_source" ] || return 0
  mkdir -p "$resource_destination"
  resource_manifest="$resource_destination/.agent-resources-manifest"
  resource_cursor="$resource_manifest"
  while [ "$resource_cursor" != / ] && [ "$resource_cursor" != . ]; do
    [ ! -L "$resource_cursor" ] || { printf 'Resource ownership path contains a link: %s\n' "$resource_cursor" >&2; exit 1; }
    resource_parent=${resource_cursor%/*}
    [ "$resource_parent" != "$resource_cursor" ] || break
    [ -n "$resource_parent" ] || resource_parent=/
    resource_cursor=$resource_parent
  done
  resource_next=$(mktemp)
  trap 'rm -f "$resource_next"' EXIT HUP INT TERM
  resource_path_safe() {
    case "$1" in /*|*\\*|*:*|../*|*/../*|*/..|./*|*/./*|*/.|*//*|.*|*/*) ;; *) return 1 ;; esac
    case "$1" in /*|*\\*|*:*|../*|*/../*|*/..|./*|*/./*|*/.|*//*|.*) return 1 ;; esac
    resource_cursor="$resource_destination/$1"
    while [ "$resource_cursor" != "$resource_destination" ]; do
      [ ! -L "$resource_cursor" ] || return 1
      resource_parent=${resource_cursor%/*}
      [ "$resource_parent" != "$resource_cursor" ] || return 1
      [ -n "$resource_parent" ] || resource_parent=/
      resource_cursor=$resource_parent
    done
    [ ! -L "$resource_destination" ]
  }
  for resource_bundle in "$resource_source"/*; do
    [ -d "$resource_bundle" ] || continue
    [ -f "$resource_bundle.md" ] || continue
    find "$resource_bundle" -type f -print | while IFS= read -r resource_file; do
      resource_key=${resource_file#"$resource_source"/}
      resource_path_safe "$resource_key" || { printf 'Unsafe resource path: %s\n' "$resource_key" >&2; exit 1; }
      resource_target="$resource_destination/$resource_key"
      resource_hash=$(resource_sha256 "$resource_file")
      resource_old=
      if [ -f "$resource_manifest" ]; then
        while IFS= read -r resource_record; do
          if [ "${resource_record#* }" = "$resource_key" ]; then
            resource_old=${resource_record%% *}
            break
          fi
        done < "$resource_manifest"
      fi
      if [ ! -e "$resource_target" ] || cmp -s "$resource_file" "$resource_target" || { [ -n "$resource_old" ] && [ "$(resource_sha256 "$resource_target")" = "$resource_old" ]; }; then
        mkdir -p "${resource_target%/*}"
        cp "$resource_file" "$resource_target"
        printf '%s %s\n' "$resource_hash" "$resource_key" >> "$resource_next"
      else
        printf 'Preserved user resource: %s\n' "$resource_target" >&2
      fi
    done
  done
  if [ -f "$resource_manifest" ]; then
    while IFS= read -r resource_line; do
      resource_hash=${resource_line%% *}
      resource_key=${resource_line#* }
      resource_path_safe "$resource_key" || { printf 'Unsafe resource manifest path: %s\n' "$resource_key" >&2; exit 1; }
      # A removed/renamed bundle is no longer paired with a source persona.
      resource_name=${resource_key%%/*}
      if [ ! -f "$resource_source/$resource_key" ] || [ ! -f "$resource_source/$resource_name.md" ]; then
        resource_target="$resource_destination/$resource_key"
        if [ -f "$resource_target" ] && [ "$(resource_sha256 "$resource_target")" = "$resource_hash" ]; then
          rm -f "$resource_target"
        fi
      fi
    done < "$resource_manifest"
  fi
  sort "$resource_next" > "$resource_manifest"
)
