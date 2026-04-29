# Yank It

A small chrome extension to copy a path to a dom element.
For example:

`section.page > div.taskList > div.taskRow > p.taskSummary`

Useful for pasting to a llm.

## How to use

1. Open `chrome://extensions`, enable Developer mode, click "Load unpacked", select the project directory
2. Click the extension icon → hover over elements → blue highlight overlay tracks elements
3. Click an element → path copied to clipboard

## Security

IMO, chrome extension are a security nightmare, this extension code is very small, in pure js and with no dependencies. You can easily verify the code.
