#!/bin/bash

# Preprocess the entries and save to a temporary file
python3 /root/.local/bin/tmlib.notes-citations-processor.py "$(pwd)" group-task-notelog $@ \
  | awk 'BEGIN{RS="/ENTRY"; ORS="\0"} {gsub(/\n/, "\\n"); print}' > /tmp/preprocessed_entries.txt

# Run fzf with the preprocessed entries
selected=$(cat /tmp/preprocessed_entries.txt \
  | fzf --preview="sh ~/.local/bin/tmlib.notes-task-notelog-grep-preview.sh {} {q}" \
        --read0 --multi --preview-window=up:60% \
)

# Check if selected is empty
if [ -z "$selected" ]; then
  echo "No entry selected"
  exit 1
fi

# Convert \\n to actual newlines for each selection
selected=$(echo "$selected" | sed 's/\\\\n/\n/g')

# Remove temporary quickfix file if existent
quick_fix_file=/tmp/quickfix.vim
if [ -e "$quick_fix_file" ]; then
  rm $quick_fix_file
fi

# Extract filename and line number for each selected entry
while IFS= read -r entry; do
  last_line=$(echo "$entry" | tail -n 1)
  filename=$(echo "$last_line" | cut -d':' -f1 | tr -d '\n')
  other_content=$(echo "$last_line" | cut -d':' -f2- | tr -d '\n')

  # Check if filename starts with \n and remove it if present
  if [[ "$filename" == \\n* ]]; then
    filename=$(echo "$filename" | sed 's/^\\n//')
  fi

  lineno=$(echo "$last_line" | cut -d':' -f2 | tr -d '\n')

  # Check if filename and lineno are extracted
  if [ -n "$filename" ] && [ -n "$lineno" ]; then
    echo $filename:$lineno:1:$other_content >> $quick_fix_file
  fi
done <<< "$selected"

# Check if entries are extracted
if [ ! -e "$quick_fix_file" ]; then
  echo "Failed to extract filename or line number."
  exit 1
fi

# Open Vim and load the quickfix list
#vim -q $quick_fix_file

# cleanup
#rm $quick_fix_file

# Get the parent process ID (PPID)
#ppid=$(ps -o ppid= -p $$)
