;; _____________________________________________________________________
;; = Licence =

;; This file is part of Rose, a framework for scientific suites.

;; Rose is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; Rose is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with Rose. If not, see <http://www.gnu.org/licenses/>.
;; _____________________________________________________________________
;;
;; = rose-conf-mode.el =
;;    An emacs syntax highlighting mode for the various rose .conf files
;;
;; = Instructions =
;;    Place this file in a directory on your emacs load path. e.g:
;;
;;         ~/.emacs.d/lisp
;;
;;    and in your .emacs file:
;;
;;         (add-to-list 'load-path "~/.emacs.d/lisp/")
;;         (require 'rose-conf-mode)
;;
;;    This mode introduces one non-standard face, for the ignored
;;    settings: font-lock-rose-ignored-face (defaults to gray) which
;;    you may customise as desired
;; _____________________________________________________________________

(defvar rose-conf-mode-hook nil)

;; Face for de-activated/ignored rose regions
(defface font-lock-rose-ignored-face
  '((t (:foreground "#888888")))
  "Ignored Rose settings")

;; Extend region hook - to ensure re-fontifying the multi-line region is
;;                      done properly
(defun rose-font-lock-extend-region ()
  "Extend the search region to include an entire block of text."
  ;; Avoid compiler warnings about these global variables from font-lock.el.
  ;; See the documentation for variable `font-lock-extend-region-functions'.
  (eval-when-compile (defvar font-lock-beg) (defvar font-lock-end))
  (save-excursion
    (goto-char font-lock-beg)
    (let ((found (or (re-search-backward "\n\n" nil t) (point-min))))
      (goto-char font-lock-end)
      (when (re-search-forward "\n\n" nil t)
        (beginning-of-line)
        (setq font-lock-end (point)))
      (setq font-lock-beg found))))

;; Define the mode and the syntax highlighting for it
(define-derived-mode rose-conf-mode fundamental-mode
  "rose-conf" "Major mode for editing Rose files"
  ;; Variable names at start of line up to first = sign
  (font-lock-add-keywords nil '(("\\(^.*?\\)=" 1 'font-lock-variable-name-face)))
  ;; Section headers within square brackets
  (font-lock-add-keywords nil '(("\\[\\(.*\\)\\]" 1 'font-lock-keyword-face)))  
  ;; If a : separated section header re-highlight each half separately
  (font-lock-add-keywords nil '(("\\[\\(.*:\\)" 1 'font-lock-function-name-face)))
  (font-lock-add-keywords nil '(("\\[.*:\\(.*\\)\\]" 1 'font-lock-keyword-face)))
  ;; If as above but with an = re-hightlight the part between : and =
  (font-lock-add-keywords nil '(("\\[.*:\\(.*\\)=.*\\]" 1 'font-lock-keyword-face)))
  ;; Strings are as always between quotes
  (font-lock-add-keywords nil '(("'.*'" . 'font-lock-string-face)))
  (font-lock-add-keywords nil '(("\".*\"" . 'font-lock-string-face)))
  ;; Comments are following # but only if at the start of the line
  (font-lock-add-keywords nil '(("^#.*" . 'font-lock-comment-face)))
  ;; A ! at the start of the line de-activates that line
  (font-lock-add-keywords nil '(("^!.*" . 'font-lock-rose-ignored-face)))
  ;; A ! at the start of a section header de-activates that line
  (font-lock-add-keywords nil '(("\\[!.*\\]" . 'font-lock-rose-ignored-face)))
  ;; Any ! at the start of a section header de-activates the whole section
  (font-lock-add-keywords nil 
    '(("^\\[!.*\\]\\(\\(.*\n\\)*?\\)\\(?:^\\[[^!]\\|\\(?:\n\\|\t\\)*\\'\\)" 
        1 'font-lock-rose-ignored-face)))

  ;; Add the extend region hook to deal with the multiline matching above
  (add-hook 'font-lock-extend-region-functions
            'rose-font-lock-extend-region)

  ;; Make sure jit-lock scans larger multiline regions correctly
  (set (make-local-variable 'jit-lock-contextually) t)

  ;; Force any other fundamental mode inherit font-locking to be ignored, this
  ;; previously caused double-quotes to break the multiline highlighting
  (set (make-local-variable 'font-lock-keywords-only) t)

  ;; And of course we need multiline mode
  (set (make-local-variable 'font-lock-multiline) t)

  ;; Run the mode hooks to allow a user to execute mode-specific stuff
  (run-hooks 'rose-conf-mode-hook))

;;;###autoload
(add-to-list 'auto-mode-alist '("rose-.*.conf" . rose-conf-mode))
(add-to-list 'auto-mode-alist '("rose-suite\\.info\\'" . rose-conf-mode))

(provide 'rose-conf-mode)

