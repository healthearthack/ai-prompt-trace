# Prompt Trace v2 shell integration. Generated placeholders are replaced by setup-wizard.sh.
PROMPT_TRACE_CLI='__CLI__'
PROMPT_TRACE_ACTOR='__ACTOR__'
PROMPT_TRACE_ENABLED=1
PROMPT_TRACE_LAST_HISTORY=''

prompt_trace() { python3 "$PROMPT_TRACE_CLI" "$@"; }
pt_pause() { PROMPT_TRACE_ENABLED=0; printf '%s\n' 'Prompt Trace paused'; }
pt_resume() { PROMPT_TRACE_ENABLED=1; printf '%s\n' 'Prompt Trace resumed'; }
pt_export() { prompt_trace export-csv "${1:-$HOME/prompt-trace.csv}"; }

_pt_record_bash() {
  status=$?
  [ "$PROMPT_TRACE_ENABLED" = 1 ] || return "$status"
  current=$(history 1 2>/dev/null | sed 's/^[[:space:]]*[0-9][0-9]*[[:space:]]*//')
  [ -n "$current" ] && [ "$current" != "$PROMPT_TRACE_LAST_HISTORY" ] || return "$status"
  PROMPT_TRACE_LAST_HISTORY=$current
  printf '%s' "$current" | python3 "$PROMPT_TRACE_CLI" record --source bash --path "$PWD" --exit-code "$status" --quiet 2>/dev/null || true
  return "$status"
}

_pt_zsh_command=''
_pt_zsh_preexec() { _pt_zsh_command=$1; }
_pt_zsh_precmd() {
  status=$?
  [ "$PROMPT_TRACE_ENABLED" = 1 ] && [ -n "$_pt_zsh_command" ] && printf '%s' "$_pt_zsh_command" | python3 "$PROMPT_TRACE_CLI" record --source zsh --path "$PWD" --exit-code "$status" --quiet 2>/dev/null || true
  _pt_zsh_command=''
}

if [ -n "${ZSH_VERSION:-}" ]; then
  autoload -Uz add-zsh-hook
  add-zsh-hook preexec _pt_zsh_preexec
  add-zsh-hook precmd _pt_zsh_precmd
  PROMPT="[PT:$PROMPT_TRACE_ACTOR] $PROMPT"
elif [ -n "${BASH_VERSION:-}" ]; then
  PROMPT_COMMAND="_pt_record_bash${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
  PS1="[PT:$PROMPT_TRACE_ACTOR] $PS1"
fi
