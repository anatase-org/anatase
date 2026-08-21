# Switch interactive bash sessions to zsh on bootc systems, where chsh is not useful.
# Also wrap systemd-inhibit over ssh, so devices don't sleep while SSH is active

case "$-" in
  *i*) ;;
  *) return 0 ;;
esac

[ -n "${BASH_VERSION:-}" ] || return 0
[ -z "${BASH_EXECUTION_STRING:-}" ] || return 0
[ "${ANATASE_AUTO_ZSH:-1}" != 0 ] || return 0
[ ! -e "${HOME}/.no-anatase-zsh" ] || return 0
[ -z "${ANATASE_ZSH_ENTERED:-}" ] || return 0
anatase_zsh_path=$(command -v zsh) || return 0

# Existing users may not have inherited .zshrc from /etc/skel. Without it,
# zsh opens its new-user configuration wizard before loading /etc/zshrc.
anatase_zdotdir=${ZDOTDIR:-$HOME}
if [ ! -e "${anatase_zdotdir}/.zshrc" ]; then
    touch "${anatase_zdotdir}/.zshrc" 2>/dev/null || true
fi

export ANATASE_ZSH_ENTERED=1
export SHELL="$anatase_zsh_path"
if shopt -q login_shell; then
    anatase_zsh=("$anatase_zsh_path" -l)
else
    anatase_zsh=("$anatase_zsh_path")
fi

if [ "${ANATASE_SSH_NOSLEEP:-1}" != 0 ] \
    && [ -n "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] \
    && command -v systemd-inhibit >/dev/null 2>&1; then
    exec systemd-inhibit \
        --what=idle \
        --mode=block \
        --who=sshd \
        --why="SSH session active" \
        "${anatase_zsh[@]}"
fi

exec "${anatase_zsh[@]}"
