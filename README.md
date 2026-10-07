# lqh2011.com

![Static Badge](https://img.shields.io/badge/Author-@LQH--2011-blue)
![Static Badge](https://img.shields.io/badge/github-repo-purple?logo=github)  

Personal site of **Jesús Luo** (**LQH-2011**). Plain static HTML on GitHub Pages, served at
[lqh2011.com](https://lqh2011.com/) (see `CNAME`).

## Structure

| Path | What it is |
| --- | --- |
| `/` (`index.html`) | Redirects to the blog, [blog.lqh2011.com](https://blog.lqh2011.com) |
| `/tools/` | Hub listing all the small tools (each in its own folder) |
| `/tools/primecalc/` | Prime checker &amp; factorisation |
| `/tools/mdtopdf/` | Markdown → PDF converter |
| `/tools/gameoflife/` | Conway's Game of Life |
| `/tools/pong/` | Configurable Pong |
| `/tools/compressly/` | Photo compressor |
| `/pages/` | Odd one-off pages — Lishu, Bears (has its own index) |
| `/jacky/` | Jacky-forum related pages (has its own index) |
| `/history/` | Every past version of the homepage, rebuilt from git history |
| `/forum/` | Redirect to [zhujingqi.com/forum](https://zhujingqi.com/forum) |
| `404.html` | Custom 404, also redirects old (pre-reorg) paths to their new homes |

Every directory has its own `index.html` describing what lives in it. Folders that hold a
single tool (`/tools/pong/`, etc.) use that tool's own page as the index.

There is no build step — edit the files and push.

Contact me at jesus@lqh2011.com :D
