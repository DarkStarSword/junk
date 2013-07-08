set hls
set ts=8
set sw=8
set noexpandtab
syntax on
set background=dark
set ignorecase
set smartcase
set autoindent
filetype plugin indent on
au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
set showmatch
set showcmd
set incsearch
set autowrite
setlocal spell spelllang=en_au
set spell
set modeline
set nowrap
set tags=./tags,tags;
"set formatprg=par
set shell=/bin/sh " fish doesn't work since vim encloses the command in brackets

" Disable the unnecessary and annoying bells (esp. with urgent on bell)
set noerrorbells visualbell t_vb=

"map <F5> :set mouse=a<CR>
"map <F6> :set mouse=<CR>
map <F6> :set filetype=diff<CR>
map <F7> :set invspell<CR>
" F8 set below
" F9 set below
nnoremap <silent> <f4> :TlistToggle<CR>
nnoremap <F11> :set number!<CR>

let Tlist_Use_Right_Window=1

" For use with MidnightBlue background & Gold foreground
colorscheme desert
:highlight SpellLocal term=underline ctermbg=6 gui=undercurl guisp=Cyan ctermfg=1

" Attempts to fix vimdiff colours:
"set t_Co=256
"highlight DiffAdd term=reverse cterm=bold ctermbg=green ctermfg=white
"highlight DiffChange term=reverse cterm=bold ctermbg=cyan ctermfg=black
"highlight DiffText term=reverse cterm=bold ctermbg=gray ctermfg=black
"highlight DiffDelete term=reverse cterm=bold ctermbg=red ctermfg=black 

" Highlight whitespace at EOL, and space before tabs:
" Make sure this is after the colorscheme or it won't work!
":highlight ExtraWhitespace ctermbg=red guibg=red
":match ExtraWhitespace /\s\+$\| \+\ze\t/
" Attempt to toggle, based on 80 char highlight method:
:highlight ExtraWhitespace ctermbg=red guibg=red
let g:extraWhitespaceHighlight = 1
fun! ToggleExtraWhitespaceHighlight()
     if g:extraWhitespaceHighlight
         let g:extraWhitespaceHighlight = 0
         echo "Extra whitespace highlight off"
         return matchdelete(w:extraWhitespaceHighlight)
     endif
     let w:extraWhitespaceHighlight=matchadd('ExtraWhitespace', '\s\+$\| \+\ze\t', -1)
     let g:extraWhitespaceHighlight = 1
     echo "Extra whitespace highlight on"
endfun
let w:extraWhitespaceHighlight=matchadd('ExtraWhitespace', '\s\+$\| \+\ze\t', -1)
nmap <F8> :call ToggleExtraWhitespaceHighlight()<CR>
" BUG: DOESN'T WORK PROPERLY WITH MULTIPLE WINDOWS (e.g. vimdiff). Kind of
" works, but throws an error if disabling already disabled window.  I believe
" it is related to using global variables rather than per window (buffer?
" window I think) variables - need to figure out how to run an initialisation
" when creating windows rather than using globals.

"highlight columns beyond the 80 char mark with ^m (I might change that shortcut)
let g:marginHighlight = 0
fun! ToggleMarginHighlight()
     if g:marginHighlight
         let g:marginHighlight = 0
         echo "margin highlight off"
         return matchdelete(w:marginHighlight)
     endif
     let w:marginHighlight=matchadd('StatusLine', '\%>80v.\+', -1)
     let g:marginHighlight = 1
     echo "margin highlight on"
endfun

nmap <F9> :call ToggleMarginHighlight()<CR>

if filereadable('~/.vim/macros/table.vim')
	source ~/.vim/macros/table.vim
endif
