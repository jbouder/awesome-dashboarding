# 02 · From artifact to a standalone page

**Supports:** Part 1, Demo 2. **Type:** generative. **Needs:** a browser.
`make example static` serves it at <http://localhost:3102/02-static-html/>.

The Demo 1 dashboard as one self-contained HTML file: styles, data, and
charts in a single file you own. Open it from disk, or put it on any static
host. This folder is published to GitHub Pages by
`.github/workflows/pages.yml`:
<https://jbouder.github.io/dashboarding-lab/02-static-html/>.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt and the full build prompt |
| `index.html` | The reference result. Under 300 lines, Apache ECharts from a CDN, data embedded |

The data is a snapshot in a `<script id="lumen-snapshot">` block. `make
extract` refreshes it.

## Run it

1. In the Demo 1 chat, paste the demo prompt from `prompts.md`.
2. Download the file Claude writes and open it in a browser. No server, no
   build step.
3. Commit it to a GitHub repository with Pages turned on, or drop it on any
   static host, and share the link.

## What to point out

- **You own it now.** Plain HTML, CSS, and JavaScript. No license, no
  platform.
- **Hosting is nearly free.** GitHub Pages, S3, Netlify, or a file share.
- **The data is a snapshot.** It is only as fresh as the last time someone
  regenerated the file. This one shows its snapshot time in the footer.
- **There is no login.** Anyone with the file or the link sees all the data
  in it. Keep sensitive data out, or host it behind authentication.
- **Updates mean regenerating the file,** by hand or with a script like
  `make extract`.

## Fallback

`index.html` in this folder, or its Pages copy.
