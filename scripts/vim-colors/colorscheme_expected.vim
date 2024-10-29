" calcure_colors.vim

if exists("syntax_on")
  syntax reset
endif

let g:colors_name = "calcure_colors"
let pat_today = strftime('%Y,%-m,%-d')
let pat_today = '2024,08,10'

execute 'syntax match pat_not_today /^\(.*' . pat_today . '\)\@!.*$/ containedin=ALL'

" Handle directly the status x additive group cross product
execute 'syntax match pat_pend_add_grp0 /PEND,' . pat_today . ',.*CL0,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp0 /DONE,' . pat_today . ',.*CL0,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp0 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL0,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp1 /PEND,' . pat_today . ',.*CL1,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp1 /DONE,' . pat_today . ',.*CL1,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp1 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL1,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp2 /PEND,' . pat_today . ',.*CL2,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp2 /DONE,' . pat_today . ',.*CL2,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp2 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL2,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp3 /PEND,' . pat_today . ',.*CL3,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp3 /DONE,' . pat_today . ',.*CL3,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp3 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL3,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp4 /PEND,' . pat_today . ',.*CL4,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp4 /DONE,' . pat_today . ',.*CL4,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp4 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL4,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp5 /PEND,' . pat_today . ',.*CL5,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp5 /DONE,' . pat_today . ',.*CL5,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp5 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL5,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp6 /PEND,' . pat_today . ',.*CL6,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp6 /DONE,' . pat_today . ',.*CL6,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp6 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL6,.*/ containedin=ALL'

execute 'syntax match pat_pend_add_grp7 /PEND,' . pat_today . ',.*CL7,.*/ containedin=ALL'
execute 'syntax match pat_done_add_grp7 /DONE,' . pat_today . ',.*CL7,.*/ containedin=ALL'
execute 'syntax match pat_today_add_grp7 /\(INIT\|MISS\|MOVE\|SKIP\),' . pat_today . ',.*CL7,.*/ containedin=ALL'

highlight pat_pend_add_grp0 guifg=White ctermfg=LightYellow ctermbg=Black
highlight pat_done_add_grp0 guifg=White ctermfg=Cyan ctermbg=Black
highlight pat_today_add_grp0 guifg=White ctermfg=LightGray ctermbg=Black

highlight pat_pend_add_grp1 guifg=White ctermfg=LightYellow ctermbg=17
highlight pat_done_add_grp1 guifg=White ctermfg=Cyan ctermbg=17
highlight pat_today_add_grp1 guifg=White ctermfg=LightGray ctermbg=17

highlight pat_pend_add_grp2 guifg=White ctermfg=LightYellow ctermbg=52
highlight pat_done_add_grp2 guifg=White ctermfg=Cyan ctermbg=52
highlight pat_today_add_grp2 guifg=White ctermfg=LightGray ctermbg=52

highlight pat_pend_add_grp3 guifg=White ctermfg=LightYellow ctermbg=1
highlight pat_done_add_grp3 guifg=White ctermfg=Cyan ctermbg=1
highlight pat_today_add_grp3 guifg=White ctermfg=LightGray ctermbg=1

highlight pat_pend_add_grp4 guifg=White ctermfg=LightYellow ctermbg=2
highlight pat_done_add_grp4 guifg=White ctermfg=Cyan ctermbg=2
highlight pat_today_add_grp4 guifg=White ctermfg=LightGray ctermbg=2

highlight pat_pend_add_grp5 guifg=White ctermfg=LightYellow ctermbg=6
highlight pat_done_add_grp5 guifg=White ctermfg=Cyan ctermbg=6
highlight pat_today_add_grp5 guifg=White ctermfg=LightGray ctermbg=6

highlight pat_pend_add_grp6 guifg=White ctermfg=LightYellow ctermbg=4
highlight pat_done_add_grp6 guifg=White ctermfg=Cyan ctermbg=4
highlight pat_today_add_grp6 guifg=White ctermfg=LightGray ctermbg=4

highlight pat_pend_add_grp7 guifg=White ctermfg=LightYellow ctermbg=5
highlight pat_done_add_grp7 guifg=White ctermfg=Cyan ctermbg=5
highlight pat_today_add_grp7 guifg=White ctermfg=LightGray ctermbg=5

execute 'syntax match pat_comment /^ *#.*$/ containedin=ALL'

highlight pat_comment guifg=Gray ctermfg=Gray

" Set default colors
hi Normal ctermfg=NONE ctermbg=NONE cterm=NONE gui=NONE guifg=NONE guibg=NONE
