"-------------fish------------------
" fix fish PluginInstall error
if $SHELL =~ 'bin/fish' || $SHELL =~ '/usr/local/bin/fish'
    set shell=/bin/bash
endif

"-------------plugin----------------
filetype off
set nocompatible
call plug#begin('~/.vim/plugged')
Plug 'asins/vim-dict'
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'scrooloose/nerdtree', { 'on':  'NERDTreeToggle' }
Plug 'majutsushi/tagbar'
Plug 'SirVer/ultisnips'
Plug 'honza/vim-snippets'
Plug 'fatih/vim-go'
Plug 'jiangmiao/auto-pairs'
Plug 'Chiel92/vim-autoformat'
Plug 'scrooloose/nerdcommenter'
Plug 'octol/vim-cpp-enhanced-highlight'
Plug 'vim-scripts/DrawIt'
Plug 'artur-shaik/vim-javacomplete2'
Plug 'xolox/vim-misc'
Plug 'xolox/vim-lua-ftplugin'
" Plug 'pangloss/vim-javascript'
Plug 'sentientmachine/erics_vim_syntax_and_color_highlighting'
" Plug 'Yggdroot/indentLine'
Plug 'tbastos/vim-lua'
Plug 'adwpc/cscopex'
Plug 'vim-scripts/a.vim'
Plug 'vim-scripts/nginx.vim'
Plug 'skywind3000/asyncrun.vim'
Plug 'Yggdroot/LeaderF', { 'do': './install.sh' }
Plug 'Shougo/echodoc.vim'
Plug 'rdnetto/YCM-Generator', { 'branch': 'stable'}
Plug 'neomake/neomake' 
Plug 'othree/yajs.vim'
Plug 'othree/javascript-libraries-syntax.vim'
Plug 'hail2u/vim-css3-syntax'
Plug 'maksimr/vim-jsbeautify', {'do': 'sudo npm install -g typescript js-beautify'}
Plug 'plasticboy/vim-markdown'
Plug 'Valloric/YouCompleteMe', { 'do': './install.sh --all' }
Plug 'w0rp/ale'
" Plug 'dense-analysis/ale'
Plug 'buoto/gotests-vim'
Plug 'junegunn/fzf.vim'
Plug 'junegunn/fzf'
Plug 'plytophogy/vim-virtualenv'
Plug 'mileszs/ack.vim'
Plug 'mcchrish/nnn.vim'
"Plug 'moorereason/vim-markdownfmt'
Plug 'airblade/vim-gitgutter'
Plug 'editorconfig/editorconfig-vim'
Plug 'itchyny/lightline.vim'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'scrooloose/syntastic'
Plug 'altercation/vim-colors-solarized'
Plug 'prabirshrestha/async.vim'
Plug 'prabirshrestha/vim-lsp'
Plug 'google/vim-maktaba'
Plug 'google/vim-codefmt'
Plug 'google/vim-glaive'
call plug#end()
filetype plugin indent on
"----------------------------------

" vim base config"
so ~/.vim/base.vim

" vim plugin config"
so ~/.vim/plugin.vim

" vim useful function config"
so ~/.vim/func.vim

" vim key mapping config"
so ~/.vim/key.vim

set nu
set mouse=a
set tabstop=4
set shiftwidth=4
set go=
set rtp+=~/.fzf
let g:ackprg = 'ag --nogroup --nocolor --column'
set encoding=utf-8

set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936
set termencoding=utf-8
set encoding=utf-8

call glaive#Install()
augroup autoformat_settings
  autocmd FileType bzl AutoFormatBuffer buildifier
  autocmd FileType c,cpp,proto,javascript AutoFormatBuffer clang-format
  autocmd FileType dart AutoFormatBuffer dartfmt
  autocmd FileType go AutoFormatBuffer gofmt
  autocmd FileType gn AutoFormatBuffer gn
  autocmd FileType html,css,sass,scss,less,json AutoFormatBuffer js-beautify
  autocmd FileType java AutoFormatBuffer google-java-format
  autocmd FileType python AutoFormatBuffer yapf
  " Alternative: autocmd FileType python AutoFormatBuffer autopep8
  autocmd FileType rust AutoFormatBuffer rustfmt
  autocmd FileType vue AutoFormatBuffer prettier
augroup END

hi comment ctermfg=6
