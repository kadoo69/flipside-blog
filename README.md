# The other side of the pull request

A blog post about building [Flipside](https://github.com/pratyakshrunsoncaffeine/flipside) on [Switch](https://github.com/sandbox-quantum/switch), for the Flip the Switch hackathon's Best Blog track.

Read it at https://kadoo69.github.io/flipside-blog/ (interactive) or as [Markdown](index.md).

## Files

- `template.html`: the page; `python3 build.py` writes `index.html`.
- `draft.md`: the text; `python3 build_md.py` writes `index.md`, the agent-readable copy.
- `diagram/sequence.mmd`: the review as a Mermaid sequence diagram, the one source for the page and `index.md`.
  `npm install` adds the pinned Mermaid CLI, and `build.py` then re-renders `diagram/seq-light.svg` and `seq-dark.svg`.
  The SVGs are committed, so the page builds without Node and loads no JavaScript library.
- `code/flip_agent.py`: the 82-line Switch agent from the post, standard library only.
- `code/say.py`: talks to that agent from a second terminal, as you, and prints its reply.
- `verify-core.js`: Flipside's in-browser verifier, copied verbatim from its `site/verify.html`.
- `data/`: Flipside's synthetic example disclosure, manifest and seal trailer.
- `llms.txt`, `robots.txt`, `sitemap.xml`: for search engines and AI agents.

## Run the agent

```
SWITCH_EMAIL=... SWITCH_PASSWORD=... python3 code/flip_agent.py
```

It prints `room ready: flip-demo` and waits.
Switch Console 0.40.1 does not list that room, so talk to the agent from a second terminal:

```
SWITCH_EMAIL=... SWITCH_PASSWORD=... python3 code/say.py hello, Switch
```

Tested on Switch Console 0.40.1 with switch-core 0.31.0, on 7 Nov 2026.
Priya, Omar and PR #142 in the post are synthetic; the two-machine run it describes is real.
