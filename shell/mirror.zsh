autoload -Uz add-zsh-hook
zmodload zsh/datetime

typeset -g MIRROR_SESSION_ID="${MIRROR_SESSION_ID:-$$-$EPOCHSECONDS-$RANDOM}"

mirror_preexec() {
    typeset -g MIRROR_STARTED="$EPOCHREALTIME"
}

mirror_precmd() {
    local mirror_exit=$?
    if [[ -n "${MIRROR_STARTED:-}" ]]; then
        local mirror_ended="$EPOCHREALTIME"
        command "${MIRROR_BIN:-mirror}" record \
            --session "$MIRROR_SESSION_ID" \
            --started "$MIRROR_STARTED" \
            --ended "$mirror_ended" \
            --status "$mirror_exit" \
            --cwd "$PWD" >/dev/null 2>&1
        command "${MIRROR_BIN:-mirror}" observe --auto
        unset MIRROR_STARTED
    fi
    return 0
}

add-zsh-hook preexec mirror_preexec
add-zsh-hook precmd mirror_precmd

command "${MIRROR_BIN:-mirror}" observe --startup
