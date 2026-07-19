;;; goto-source.el --- Jump to JSX source from chrome-copy-dom selectors  -*- lexical-binding: t -*-

(defcustom goto-source-executable "goto-source"
  "Path to the goto-source executable."
  :type 'string)

(defun goto-source--run (selector)
  (let* ((root (if (and (fboundp 'project-current) (project-current))
                   (project-root (project-current))
                 default-directory))
         (output (shell-command-to-string
                  (format "%s %s %s"
                          goto-source-executable
                          (shell-quote-argument selector)
                          (shell-quote-argument (expand-file-name root)))))
         (lines (split-string (string-trim output) "\n" t)))
    (delq nil
          (mapcar (lambda (line)
                    (when (string-match "\\(.*\\):\\([0-9]+\\)$" line)
                      (cons (match-string 1 line)
                            (string-to-number (match-string 2 line)))))
                  lines))))

(defun goto-source--visit (selector)
  (let* ((results (goto-source--run selector))
         (result (pcase (length results)
                   (0 (user-error "goto-source: no matches"))
                   (1 (car results))
                   (_ (let* ((labeled (mapcar (lambda (r)
                                                (cons (format "%s:%d" (car r) (cdr r)) r))
                                              results))
                             (key (completing-read "goto-source: " (mapcar #'car labeled) nil t)))
                        (cdr (assoc key labeled)))))))
    (find-file (car result))
    (goto-char (point-min))
    (forward-line (1- (cdr result)))))

;;;###autoload
(defun goto-source-from-minibuffer ()
  (interactive)
  (goto-source--visit (read-string "Selector: ")))

;;;###autoload
(defun goto-source-from-clipboard ()
  (interactive)
  (goto-source--visit
   (string-trim (or (and (display-graphic-p) (gui-get-selection 'CLIPBOARD))
                    (current-kill 0 t)
                    (user-error "Clipboard is empty")))))

(provide 'goto-source)
;;; goto-source.el ends here
