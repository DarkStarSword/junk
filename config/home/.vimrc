set nocompatible              " be iMproved, required
if !empty(glob("~/.vim/bundle/Vundle.vim"))
	filetype off                  " vundle needs this, will be turned on later

	" set the runtime path to include Vundle and initialize
	set rtp+=~/.vim/bundle/Vundle.vim
	call vundle#begin()
	" alternatively, pass a path where Vundle should install plugins
	"call vundle#begin('~/some/path/here')

	" let Vundle manage Vundle, required
	Plugin 'VundleVim/Vundle.vim'

	Bundle 'nfvs/vim-perforce'
	"let g:perforce_use_relative_paths = 1
	let g:perforce_open_on_change = 1
	"let g:perforce_prompt_on_open = 0
	if has("win32unix")
		let g:perforce_use_cygpath = 1
	endif
	"let g:perforce_debug = 1
	let g:perforce_auto_source_dirs = ['Z:\\']

	" Plugin to quickly switch between source and header files:
	Plugin 'ericcurtin/CurtineIncSw.vim'
	map <F5> :call CurtineIncSw()<CR>

	" Show number under cursor in various bases \= \b= \h=
	Plugin 'ShowMultiBase'
	" Note: A couple of these config options are copy+paste bugged in this plugin
	" setting the binary variant instead of hex. Trivial to fix editing the script.
	let g:ShowMultiBase_Display_Binary_Show = 0
	let g:ShowMultiBase_Display_Octal_Show = 0
	let g:ShowMultiBase_Display_Hexadecimal_SegmentSize = 8
	let g:ShowMultiBase_Register_Hexadecimal_SegmentSize = 0

	" Classic test alignment plugin providing \tsp, :Align, etc
	Plugin 'Align'

	" Alternate text alignment plugin:
	Plugin 'junegunn/vim-easy-align'
	" Start interactive EasyAlign in visual mode (e.g. vipga)
	xmap ga <Plug>(EasyAlign)
	" Start interactive EasyAlign for a motion/text object (e.g. gaip)
	nmap ga <Plug>(EasyAlign)

	Plugin 'DrawIt'

	" All of your Plugins must be added before the following line
	call vundle#end()            " required
else
	echo "Vundle plugin manager is not installed, install it with:"
	echo "    git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim"
	echo "Then do :PluginInstall from vim"
endif
filetype plugin indent on    " must be after vundle

set hls
set ts=4
set sw=4
set noexpandtab
set ignorecase
set smartcase
set autoindent
set wildmode=longest,list,full
au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
set showmatch
set showcmd
set incsearch
set autowrite
setlocal spell spelllang=en_au
set spell
set modeline
set nowrap
set linebreak
set wildmode=longest,list
set tags=./tags,tags;
"set formatprg=par
if has("unix")
	set shell=/bin/sh " fish doesn't work since vim encloses the command in brackets
endif

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

syntax on
if has('gui_running')
	colorscheme torte
	set background=dark
else
	" For use with MidnightBlue background & Gold foreground
	colorscheme desert
	"colorscheme torte
	"colorscheme slate
	set background=dark
endif
set guifont=Lucida_Console:h9:cANSI

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

"highlight columns beyond the 80 char mark with F9
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

" Automatically detect external changes on various events and reload if
" unchanged or prompt if also locally modified
set autoread
au CursorHold,CursorHoldI,CursorMoved,CursorMovedI,InsertEnter,InsertChange,FocusGained * checktime

" Sync default cut buffer with clipboard. Make sure vim-gtk3 is installed for
" this to work, even if not using GUI. Also works on WSL2 (unnamedplus) if
" WSL2 graphics drivers are installed.
if !has('nvim')
	set clipboard=unnamed,unnamedplus,autoselect,exclude:cons\|linux
else
	if has('wsl')
		" This is supposed to be unecessary now WSL2 has proper clipboard
		" integration, but recently on a new install only yank has been
		" working for me and not put, so switching to neovim that can be
		" configured to call an external process to work around the issue.
		" win32yank.exe also comes highly recommended for use with neovim to
		" work around clipboard issues, but it's an extra dependency I'd
		" rather not have to remember to install.
		" https://github.com/neovim/neovim/wiki/FAQ#how-to-use-the-windows-clipboard-from-wsl
		let g:clipboard = {
		  \   'name': 'WslClipboard',
		  \   'copy': {
		  \      '+': 'clip.exe',
		  \      '*': 'clip.exe',
		  \    },
		  \   'paste': {
		  \      '+': 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
		  \      '*': 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
		  \   },
		  \   'cache_enabled': 0,
		  \ }
	end
	set clipboard=unnamed,unnamedplus
end

" Start gvim maximised
" https://vi.stackexchange.com/questions/1937/how-do-i-get-gvim-to-start-maximised-in-windows
autocmd GUIEnter * simalt ~x
