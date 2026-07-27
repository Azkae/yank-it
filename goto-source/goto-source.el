;;; goto-source.el --- Jump to JSX source from chrome-copy-dom selectors  -*- lexical-binding: t -*-

(require 'consult)

(defcustom goto-source-executable "goto-source"
  "Path to the goto-source executable."
  :type 'string)

(defcustom goto-source-project-directory nil
  "Path default project directory, using the current project if nil"
  :type 'string)

(defun goto-source--root ()
  (expand-file-name
   (or goto-source-project-directory
       (if (and (fboundp 'project-current) (project-current))
           (project-root (project-current))
         default-directory))))

(defun goto-source--run (selector root)
  "Return a list of (ELEMENT FILE LINE) matches for SELECTOR under ROOT."
  (let* ((output (shell-command-to-string
                  (format "%s --all %s %s"
                          goto-source-executable
                          (shell-quote-argument selector)
                          (shell-quote-argument root))))
         (lines (split-string (string-trim output) "\n" t)))
    (delq nil
          (mapcar (lambda (line)
                    (when (string-match "\\`\\(?:\\([^\t]+\\)\t\\)?\\(.+\\):\\([0-9]+\\)\\'" line)
                      (list (match-string 1 line)
                            (match-string 2 line)
                            (string-to-number (match-string 3 line)))))
                  lines))))

(defun goto-source--state ()
  "Preview state function for (ELEMENT FILE LINE) candidates."
  (let ((open (consult--temporary-files))
        (jump (consult--jump-state)))
    (lambda (action cand)
      (unless cand
        (funcall open))
      (funcall jump action
               (when cand
                 (consult--marker-from-line-column
                  (funcall (if (eq action 'return) #'find-file-noselect open)
                           (nth 1 cand))
                  (nth 2 cand) 0))))))

(defun goto-source--select (results root)
  "Pick one of RESULTS with consult, grouped by selector element."
  (let ((candidates
         (mapcar (pcase-lambda ((and result `(,element ,file ,line)))
                   (cons (propertize (format "%s:%d" (file-relative-name file root) line)
                                     'goto-source-element element)
                         result))
                 results)))
    (consult--read candidates
                   :prompt "goto-source: "
                   :require-match t
                   :sort nil
                   :lookup #'consult--lookup-cdr
                   :state (goto-source--state)
                   :preview-key '(:debounce 0.1 any)
                   :group (lambda (cand transform)
                            (if transform cand
                              (get-text-property 0 'goto-source-element cand))))))

(defun goto-source--visit (selector)
  (let* ((root (goto-source--root))
         (results (goto-source--run selector root))
         (result (pcase (length results)
                   (0 (user-error "goto-source: no matches"))
                   (1 (car results))
                   (_ (goto-source--select results root)))))
    (find-file (nth 1 result))
    (goto-char (point-min))
    (forward-line (1- (nth 2 result)))))

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
