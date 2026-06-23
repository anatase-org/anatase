# Anatase zsh defaults.

case $- in
  *i*) ;;
  *) return 0 ;;
esac

anatase_zsh_dir=/usr/share/anatase/zsh

#
# Basic theming
#

autoload -Uz colors
colors
setopt prompt_subst

typeset -AHg FG BG
for anatase_color in {000..255}; do
  FG[$anatase_color]="%F{$anatase_color}"
  BG[$anatase_color]="%K{$anatase_color}"
done
unset anatase_color

anatase_git_prompt_info() {
  command git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return

  local ref dirty
  ref=$(command git symbolic-ref --short HEAD 2>/dev/null) ||
    ref=$(command git describe --tags --exact-match HEAD 2>/dev/null) ||
    ref=$(command git rev-parse --short HEAD 2>/dev/null) ||
    return

  if ! command git diff --no-ext-diff --quiet --ignore-submodules -- 2>/dev/null ||
      ! command git diff --no-ext-diff --cached --quiet --ignore-submodules -- 2>/dev/null ||
      [[ -n "$(command git ls-files --others --exclude-standard 2>/dev/null)" ]]; then
    dirty=$ZSH_THEME_GIT_PROMPT_DIRTY
  else
    dirty=$ZSH_THEME_GIT_PROMPT_CLEAN
  fi

  print -r -- "${ZSH_THEME_GIT_PROMPT_PREFIX}${ref//\%/%%}${dirty}${ZSH_THEME_GIT_PROMPT_SUFFIX}"
}

git_prompt_info() {
  anatase_git_prompt_info
}

hg_prompt_info() {
  return 0
}

virtualenv_prompt_info() {
  [[ -n ${VIRTUAL_ENV:-} ]] || return
  print -r -- "${ZSH_THEME_VIRTUALENV_PREFIX=[}${VIRTUAL_ENV_PROMPT:-${VIRTUAL_ENV:t:gs/%/%%}}${ZSH_THEME_VIRTUALENV_SUFFIX=]}"
}

export VIRTUAL_ENV_DISABLE_PROMPT=1

