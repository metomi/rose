" Syntax highlighter for Rose configuration files.
"_____________________________________________________________________
" = Licence =
"
" This file is part of Rose, a framework for scientific suites.
"
" Rose is free software: you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation, either version 3 of the License, or
" (at your option) any later version.
"
" Rose is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with Rose. If not, see <http://www.gnu.org/licenses/>.
"_____________________________________________________________________
" = Instructions =
"
" Make a $HOME/.vim/syntax/ directory.
" Put this file in there.
" Alternatively, put a symlink there, pointing to this file in your
" local Rose installation.

" Put the following in $HOME/.vimrc for file type recognition:

"augroup filetype
"  au! BufRead,BufnewFile rose-*.conf,rose-*.info set filetype=rose-conf
"augroup END
"_____________________________________________________________________

if exists("b:current_syntax")
  finish
endif

syn sync fromstart

syn match roselinecomment '^#.*$'
syn region roseignoredsection start='^\[!!\?[^!].*\]' end='^\ze\[' contains=roselinecomment
syn match rosesection '^\[[^!].*\]$'
syn region roseignoredoption start='^!!\?\(\w\|-\).*$' end='^\ze\S'
syn match roserhsvaluecont '^\s\s*\w.*$'
syn match roserhsvalue '^[^=]*=\zs.*$'

hi def link roselinecomment Comment
hi def link roseignoredsection PreProc
hi def link rosesection Function
hi def link roseignoredoption PreProc
hi def link roserhsvaluecont String
hi def link roserhsvalue String
hi def link roseequals Special
