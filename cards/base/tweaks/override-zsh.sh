# Switch interactive bash sessions to zsh on bootc systems, where chsh is not useful.

case "$-" in
  *i*) ;;
  *) return 0 ;;
esac

[ -n "${BASH_VERSION:-}" ] || return 0
[ -z "${BASH_EXECUTION_STRING:-}" ] || return 0
[ "${ANATASE_AUTO_ZSH:-1}" != 0 ] || return 0
[ ! -e "${HOME}/.no-anatase-zsh" ] || return 0
[ -z "${ANATASE_ZSH_ENTERED:-}" ] || return 0
command -v zsh >/dev/null 2>&1 || return 0

export ANATASE_ZSH_ENTERED=1
if shopt -q login_shell; then
    exec zsh -l
else
    exec zsh
fi
