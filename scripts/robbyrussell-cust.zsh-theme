#PROMPT='%n@%m $(hg_prompt_info)$(git_prompt_info)%{$fg[cyan]%}%c%{$reset_color%} '
PROMPT='$(hg_prompt_info)$(git_prompt_info)%{$fg[cyan]%}%c%{$reset_color%} '
PROMPT+="%(?:%{$fg_bold[green]%}➜ :%{$fg_bold[red]%}➜ )"

ZSH_THEME_GIT_PROMPT_PREFIX="%{$fg_bold[green]%}±(%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%} "
ZSH_THEME_GIT_PROMPT_DIRTY=" %{$fg[yellow]%}✗%{$fg[green]%})"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[green]%})"

ZSH_THEME_HG_PROMPT_PREFIX="%{$fg_bold[red]%}☿(%{$fg[red]%}"
ZSH_THEME_HG_PROMPT_SUFFIX="%{$reset_color%} "
ZSH_THEME_HG_PROMPT_DIRTY=" %{$fg[yellow]%}✗%{$fg[red]%})"
ZSH_THEME_HG_PROMPT_CLEAN="%{$fg[red]%})"
