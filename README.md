# Yank It

A small Chrome & Firefox extension to copy the path to a DOM element.
For example:

`[Page] section.page > div.taskList > [Task] div.taskRow > p.taskSummary`

Useful for pasting to an LLM.

## Install
### Chrome

1. Open `chrome://extensions`
2. Enable Developer mode
3. Click **Load unpacked**
4. Select the project directory

### Firefox

1. Open `about:debugging`
2. Click **This Firefox**
3. Click **Load Temporary Add-on...**
4. Select `manifest.json`

## How to use

1. Click the extension icon → hover over elements
2. Click an element → path copied to clipboard

## Security

IMO, Chrome extensions are a security nightmare. This extension's code is very small, in pure JS and with no dependencies. You can easily verify the code.
