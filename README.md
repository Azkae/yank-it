# Yank It

A small Chrome extension to copy the path to a DOM element.
For example:

`[Page] section.page > div.taskList > [Task] div.taskRow > p.taskSummary`

Useful for pasting to an LLM.

## How to use

1. Open `chrome://extensions`, enable Developer mode, click "Load unpacked", select the project directory
2. Click the extension icon → hover over elements → blue highlight overlay tracks elements
3. Click an element → path copied to clipboard

## Security

IMO, Chrome extensions are a security nightmare. This extension's code is very small, in pure JS and with no dependencies. You can easily verify the code.
