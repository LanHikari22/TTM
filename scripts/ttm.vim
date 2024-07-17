"" -- Functions for creating notes --

function! GetWeekRelativeCustomDateString()
    " Get date of monday of this week and shorten 20XX to XX.
    let date_string = system("if [ $(date +%a) = 'Mon' ]; then date +%Y%m%d | awk '{print substr($0,3)}'; else date -d'monday last week' +%Y%m%d | awk '{print substr($0,3)}'; fi")
    let date_string = substitute(date_string, '\n', '', 'g')

    " Get week number and shorten day code
    let week_string = system("date +W%V%a | sed 's/Mon/M/; s/Tue/T/; s/Wed/W/; s/Thu/R/; s/Fri/F/; s/Sat/S/; s/Sun/U/'")

    let result = date_string . "-" . week_string

    return result
endfunction

function! GetLeadingSpaces()
    " Get the current line number
    let l:current_line = line('.')

    " Loop backward from the current line
    while l:current_line > 0
        " Get the content of the current line
        let l:line_content = getline(l:current_line)

        " Check if the line starts with the date pattern
        if l:line_content =~ '^\s*- \d\{6\}-W\d\{2\}[MTWRFSU]'
            " Match the leading spaces of the line and return
            return matchstr(l:line_content, '^\s\+')
        endif

        " if the line starts with a non-space character, there won't be any spaces
        if l:line_content =~ '^\S'
            return ''
        endif

        " Decrement the line number to check the previous line
        let l:current_line -= 1
    endwhile

    " If no matching line is found, return empty string
    return ''
endfunction

function! CreateNoteTemplate()
    " Get current date in specified format
    let date_string = GetWeekRelativeCustomDateString()

    " Get current time
    let time_string = system("date +%H:%M")

    " Generate a random number and pad it to four digits
    let random_num = printf("%04d", system("echo $(( RANDOM % 10000 ))"))

    " Concatenate to create the unique identifier
    let identifier = "P[" . trim(date_string) . "-" . trim(random_num) . "]"

    let spaces= GetLeadingSpaces()

    let divider="------------------------------------------------------------------------"

    " Create the todo log
    let todo_log = spaces . identifier . "- TODO (tags: #)\n" . spaces . "\tLOG_START\n" . spaces . "\t- " . trim(date_string) . " " . trim(time_string) . " - Created Note Entry\n" . spaces . "\tLOG_END\n" . spaces . divider

    " Add the todo log to the current buffer
    call append(line('.'), split(todo_log, '\n'))
endfunction

function! CreateNoteLog()
    " Get current date in specified format
    let date_string = GetWeekRelativeCustomDateString()

    " Get current time
    let time_string = system("date +%H:%M")

    let leading_spaces = GetLeadingSpaces()

    " Create the todo log
    let todo_log = leading_spaces . "- " . trim(date_string) . " " . trim(time_string) . " - \n"

    " Add the todo log to the current buffer
    call append(line('.'), split(todo_log, '\n'))
endfunction

autocmd BufRead,BufNewFile ~/.task/schedule/events.csv colorscheme calcure_colors
autocmd BufRead,BufNewFile ~/.task/schedule/events_ann colorscheme calcure_colors

" Function to set the filetype if LOG_START token is present
function! SetCustomLogFileType()
    if expand('%:t') == '.vimrc'
        return
    endif

    if expand('%:e') == 'vim'
        return
    endif

    if search('LOG_START', 'nw') > 0
      set filetype=custom_log
    endif
endfunction

autocmd FileType custom_log colorscheme custom_log
autocmd BufRead,BufNewFile * call SetCustomLogFileType()


"" -- Registering objectives from notes --

function! RegisterTask()
  let l:current_line = line('.')
  let l:current_file = expand('%:p')
  echo "Current File: " . l:current_file . " | Line Number: " . l:current_line
  execute '!python3 ~/.local/bin/tmlib.notes-register-task.py' shellescape(l:current_file) l:current_line
endfunction

function! RegisterObjective()
  let l:current_line = line('.')
  let l:current_file = expand('%:p')
  echo "Current File: " . l:current_file . " | Line Number: " . l:current_line
  execute '!python3 ~/.local/bin/tmlib.notes-register-objective.py' shellescape(l:current_file) l:current_line
endfunction

