# The other side of the pull request

A blog post about building [Flipside](https://github.com/pratyakshrunsoncaffeine/flipside) on [Switch](https://github.com/sandbox-quantum/switch), for the Flip the Switch hackathon's Best Blog track.

Read it at https://kadoo69.github.io/flipside-blog/ (interactive) or as [Markdown](index.md).

## Files

- `template.html`: the page; `python3 build.py` writes `index.html`.
- `draft.md`: the text; `python3 build_md.py` writes `index.md`, the agent-readable copy.
- `code/flip_agent.py`: the 76-line Switch agent from the post, standard library only.
- `verify-core.js`: Flipside's in-browser verifier, copied verbatim from its `site/verify.html`.
- `data/`: Flipside's synthetic example disclosure, manifest and seal trailer.
- `llms.txt`, `robots.txt`, `sitemap.xml`: for search engines and AI agents.

## Run the agent

```
SWITCH_EMAIL=... SWITCH_PASSWORD=... python3 code/flip_agent.py
```

Tested on Switch Console 0.40.1 with switch-core 0.31.0, on 6 Nov 2026.
All people, code and sessions in the post are synthetic.
