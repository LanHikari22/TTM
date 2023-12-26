#!/bin/sh

# Make sure all these directories exist.
mkdir -p /root/notes
mkdir -p /root/.task/schedule

tmux new-session -d -s main

tmux new-session -d -s notes
tmux send-keys -t notes 'cd /root/notes' C-m

tmux new-session -d -s tasks
tmux send-keys -t tasks 'cd /root/.task' C-m

tmux new-session -d -s schedule
tmux send-keys -t schedule 'cd /root/.task/schedule' C-m

tmux new-session -d -s react_calendar_app
tmux send-keys -t react_calendar_app 'cd /root/src/react-calendar && npm start' C-m
tmux new-window -t react_calendar_app:2 
tmux send-keys -t react_calendar_app:2 'cd /root/src/react-calendar && python3 scripts/calcure_events.py populate && python3 scripts/calcure_events.py watch' C-m

tmux bind-key 'C-m' command-prompt -p "tm.fzf-cmd notes:6.1" "ru -b 'tm.fzf-cmd notes:5.1'"
tmux bind-key 'C-l' run-shell 'tmux split-window; tmux kill-pane -t 1'
tmux bind-key 'C-v' run-shell 'tmux select-layout even-vertical'

#tmux attach -t main
