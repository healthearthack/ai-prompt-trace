#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

printf '%s\n' 'PROMPT TRACE INSTALLATION WIZARD'
printf '%s\n' 'Binds one author ID to this device signing identity.'
printf '%s' 'Full display name: '
IFS= read -r DISPLAY_NAME
[ -n "$DISPLAY_NAME" ] || { printf '%s\n' 'Display name is required.' >&2; exit 1; }
printf '%s' 'Unique author ID (1-8 letters or numbers): '
IFS= read -r ACTOR
ACTOR=$(printf '%s' "$ACTOR" | tr '[:lower:]' '[:upper:]')
printf '%s' "$ACTOR" | grep -Eq '^[A-Z0-9]{1,8}$' || { printf '%s\n' 'Author ID must contain 1-8 alphanumeric characters.' >&2; exit 1; }
printf '%s\n' 'For teams, enter a shared mounted actors.json path. Press Enter for local only.'
printf '%s' 'Shared registry path (optional): '
IFS= read -r REGISTRY
TOKEN=''
if [ -n "$REGISTRY" ]; then
  printf '%s' 'Enterprise enrollment token (optional): '
  IFS= read -r TOKEN
fi
printf '%s\n' 'NOTICE: submitted shell commands and prompts are sanitized, stored, and signed.'
printf '%s\n' 'Detected passwords, passcodes, PINs, API keys, authorization values, and tokens become ****.'
printf '%s\n' 'Outputs, unsubmitted keystrokes, clipboard data, and file contents are not captured.'
printf '%s' 'Type I CONSENT to continue: '
IFS= read -r CONSENT
[ "$CONSENT" = 'I CONSENT' ] || { printf '%s\n' 'Consent not granted.' >&2; exit 1; }

INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/prompt-trace"
mkdir -p "$INSTALL_ROOT"
cp "$SCRIPT_DIR/prompt_trace.py" "$INSTALL_ROOT/prompt_trace.py"
if [ -n "$REGISTRY" ]; then
  if [ -n "$TOKEN" ]; then
    python3 "$INSTALL_ROOT/prompt_trace.py" init --actor "$ACTOR" --display-name "$DISPLAY_NAME" --registry "$REGISTRY" --enrollment-token "$TOKEN" --consent
  else
    python3 "$INSTALL_ROOT/prompt_trace.py" init --actor "$ACTOR" --display-name "$DISPLAY_NAME" --registry "$REGISTRY" --consent
  fi
else
  python3 "$INSTALL_ROOT/prompt_trace.py" init --actor "$ACTOR" --display-name "$DISPLAY_NAME" --consent
fi

INTEGRATION="$INSTALL_ROOT/shell-integration.sh"
sed "s/__ACTOR__/$ACTOR/g; s|__CLI__|$INSTALL_ROOT/prompt_trace.py|g" "$SCRIPT_DIR/shell-integration.sh" > "$INTEGRATION"
SHELL_RC="$HOME/.bashrc"
case "${SHELL:-}" in *zsh) SHELL_RC="$HOME/.zshrc";; esac
LINE=". \"$INTEGRATION\""
grep -F "$LINE" "$SHELL_RC" >/dev/null 2>&1 || printf '\n%s\n' "$LINE" >> "$SHELL_RC"
printf '%s\n' "Configured Prompt Trace for $ACTOR. Open a new terminal."
printf '%s\n' 'Controls: pt_pause, pt_resume, pt_export'
