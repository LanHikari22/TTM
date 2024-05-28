" Check for the existence of the syntax being loaded
if exists("b:current_syntax")
    finish
endif

" Define the syntax match for the date and time format
" This pattern matches:
" - A dash followed by a space
" - Six digits (representing the date)
" - '-W' followed by two digits (representing the week number)
" - A single character from the set [MTWRFSU] (representing the day of the week)
" - A space, followed by five characters representing the time (HH:MM)
" - Another space and dash
syntax match CustomDate "- \d\{6}-W\d\{2}[MTWRFSU] \d\{2}:\d\{2}"
syntax match ObjectiveToken "- \d\{6}-W\d\{2}[MTWRFSU] \d\{2}:\d\{2} - (.*) .*"
syntax match Header "^ *#.*$"
syntax match Header "^ *_.*$"
syntax match NoteToken "..\d\{6}-W\d\{2}[MTWRFSU]-\d\{4}."
syntax match LOG_START "LOG_START"
syntax match LOG_END "LOG_END"

" Link the CustomDate syntax to the Comment highlight group to make it gray
highlight link CustomDate Comment
highlight Header guifg=White ctermfg=White
highlight NoteToken guifg=Blue ctermfg=Blue
highlight ObjectiveToken guifg=Yellow ctermfg=Yellow
highlight LOG_START guifg=Red ctermfg=Red
highlight LOG_END guifg=Red ctermfg=Red

" Set the current syntax to custom_log
let b:current_syntax = "custom_log"