anatase_afmagic_dashes() {
  local python_env_dir="${VIRTUAL_ENV:-$CONDA_DEFAULT_ENV}"
  local python_env="${python_env_dir##*/}"

  if [[ -n "$python_env" && "$PS1" = *\(${python_env}\)* ]]; then
    print -- $(( COLUMNS - ${#python_env} - 3 ))
  elif [[ -n "${VIRTUAL_ENV_PROMPT:-}" && "$PS1" = *${VIRTUAL_ENV_PROMPT}* ]]; then
    print -- $(( COLUMNS - ${#VIRTUAL_ENV_PROMPT} - 3 ))
  else
    print -- "$COLUMNS"
  fi
}

anatase_configure_afmagic() {
  PS1="${FG[237]}\${(l.\$(anatase_afmagic_dashes)..-.)}%f%k
${FG[032]}%~\$(git_prompt_info)\$(hg_prompt_info) ${FG[105]}%(!.#.»)%f%k "
  PS2="%F{red}\\ %f%k"

  RPS1="%(?..%F{red}%? ↵%f%k)"
  RPS1+='$(virtualenv_prompt_info)'
  RPS1+=" ${FG[237]}%n@%m%f%k"

  ZSH_THEME_GIT_PROMPT_PREFIX=" ${FG[075]}(${FG[078]}"
  ZSH_THEME_GIT_PROMPT_CLEAN=""
  ZSH_THEME_GIT_PROMPT_DIRTY="${FG[214]}*%f%k"
  ZSH_THEME_GIT_PROMPT_SUFFIX="${FG[075]})%f%k"

  ZSH_THEME_VIRTUALENV_PREFIX=" ${FG[075]}["
  ZSH_THEME_VIRTUALENV_SUFFIX="]%f%k"
}

anatase_configure_powerlevel10k() {
  local background_color=8
  local foreground_color=254
  local foreground_color_weaker=250
  local foreground_color_stronger=255

  unset -m '(POWERLEVEL9K_*|DEFAULT_USER)~POWERLEVEL9K_GITSTATUS_DIR'

  autoload -Uz is-at-least
  is-at-least 5.1 || return

  typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(
    os_icon
    dir
    vcs
  )

  typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
    status
    command_execution_time
    background_jobs
    direnv
    asdf
    virtualenv
    anaconda
    pyenv
    goenv
    nodenv
    nvm
    nodeenv
    rbenv
    rvm
    fvm
    luaenv
    jenv
    plenv
    phpenv
    scalaenv
    haskell_stack
    kubecontext
    terraform
    aws
    aws_eb_env
    azure
    gcloud
    google_app_cred
    context
    ranger
    nnn
    vim_shell
    midnight_commander
    nix_shell
    vi_mode
    todo
    timewarrior
    taskwarrior
  )

  typeset -g POWERLEVEL9K_MODE=nerdfont-complete
  typeset -g POWERLEVEL9K_ICON_PADDING=none
  typeset -g POWERLEVEL9K_ICON_BEFORE_CONTENT=
  typeset -g POWERLEVEL9K_PROMPT_ADD_NEWLINE=true

  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_PREFIX='%242F╭─'
  typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_PREFIX='%242F├─'
  typeset -g POWERLEVEL9K_MULTILINE_LAST_PROMPT_PREFIX='%242F╰─'
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_SUFFIX='%242F─╮'
  typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_SUFFIX='%242F─┤'
  typeset -g POWERLEVEL9K_MULTILINE_LAST_PROMPT_SUFFIX='%242F─╯'
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_CHAR=' '
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_BACKGROUND=
  typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_GAP_BACKGROUND=

  typeset -g POWERLEVEL9K_LEFT_SUBSEGMENT_SEPARATOR='\u2571'
  typeset -g POWERLEVEL9K_RIGHT_SUBSEGMENT_SEPARATOR='\u2571'
  typeset -g POWERLEVEL9K_LEFT_SEGMENT_SEPARATOR='\uE0BC'
  typeset -g POWERLEVEL9K_RIGHT_SEGMENT_SEPARATOR='\uE0BA'
  typeset -g POWERLEVEL9K_LEFT_PROMPT_LAST_SEGMENT_END_SYMBOL='\uE0BC'
  typeset -g POWERLEVEL9K_RIGHT_PROMPT_FIRST_SEGMENT_START_SYMBOL='\uE0BA'
  typeset -g POWERLEVEL9K_LEFT_PROMPT_FIRST_SEGMENT_START_SYMBOL='\uE0BA'
  typeset -g POWERLEVEL9K_RIGHT_PROMPT_LAST_SEGMENT_END_SYMBOL='\uE0BC'
  typeset -g POWERLEVEL9K_EMPTY_LINE_LEFT_PROMPT_LAST_SEGMENT_END_SYMBOL=

  typeset -g POWERLEVEL9K_OS_ICON_FOREGROUND=232
  typeset -g POWERLEVEL9K_OS_ICON_BACKGROUND=255

  typeset -g POWERLEVEL9K_DIR_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_DIR_FOREGROUND=$foreground_color
  typeset -g POWERLEVEL9K_SHORTEN_STRATEGY=truncate_to_unique
  typeset -g POWERLEVEL9K_SHORTEN_DELIMITER=
  typeset -g POWERLEVEL9K_DIR_SHORTENED_FOREGROUND=$foreground_color_weaker
  typeset -g POWERLEVEL9K_DIR_ANCHOR_FOREGROUND=$foreground_color_stronger
  typeset -g POWERLEVEL9K_DIR_ANCHOR_BOLD=true
  typeset -g POWERLEVEL9K_DIR_TRUNCATE_BEFORE_MARKER=false
  typeset -g POWERLEVEL9K_SHORTEN_DIR_LENGTH=1
  typeset -g POWERLEVEL9K_DIR_MAX_LENGTH=80
  typeset -g POWERLEVEL9K_DIR_MIN_COMMAND_COLUMNS=40
  typeset -g POWERLEVEL9K_DIR_MIN_COMMAND_COLUMNS_PCT=50
  typeset -g POWERLEVEL9K_DIR_HYPERLINK=false
  typeset -g POWERLEVEL9K_DIR_SHOW_WRITABLE=v3

  local anchor_files=(
    .bzr .citc .git .hg .node-version .python-version .go-version .ruby-version
    .lua-version .java-version .perl-version .php-version .tool-version
    .shorten_folder_marker .svn .terraform CVS Cargo.toml composer.json go.mod
    package.json stack.yaml
  )
  typeset -g POWERLEVEL9K_SHORTEN_FOLDER_MARKER="(${(j:|:)anchor_files})"

  typeset -g POWERLEVEL9K_VCS_CLEAN_BACKGROUND=2
  typeset -g POWERLEVEL9K_VCS_MODIFIED_BACKGROUND=3
  typeset -g POWERLEVEL9K_VCS_UNTRACKED_BACKGROUND=2
  typeset -g POWERLEVEL9K_VCS_CONFLICTED_BACKGROUND=3
  typeset -g POWERLEVEL9K_VCS_LOADING_BACKGROUND=8
  typeset -g POWERLEVEL9K_VCS_BRANCH_ICON='\uF126 '
  typeset -g POWERLEVEL9K_VCS_UNTRACKED_ICON='?'
  typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=-1
  typeset -g POWERLEVEL9K_VCS_DISABLED_WORKDIR_PATTERN='~'
  typeset -g POWERLEVEL9K_VCS_DISABLE_GITSTATUS_FORMATTING=true
  typeset -g POWERLEVEL9K_VCS_CONTENT_EXPANSION='${$((anatase_p10k_git_formatter()))+${anatase_p10k_git_format}}'
  typeset -g POWERLEVEL9K_VCS_{STAGED,UNSTAGED,UNTRACKED,CONFLICTED,COMMITS_AHEAD,COMMITS_BEHIND}_MAX_NUM=-1
  typeset -g POWERLEVEL9K_VCS_BACKENDS=(git)

  typeset -g POWERLEVEL9K_STATUS_EXTENDED_STATES=true
  typeset -g POWERLEVEL9K_STATUS_OK=true
  typeset -g POWERLEVEL9K_STATUS_OK_VISUAL_IDENTIFIER_EXPANSION='✔'
  typeset -g POWERLEVEL9K_STATUS_OK_FOREGROUND=$foreground_color
  typeset -g POWERLEVEL9K_STATUS_OK_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_STATUS_OK_PIPE=true
  typeset -g POWERLEVEL9K_STATUS_OK_PIPE_VISUAL_IDENTIFIER_EXPANSION='✔'
  typeset -g POWERLEVEL9K_STATUS_OK_PIPE_FOREGROUND=$foreground_color
  typeset -g POWERLEVEL9K_STATUS_OK_PIPE_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_STATUS_ERROR=true
  typeset -g POWERLEVEL9K_STATUS_ERROR_VISUAL_IDENTIFIER_EXPANSION='✘'
  typeset -g POWERLEVEL9K_STATUS_ERROR_FOREGROUND=3
  typeset -g POWERLEVEL9K_STATUS_ERROR_BACKGROUND=1
  typeset -g POWERLEVEL9K_STATUS_ERROR_SIGNAL=true
  typeset -g POWERLEVEL9K_STATUS_VERBOSE_SIGNAME=false
  typeset -g POWERLEVEL9K_STATUS_ERROR_SIGNAL_VISUAL_IDENTIFIER_EXPANSION='✘'
  typeset -g POWERLEVEL9K_STATUS_ERROR_SIGNAL_FOREGROUND=3
  typeset -g POWERLEVEL9K_STATUS_ERROR_SIGNAL_BACKGROUND=1
  typeset -g POWERLEVEL9K_STATUS_ERROR_PIPE=true
  typeset -g POWERLEVEL9K_STATUS_ERROR_PIPE_VISUAL_IDENTIFIER_EXPANSION='✘'
  typeset -g POWERLEVEL9K_STATUS_ERROR_PIPE_FOREGROUND=3
  typeset -g POWERLEVEL9K_STATUS_ERROR_PIPE_BACKGROUND=1

  typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_FOREGROUND=0
  typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_BACKGROUND=3
  typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_THRESHOLD=3
  typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_PRECISION=0
  typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_FORMAT='d h m s'

  typeset -g POWERLEVEL9K_BACKGROUND_JOBS_FOREGROUND=6
  typeset -g POWERLEVEL9K_BACKGROUND_JOBS_BACKGROUND=0
  typeset -g POWERLEVEL9K_BACKGROUND_JOBS_VERBOSE=false

  typeset -g POWERLEVEL9K_DIRENV_FOREGROUND=3
  typeset -g POWERLEVEL9K_DIRENV_BACKGROUND=0
  typeset -g POWERLEVEL9K_ASDF_FOREGROUND=0
  typeset -g POWERLEVEL9K_ASDF_BACKGROUND=7
  typeset -g POWERLEVEL9K_ASDF_SOURCES=(shell local global)
  typeset -g POWERLEVEL9K_ASDF_PROMPT_ALWAYS_SHOW=false
  typeset -g POWERLEVEL9K_ASDF_SHOW_SYSTEM=true

  typeset -g POWERLEVEL9K_CONTEXT_ROOT_FOREGROUND=1
  typeset -g POWERLEVEL9K_CONTEXT_ROOT_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_CONTEXT_{REMOTE,REMOTE_SUDO}_FOREGROUND=$foreground_color_stronger
  typeset -g POWERLEVEL9K_CONTEXT_{REMOTE,REMOTE_SUDO}_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_CONTEXT_FOREGROUND=$foreground_color_stronger
  typeset -g POWERLEVEL9K_CONTEXT_BACKGROUND=$background_color
  typeset -g POWERLEVEL9K_CONTEXT_ROOT_TEMPLATE='%n@%m'
  typeset -g POWERLEVEL9K_CONTEXT_{REMOTE,REMOTE_SUDO}_TEMPLATE='%n@%m'
  typeset -g POWERLEVEL9K_CONTEXT_TEMPLATE='%n@%m'
  typeset -g POWERLEVEL9K_CONTEXT_{DEFAULT,SUDO}_{CONTENT,VISUAL_IDENTIFIER}_EXPANSION=

  typeset -g POWERLEVEL9K_VIRTUALENV_FOREGROUND=0
  typeset -g POWERLEVEL9K_VIRTUALENV_BACKGROUND=4
  typeset -g POWERLEVEL9K_VIRTUALENV_SHOW_PYTHON_VERSION=false
  typeset -g POWERLEVEL9K_VIRTUALENV_SHOW_WITH_PYENV=false
  typeset -g POWERLEVEL9K_VIRTUALENV_{LEFT,RIGHT}_DELIMITER=
  typeset -g POWERLEVEL9K_ANACONDA_FOREGROUND=0
  typeset -g POWERLEVEL9K_ANACONDA_BACKGROUND=4
  typeset -g POWERLEVEL9K_ANACONDA_CONTENT_EXPANSION='${${${${CONDA_PROMPT_MODIFIER#\(}% }%\)}:-${CONDA_PREFIX:t}}'

  typeset -g POWERLEVEL9K_KUBECONTEXT_SHOW_ON_COMMAND='kubectl|helm|kubens|kubectx|oc|istioctl|kogito|k9s|helmfile'
  typeset -g POWERLEVEL9K_KUBECONTEXT_DEFAULT_FOREGROUND=7
  typeset -g POWERLEVEL9K_KUBECONTEXT_DEFAULT_BACKGROUND=5
  typeset -g POWERLEVEL9K_KUBECONTEXT_DEFAULT_CONTENT_EXPANSION='${P9K_KUBECONTEXT_CLOUD_CLUSTER:-${P9K_KUBECONTEXT_NAME}}'
  POWERLEVEL9K_KUBECONTEXT_DEFAULT_CONTENT_EXPANSION+='${${:-/$P9K_KUBECONTEXT_NAMESPACE}:#/default}'
  typeset -g POWERLEVEL9K_AWS_SHOW_ON_COMMAND='aws|awless|terraform|pulumi|terragrunt'
  typeset -g POWERLEVEL9K_AWS_DEFAULT_FOREGROUND=7
  typeset -g POWERLEVEL9K_AWS_DEFAULT_BACKGROUND=1
  typeset -g POWERLEVEL9K_AZURE_SHOW_ON_COMMAND='az|terraform|pulumi|terragrunt'
  typeset -g POWERLEVEL9K_AZURE_FOREGROUND=7
  typeset -g POWERLEVEL9K_AZURE_BACKGROUND=4
  typeset -g POWERLEVEL9K_GCLOUD_SHOW_ON_COMMAND='gcloud|gcs'
  typeset -g POWERLEVEL9K_GCLOUD_FOREGROUND=7
  typeset -g POWERLEVEL9K_GCLOUD_BACKGROUND=4
  typeset -g POWERLEVEL9K_GCLOUD_PARTIAL_CONTENT_EXPANSION='${P9K_GCLOUD_PROJECT_ID//\%/%%}'
  typeset -g POWERLEVEL9K_GCLOUD_COMPLETE_CONTENT_EXPANSION='${P9K_GCLOUD_PROJECT_NAME//\%/%%}'
  typeset -g POWERLEVEL9K_GCLOUD_REFRESH_PROJECT_NAME_SECONDS=60

  typeset -g POWERLEVEL9K_VI_MODE_FOREGROUND=0
  typeset -g POWERLEVEL9K_VI_MODE_NORMAL_BACKGROUND=2
  typeset -g POWERLEVEL9K_VI_MODE_INSERT_BACKGROUND=4
  typeset -g POWERLEVEL9K_VI_MODE_VISUAL_BACKGROUND=3
  typeset -g POWERLEVEL9K_VI_MODE_OVERWRITE_BACKGROUND=1
  typeset -g POWERLEVEL9K_VI_COMMAND_MODE_STRING=NORMAL
  typeset -g POWERLEVEL9K_VI_INSERT_MODE_STRING=
  typeset -g POWERLEVEL9K_TODO_FOREGROUND=0
  typeset -g POWERLEVEL9K_TODO_BACKGROUND=8
  typeset -g POWERLEVEL9K_TIMEWARRIOR_FOREGROUND=255
  typeset -g POWERLEVEL9K_TIMEWARRIOR_BACKGROUND=8
  typeset -g POWERLEVEL9K_TIMEWARRIOR_CONTENT_EXPANSION='${P9K_CONTENT:0:24}${${P9K_CONTENT:24}:+…}'
  typeset -g POWERLEVEL9K_TASKWARRIOR_FOREGROUND=0
  typeset -g POWERLEVEL9K_TASKWARRIOR_BACKGROUND=6

  typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always
  typeset -g POWERLEVEL9K_INSTANT_PROMPT=verbose
  typeset -g POWERLEVEL9K_DISABLE_HOT_RELOAD=true
  typeset -g POWERLEVEL9K_CONFIG_FILE=${${(%):-%x}:a}
}

anatase_p10k_git_formatter() {
  emulate -L zsh

  if [[ -n $P9K_CONTENT ]]; then
    typeset -g anatase_p10k_git_format=$P9K_CONTENT
    return
  fi

  local meta='%7F'
  local clean='%0F'
  local modified='%0F'
  local untracked='%0F'
  local conflicted='%1F'
  local res

  if [[ -n $VCS_STATUS_LOCAL_BRANCH ]]; then
    local branch=${(V)VCS_STATUS_LOCAL_BRANCH}
    (( $#branch > 32 )) && branch[13,-13]="…"
    res+="${clean}${(g::)POWERLEVEL9K_VCS_BRANCH_ICON}${branch//\%/%%}"
  fi

  if [[ -n $VCS_STATUS_TAG && -z $VCS_STATUS_LOCAL_BRANCH ]]; then
    local tag=${(V)VCS_STATUS_TAG}
    (( $#tag > 32 )) && tag[13,-13]="…"
    res+="${meta}#${clean}${tag//\%/%%}"
  fi

  [[ -z $VCS_STATUS_LOCAL_BRANCH && -z $VCS_STATUS_TAG ]] &&
    res+="${meta}@${clean}${VCS_STATUS_COMMIT[1,8]}"

  if [[ -n ${VCS_STATUS_REMOTE_BRANCH:#$VCS_STATUS_LOCAL_BRANCH} ]]; then
    res+="${meta}:${clean}${(V)VCS_STATUS_REMOTE_BRANCH//\%/%%}"
  fi

  (( VCS_STATUS_COMMITS_BEHIND )) && res+=" ${clean}⇣${VCS_STATUS_COMMITS_BEHIND}"
  (( VCS_STATUS_COMMITS_AHEAD && !VCS_STATUS_COMMITS_BEHIND )) && res+=" "
  (( VCS_STATUS_COMMITS_AHEAD )) && res+="${clean}⇡${VCS_STATUS_COMMITS_AHEAD}"
  (( VCS_STATUS_PUSH_COMMITS_BEHIND )) && res+=" ${clean}⇠${VCS_STATUS_PUSH_COMMITS_BEHIND}"
  (( VCS_STATUS_PUSH_COMMITS_AHEAD && !VCS_STATUS_PUSH_COMMITS_BEHIND )) && res+=" "
  (( VCS_STATUS_PUSH_COMMITS_AHEAD )) && res+="${clean}⇢${VCS_STATUS_PUSH_COMMITS_AHEAD}"
  (( VCS_STATUS_STASHES )) && res+=" ${clean}*${VCS_STATUS_STASHES}"
  [[ -n $VCS_STATUS_ACTION ]] && res+=" ${conflicted}${VCS_STATUS_ACTION}"
  (( VCS_STATUS_NUM_CONFLICTED )) && res+=" ${conflicted}~${VCS_STATUS_NUM_CONFLICTED}"
  (( VCS_STATUS_NUM_STAGED )) && res+=" ${modified}+${VCS_STATUS_NUM_STAGED}"
  (( VCS_STATUS_NUM_UNSTAGED )) && res+=" ${modified}!${VCS_STATUS_NUM_UNSTAGED}"
  (( VCS_STATUS_NUM_UNTRACKED )) && res+=" ${untracked}${(g::)POWERLEVEL9K_VCS_UNTRACKED_ICON}${VCS_STATUS_NUM_UNTRACKED}"
  (( VCS_STATUS_HAS_UNSTAGED == -1 )) && res+=" ${modified}-"

  typeset -g anatase_p10k_git_format=$res
}
functions -M anatase_p10k_git_formatter 2>/dev/null

anatase_should_configure_prompt() {
  case "${ANATASE_ZSH_THEME:-auto}" in
    off)
      return 1
      ;;
    simple|p10k)
      return 0
      ;;
  esac

  [[ -z "${PROMPT:-}" ||
    "${PROMPT:-}" = "%m%# " ||
    "${PROMPT:-}" = "%# " ||
    "${PROMPT:-}" = "[%n@%m]%~%# " ]]
}

if anatase_should_configure_prompt; then
  anatase_zsh_theme=${ANATASE_ZSH_THEME:-auto}
  if [[ "$anatase_zsh_theme" = auto && -n "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ]]; then
    anatase_zsh_theme=simple
  fi

  case "$anatase_zsh_theme:$TERM" in
    simple:*|auto:linux|auto:screen.linux)
      anatase_use_powerlevel10k=false
      anatase_configure_afmagic
      ;;
    p10k:*|auto:*)
      anatase_use_powerlevel10k=true
      anatase_configure_powerlevel10k
      ;;
  esac
else
  anatase_use_powerlevel10k=false
fi

#
# Load plugins
#

zmodload zsh/terminfo 2>/dev/null || true

autoload -Uz \
  compinit \
  down-line-or-beginning-search \
  edit-command-line \
  up-line-or-beginning-search
compinit

zle -N down-line-or-beginning-search
zle -N edit-command-line
zle -N up-line-or-beginning-search

anatase_bindkey_all() {
  bindkey -M emacs "$1" "$2"
  bindkey -M viins "$1" "$2"
  bindkey -M vicmd "$1" "$2"
}

if (( ${+terminfo[smkx]} && ${+terminfo[rmkx]} )); then
  anatase_zle_line_init() {
    echoti smkx
  }
  anatase_zle_line_finish() {
    echoti rmkx
  }
  zle -N zle-line-init anatase_zle_line_init
  zle -N zle-line-finish anatase_zle_line_finish
fi

#
# Expand key bindings
#

bindkey -e

# Up/Down -> search command history by the current line prefix.
anatase_bindkey_all '^[[A' up-line-or-beginning-search
anatase_bindkey_all '^[[B' down-line-or-beginning-search
[[ -n "${terminfo[kcuu1]:-}" ]] && anatase_bindkey_all "${terminfo[kcuu1]}" up-line-or-beginning-search
[[ -n "${terminfo[kcud1]:-}" ]] && anatase_bindkey_all "${terminfo[kcud1]}" down-line-or-beginning-search

# PageUp/PageDown -> search command history by the current line prefix.
anatase_bindkey_all '^[[5~' history-beginning-search-backward
anatase_bindkey_all '^[[6~' history-beginning-search-forward
[[ -n "${terminfo[kpp]:-}" ]] && anatase_bindkey_all "${terminfo[kpp]}" history-beginning-search-backward
[[ -n "${terminfo[knp]:-}" ]] && anatase_bindkey_all "${terminfo[knp]}" history-beginning-search-forward

# Home/End -> move to the beginning/end of the line.
anatase_bindkey_all '^[[7~' beginning-of-line
anatase_bindkey_all '^[[H' beginning-of-line
anatase_bindkey_all '^[[8~' end-of-line
anatase_bindkey_all '^[[F' end-of-line
[[ -n "${terminfo[khome]:-}" ]] && anatase_bindkey_all "${terminfo[khome]}" beginning-of-line
[[ -n "${terminfo[kend]:-}" ]] && anatase_bindkey_all "${terminfo[kend]}" end-of-line

# Insert -> toggle overwrite mode.
anatase_bindkey_all '^[[2~' overwrite-mode
# Delete -> delete the character under the cursor.
anatase_bindkey_all '^[[3~' delete-char
# Left/Right -> move by one character.
anatase_bindkey_all '^[[C' forward-char
anatase_bindkey_all '^[[D' backward-char
# Ctrl-Left/Ctrl-Right -> move by one word.
anatase_bindkey_all '^[[1;5C' forward-word
anatase_bindkey_all '^[[1;5D' backward-word
anatase_bindkey_all '^[Oc' forward-word
anatase_bindkey_all '^[Od' backward-word
# Ctrl-Delete -> delete the next word.
anatase_bindkey_all '^[[3;5~' kill-word
# Backspace -> delete the previous character.
anatase_bindkey_all '^?' backward-delete-char

# Ctrl-Backspace -> delete the previous word.
bindkey '^H' backward-kill-word
# Shift-Tab -> undo the last line editor action.
bindkey '^[[Z' undo
# Alt-w -> kill from the cursor to the mark.
bindkey '^[w' kill-region
# Alt-l -> run ls.
bindkey -s '^[l' '^q ls^J'
# Ctrl-r -> search backward through command history incrementally.
bindkey '^r' history-incremental-search-backward
# Space -> expand history references before inserting a space.
bindkey ' ' magic-space
# Ctrl-x Ctrl-e -> edit the current command line in $VISUAL or $EDITOR.
bindkey '^X^E' edit-command-line
# Alt-m -> copy the previous shell word.
bindkey '^[m' copy-prev-shell-word

WORDCHARS=${WORDCHARS//\/[&.;]}

export POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true

if $anatase_use_powerlevel10k && [ -r "${anatase_zsh_dir}/powerlevel10k/powerlevel10k.zsh-theme" ]; then
  . "${anatase_zsh_dir}/powerlevel10k/powerlevel10k.zsh-theme"
fi

if [ -r "${anatase_zsh_dir}/zsh-autosuggestions/zsh-autosuggestions.zsh" ]; then
  . "${anatase_zsh_dir}/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi

if [ -r "${anatase_zsh_dir}/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]; then
  . "${anatase_zsh_dir}/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi

unfunction anatase_bindkey_all
unfunction anatase_configure_afmagic
unfunction anatase_configure_powerlevel10k
unfunction anatase_should_configure_prompt
unset anatase_zsh_dir anatase_use_powerlevel10k anatase_zsh_theme

#
# Encryption helper aliases
#

# TPM PCRS
# 0 UEFI 2 KERNEL 4 BOOTLOADER 5 PARTITION TABLE 7 SECURE BOOT (grub: 8 KERNEL CMD 9 KERNEL IMG)
# https://www.gnu.org/software/grub/manual/grub/grub.html#Measured-Boot
# https://threat.tevora.com/secure-boot-tpm-2/
: ${PCRS:="0+2+3+7+8"}

_anatase_enroll_with_key() {
  if ! sudo test -s /crypt/systemd.key; then
    print -r -- "No cached LUKS recovery key was found at /crypt/systemd.key."
    print -r -- "Anatase will generate and enroll a recovery key now, then store it"
    print -r -- "there so TPM/FIDO enrollment updates can happen without a password."
    print -r -- "You may be prompted for your current disk encryption passphrase."

    sudo bash -c '
      set -e

      key=/crypt/systemd.key
      device=$(blkid | awk -F: "/crypto_LUKS/ { print \$1; exit }")

      if [ -z "$device" ]; then
        echo "No crypto_LUKS device found." >&2
        exit 1
      fi

      install -d -m 0700 "$(dirname "$key")"
      systemd-cryptenroll --recovery-key "$device" > "$key"
      chmod 0600 "$key"
    ' || return
  fi

  sudo bash -c '
    set -e

    key=$1
    shift
    device=$(blkid | awk -F: "/crypto_LUKS/ { print \$1; exit }")

    if [ -z "$device" ]; then
      echo "No crypto_LUKS device found." >&2
      exit 1
    fi

    PASSWORD="$(cat "$key")" systemd-cryptenroll "$@" "$device"
  ' bash /crypt/systemd.key "$@"
}

# Asks you to enter your hardware encryption password
# Since TPM always unlocks, you might feel you're about to forget it...
alias remindme="sudo bash -c 'cryptsetup luksOpen --test-passphrase --disable-external-tokens --verbose \$(blkid | grep crypto_LUKS | grep -Eo \"^/dev/[a-zA-Z0-9]+\")'"

# TPM update and clear commands to setup autounlock
tpmu() {
  _anatase_enroll_with_key --tpm2-device=auto --wipe-slot=tpm2 --tpm2-pcrs="$PCRS" &&
    print -r -- "Updated TPM2 LUKS auto-unlock enrollment."
}
tpmc() {
  _anatase_enroll_with_key --wipe-slot=tpm2 &&
    print -r -- "Cleared TPM2 LUKS auto-unlock enrollment."
}

# Same as TPM but with a FIDO key
fidou() {
  _anatase_enroll_with_key \
    --fido2-device=auto \
    --wipe-slot=fido2 \
    --fido2-with-user-presence=false \
    --fido2-with-client-pin=false \
    --fido2-with-user-verification=true &&
    print -r -- "Updated FIDO2 LUKS auto-unlock enrollment."
}
fidoc() {
  _anatase_enroll_with_key --wipe-slot=fido2 &&
    print -r -- "Cleared FIDO2 LUKS auto-unlock enrollment."
}

#
# 
#

# Prints all terminal colors, with optional parameters for start and stop
# Useful for setting up your terminal colors
printc () {
  if [ -n "$2" ]; then
    start=$1
    end=$2
  else
    start=0
    end=${1:-255}
  fi
  for i in {$start..$end}; do 
    print -Pn "%K{$i}  %k%F{$i}${(l:3::0:)i}%f " ${${(M)$((i%6)):#3}:+$'\n'}; 
  done
}

# Screen helpers
# ss <name> launches a screen
# sr lists screens and sr <name> returns to a screen
# exit with Ctrl + C
alias ss='screen -S' 
alias sr='screen -r'

# Python venv helpers
# Essentially, on a new python project, type cv -> av to create and activate
# the virtual environment, and dv to deactivate
cv ()
{
  python${1:-3} -m venv venv
}
alias av='source venv/bin/activate'
alias dv='deactivate'

# ex - archive extractor, who remembers the commands anyway
# Yes, some of these are not available in anatase (for now)
# usage: ex <file>
ex ()
{
  if [ -f $1 ] ; then
    case $1 in
      *.tar.bz2)   tar xjf $1   ;;
      *.tar.gz)    tar xzf $1   ;;
      *.bz2)       bunzip2 $1   ;;
      *.rar)       unrar x $1     ;;
      *.gz)        gunzip $1    ;;
      *.tar)       tar xf $1    ;;
      *.tbz2)      tar xjf $1   ;;
      *.tgz)       tar xzf $1   ;;
      *.zip)       unzip $1     ;;
      *.Z)         uncompress $1;;
      *.7z)        7z x $1      ;;
      *)           echo "'$1' cannot be extracted via ex()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}
