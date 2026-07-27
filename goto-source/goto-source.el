;;; goto-source.el --- Jump to JSX source from chrome-copy-dom selectors  -*- lexical-binding: t -*-

(defcustom goto-source-executable "goto-source"
  "Path to the goto-source executable."
  :type 'string)

(defcustom goto-source-project-directory nil
  "Path default project directory, using the current project if nil"
  :type 'string)

(defun goto-source--run (selector)
  (let* ((root (or goto-source-project-directory
                   (if (and (fboundp 'project-current) (project-current))
                       (project-root (project-current))
                     default-directory)))
         (output (shell-command-to-string
                  (format "%s --all %s %s"
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

(use-package simple-httpd)
(require 'simple-httpd)
(setq httpd-serve-files nil)
(setq httpd-port 30142)

(httpd-servlet* open-ref text/plain (ref)
  (message "Finding source..")
  (select-frame-set-input-focus (selected-frame))
  (condition-case err
      (goto-source--visit ref)
    (error (message "goto-source: %s" (error-message-string err)))))

(httpd-start)

(setq goto-source-project-directory "~/work/candid-website/")

(provide 'goto-source)
;;; goto-source.el ends here
