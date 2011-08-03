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
set autowrite
setlocal spell spelllang=en_au
set spell
set modeline
set nowrap
set tags=./tags,tags;
"set formatprg=par

map <F5> :set mouse=a<CR>
map <F6> :set mouse=<CR>
map <F7> :set invspell<CR>
nnoremap <silent> <f8> :TlistToggle<CR>

let Tlist_Use_Right_Window=1

" Attempts to fix vimdiff colours:
"set t_Co=256
"highlight DiffAdd term=reverse cterm=bold ctermbg=green ctermfg=white
"highlight DiffChange term=reverse cterm=bold ctermbg=cyan ctermfg=black
"highlight DiffText term=reverse cterm=bold ctermbg=gray ctermfg=black
"highlight DiffDelete term=reverse cterm=bold ctermbg=red ctermfg=black 

:highlight ExtraWhitespace ctermbg=red guibg=red
:match ExtraWhitespace /\s\+$\| \+\ze\t/

" For use with MidnightBlue background & Gold foreground
colorscheme desert
:highlight SpellLocal term=underline ctermbg=6 gui=undercurl guisp=Cyan ctermfg=1

source /home/dss/.vim/macros/table.vim
