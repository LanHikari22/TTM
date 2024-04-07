#!/bin/sh

# TODO Update: This is the location on mounted for storing notes
export TTM_NOTES_MOUNT=~/data/ttm/notes

# TODO Update: This is the location on mounted for storing task database and schedule information
export TTM_TASK_MOUNT=~/data/ttm/task

# The port for a React calendar app representation of the schedule
export TTM_CALENDAR_PORT=3000

# The port to expose SSH
export TTM_SSH_PORT=2222


docker run -it -d -p $TTM_CALENDAR_PORT:3000 -p $TTM_SSH_PORT:22 \
    -v $TTM_TASK_MOUNT:/root/.task \
    -v $TTM_NOTES_MOUNT:/root/notes \
  ttm
