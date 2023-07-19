# Task Warrior Hooks

This repository contains various hooks for task warrior

## Tasks
- tasks in this repository use TaskWarrior for task keeping. 
    - use `TASKRC=.taskrc taskwarrior` or `TASKRC=.taskrc vit`
    - to avoid coupling code, notes and documentation in the same place, 
      the notes are in the `docs` branch. 
        - Consider running `git worktree add .docs docs` to copy it to a hidden
      worktree for ease of use.

## Vit
- You need the following command for custom vit menu. You may need to specify different session names.
  - tmux bind-key 'C-m' command-prompt -p "tm.fzf-cmd notes:6.1" "ru -b 'tm.fzf-cmd notes:5.1'"
