#!/bin/sh
# Installs the pre-commit, commit-msg and pre-push hooks that run the privacy guard.
# Hooks go where git looks for them: a linked worktree shares the main repo's hooks, and a
# repo-local core.hooksPath is honored. A global or system core.hooksPath is refused, because
# these hooks would then run in every other repository on the machine. Nothing is written unless
# all three targets are free or were installed by this script, so an install is never partial.
set -e
SENTINEL="# installed by persona-debate-lab guard"

scope="$(git config --show-scope --get core.hooksPath 2>/dev/null | cut -f1)"
case "$scope" in
  ""|local|worktree) ;;
  *) echo "refusing: core.hooksPath is set in $scope config; hooks there would run in every repository" >&2
     exit 1 ;;
esac

hooks="$(git rev-parse --path-format=absolute --git-path hooks)"
mkdir -p "$hooks"

foreign=""
for name in pre-commit commit-msg pre-push; do
  if [ -e "$hooks/$name" ] && ! grep -qxF "$SENTINEL" "$hooks/$name"; then
    echo "refusing to replace an existing $name hook: $hooks/$name" >&2
    foreign=1
  fi
done
[ -z "$foreign" ] || exit 1

install_hook() {
  printf '#!/bin/sh\n%s\n%s\n' "$SENTINEL" "$2" > "$hooks/$1"
  chmod +x "$hooks/$1"
  echo "$1 hook installed: $hooks/$1"
}

# pre-commit scans the staged changes, commit-msg the message, and pre-push every outgoing
# commit: the last local point before anything is public.
install_hook pre-commit 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --staged'
install_hook commit-msg 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --message "$1"'
install_hook pre-push 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --pre-push "$1"'
