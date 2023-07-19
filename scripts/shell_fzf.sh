#!/bin/bash

# settings
# set this to 1 to also copy the command to tmux buffer (default=0)
FHP_COPY_TO_TMUX_BUFFER=0

# fd - cd to selected directory from specified directory
fd() {
  local dir
  local init_dir
  init_dir=$(pwd)
  [ ! -z "$1" ] && cd "$1"
  dir=$(find ${1:-.} -path '*/\.*' -prune \
                  -o -type d -print 2> /dev/null | fzf +m) && cd "$dir"
  [ $? != 0 ] && cd $init_dir
}

# fda - including hidden directories
fda() {
  local dir
  local init_dr
  init_dir="$(pwd)"
  [ ! -z "$1" ] && cd "$1"
  dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) && cd "$dir"
  [ $? != 0 ] && cd $init_dir
}


# fhp - print command from history
fhp() {
  comm="$( ([ -n "$ZSH_NAME" ] && fc -l 1 || history) | fzf +s --tac | sed -E 's/ *[0-9]*\*? *//' | sed -E 's/\\/\\\\/g')"
  echo $comm
  if [[ $FHP_COPY_TO_TMUX_BUFFER != 0 ]]; then
    echo $comm | tr --d '\n' | tmux loadb -
  fi
}


# fh - repeat history
fh() {
  comm="$(fhp)"
  echo "$" $comm
  eval "$comm"
}

# fkill - kill processes - list only the ones you can kill. Modified the earlier script.
fkill() {
    local pid 
    if [ "$UID" != "0" ]; then
        pid=$(ps -f -u $UID | sed 1d | fzf -m | awk '{print $2}')
    else
        pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
    fi  

    if [ "x$pid" != "x" ]
    then
        echo $pid | xargs kill -${1:-9}
    fi  
}