function! LinkObjective()
  " Get the current line number and file path
  let l:current_line = line('.')
  let l:current_file = expand('%:p')

  " Get current date in specified format
  let l:date_string = GetWeekRelativeCustomDateString()

  " Get current time
  let l:time_string = system("date +%H:%M")

  " Concatenate ttm_timedate
  let l:ttm_timedate = trim(l:date_string) . " " . trim(l:time_string)
  
  " Read the /tmp/target_task file
  let l:target_task = readfile('/tmp/target_task')

  " Extract the source filename and line content from the file
  let l:source_filename = l:target_task[0]
  let l:source_line_content = l:target_task[1]

  " Search for the line content in the source file to find the line number
  execute 'silent! e ' . l:source_filename
  let l:source_lineno = search(l:source_line_content, 'nw')

  " Format the source and sink params
  let l:source_filename_lineno = l:source_filename . ":" . l:source_lineno
  let l:sink_filename_lineno = l:current_file . ":" . l:current_line

  echo "Source File: " . l:source_filename . " | Line Number: " . l:source_lineno
  echo "Sink File: " . l:current_file . " | Line Number: " . l:current_line
  
  " Execute the external Python script with the necessary arguments
  execute '!python3 ~/.local/bin/tmlib.notes-link-objective.py' . ' ' . shellescape(l:ttm_timedate) . ' ' . shellescape(l:source_filename_lineno) . ' ' . shellescape(l:sink_filename_lineno) . ' link-task'
endfunction

function! LinkMilestone()
  " Get the current line number and file path
  let l:current_line = line('.')
  let l:current_file = expand('%:p')

  " Get current date in specified format
  let l:date_string = GetWeekRelativeCustomDateString()

  " Get current time
  let l:time_string = system("date +%H:%M")

  " Concatenate ttm_timedate
  let l:ttm_timedate = trim(l:date_string) . " " . trim(l:time_string)
  
  " Read the /tmp/target_task file
  let l:target_task = readfile('/tmp/target_task')

  " Extract the source filename and line content from the file
  let l:source_filename = l:target_task[0]
  let l:source_line_content = l:target_task[1]

  " Search for the line content in the source file to find the line number
  execute 'silent! e ' . l:source_filename
  let l:source_lineno = search(l:source_line_content, 'nw')

  " Format the source and sink params
  let l:source_filename_lineno = l:source_filename . ":" . l:source_lineno
  let l:sink_filename_lineno = l:current_file . ":" . l:current_line

  echo "Source File: " . l:source_filename . " | Line Number: " . l:source_lineno
  echo "Sink File: " . l:current_file . " | Line Number: " . l:current_line
  
  " Link the sink first (has-milestone), since it can cause a search change for source.
  execute '!python3 ~/.local/bin/tmlib.notes-link-objective.py' . ' ' . shellescape(l:ttm_timedate) . ' ' . shellescape(l:source_filename_lineno) . ' ' . shellescape(l:sink_filename_lineno) . ' link-has-milestone'

  " Now the file content could have changed, so search again.

  " Search for the line content in the source file to find the line number
  execute 'silent! e ' . l:source_filename
  let l:source_lineno = search(l:source_line_content, 'nw')

  " Format the source and sink params
  let l:source_filename_lineno = l:source_filename . ":" . l:source_lineno
  let l:sink_filename_lineno = l:current_file . ":" . l:current_line

  echo "Source File: " . l:source_filename . " | Line Number: " . l:source_lineno
  echo "Sink File: " . l:current_file . " | Line Number: " . l:current_line

  " Link milestone-of
  execute '!python3 ~/.local/bin/tmlib.notes-link-objective.py' . ' ' . shellescape(l:ttm_timedate) . ' ' . shellescape(l:source_filename_lineno) . ' ' . shellescape(l:sink_filename_lineno) . ' link-milestone-of'
endfunction

function! TargetObjective()
  " Get the current line content and file path
  let l:current_line_content = getline('.')
  let l:current_file = expand('%:p')

  " Use system command to truncate the line content up to the second '('
  let l:truncated_line_content = system("echo " . shellescape(l:current_line_content) . " | cut -d'(' -f1-2")
  let l:truncated_line_content = trim(l:truncated_line_content)

  " Create a list with the current file and truncated line content
  let l:target_task = [l:current_file, l:truncated_line_content]

  " Write the list to /tmp/target_task, overwriting the file
  call writefile(l:target_task, '/tmp/target_task')

  echo "Target task saved: " . l:current_file . " | Line Content: " . l:truncated_line_content
endfunction

function! SyncTask()
  let l:current_line = line('.')
  let l:current_file = expand('%:p')
  echo "Current File: " . l:current_file . " | Line Number: " . l:current_line
  execute '!python3 ~/.local/bin/tmlib.notes-sync-task.py' shellescape(l:current_file) l:current_line
endfunction

function! CheckTask()
  let l:current_line = line('.')
  let l:current_file = expand('%:p')
  echo "Current File: " . l:current_file . " | Line Number: " . l:current_line
  execute '!python3 ~/.local/bin/tmlib.notes-check-task.py' shellescape(l:current_file) l:current_line
endfunction

function! CalcureAddEvent()
  let l:current_line = line('.')
  let l:current_file = expand('%:p')
  echo "Current File: " . l:current_file . " | Line Number: " . l:current_line
  execute '!python3 ~/.local/bin/tmlib.notes-add-event.py' shellescape(l:current_file) l:current_line
endfunction

