" calcure_colors.vim

if exists("syntax_on")
  syntax reset
endif

let g:colors_name = "calcure_colors"
let pat_today = strftime('%Y,%-m,%-d')
let pat_today = '2023,7,13'

execute 'syntax match pat_important /.*' . pat_today . '.*,important.*/ containedin=ALL'
execute 'syntax match pat_unimportant /.*' . pat_today . '.*,unimportant.*/ containedin=ALL'
execute 'syntax match pat_not_today /^\(.*' . pat_today . '\)\@!.*$/ containedin=ALL'

highlight pat_important guifg=Yellow ctermfg=Yellow
highlight pat_unimportant guifg=Cyan ctermfg=Cyan
highlight pat_not_today guifg=Gray ctermfg=Gray

" Set default colors
hi Normal ctermfg=NONE ctermbg=NONE cterm=NONE gui=NONE guifg=NONE guibg=NONE
