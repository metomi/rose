" Syntax highlighter for Rose configuration files.
"_____________________________________________________________________
" = Instructions =
"
" Make a $HOME/.vim/syntax/ directory and bung this file in there.

" Put the following in $HOME/.vimrc for file type recognition:

"augroup filetype
"  au! BufRead,BufnewFile rose-*.conf,rose-*.info set filetype=rose-conf
"augroup END
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

if exists("b:current_syntax")
  finish
endif

syn sync fromstart

syn match roselinecomment '^#.*$'
syn region roseignoredsection start='^\[!!\?[^!].*\]' end='^\ze\[' contains=roselinecomment
syn match rosesection '^\[[^!].*\]$'
syn region roseignoredoption start='^!!\?[^!].*$' end='^\ze\S'
syn match roserhsvaluecont '^\s\s*\w.*$'
syn match roserhsvalue '^[^=]*=\zs.*$'

hi def link roselinecomment Comment
hi def link roseignoredsection PreProc
hi def link rosesection Function
hi def link roseignoredoption PreProc
hi def link roserhsvaluecont String
hi def link roserhsvalue String
hi def link roseequals Special
