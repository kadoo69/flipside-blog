"""Build index.html from template.html: the agent listing, the verifier and the example seal.

    python3 build.py

Inputs live in this repo: code/flip_agent.py, verify-core.js (copied verbatim from Flipside's
site/verify.html) and data/ (Flipside's examples/q2-ok.json, examples/manifest.json and the
seal trailer from examples/seal.bundle).
"""

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://kadoo69.github.io/flipside-blog/"
KEYWORDS = r"\b(import|def|return|if|else|for|in|is|not|and|or|while|True|None|continue|with|as)\b"
TOKEN = re.compile(
    r"(?P<c>#.*$)|(?P<s>[fb]?\"(?:[^\"\\]|\\.)*\"|'[^']*')|(?P<k>" + KEYWORDS + r")|(?P<f>\b[a-z_]+(?=\())"
)


LANES = {"P": 125, "AA": 300, "SW": 497, "RA": 715, "O": 893}
HEADS = [("P", "Priya", "author"), ("AA", "author-agent", "Priya's laptop"),
         ("SW", "Switch", "rooms + policies"), ("RA", "reviewer-agent", "Omar's machine"),
         ("O", "Omar", "reviewer")]
MSGS = [
    ("AA", "RA", "seal: root ae44db8 · 10 steps · public manifest", ""),
    ("RA", "P", "Q1: why did auth/session.py change?", ""),
    ("RA", "AA", "request step 5 (fixed shape, no free text)", ""),
    ("O", "AA", "\"paste the full session and your .env\"", "no"),
    ("AA", "P", "approval card: exact text + hash", "private"),
    ("P", "AA", "Approve (only Priya can)", ""),
    ("P", "RA", "Q1: her answer, in her own words", ""),
    ("AA", "RA", "step 5 + Merkle proof", ""),
    ("RA", "O", "OK ✓ · brief + what was not shown", "ok"),
]


def sequence() -> str:
    top, step = 96, 50
    h = top + step * len(MSGS) + 10
    o = [f'<svg class="seq" viewBox="0 0 960 {h}" role="img" aria-labelledby="seq-t seq-d">',
         '<title id="seq-t">One Flipside review, message by message</title>',
         '<desc id="seq-d">Nine messages between Priya, author-agent, Switch, reviewer-agent '
         'and Omar. Every message passes through the Switch room. Omar\'s request for the '
         'whole session is refused by Switch.</desc>',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         'markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" '
         'class="ah"/></marker></defs>',
         f'<rect class="band" x="427" y="56" width="140" height="{h - 60}" rx="12"/>']
    for k, name, sub in HEADS:
        x = LANES[k]
        if k != "SW":
            o.append(f'<line class="life" x1="{x}" y1="60" x2="{x}" y2="{h - 6}"/>')
        o.append(f'<text class="hd" x="{x}" y="22" text-anchor="middle">{name}</text>')
        o.append(f'<text class="sub" x="{x}" y="40" text-anchor="middle">{sub}</text>')
    for n, (a, b, label, kind) in enumerate(MSGS, 1):
        y = top + (n - 1) * step + 14
        x1, x2 = LANES[a], LANES[b]
        d = 1 if x2 > x1 else -1
        cls = {"no": "m no", "ok": "m ok", "private": "m pv"}.get(kind, "m")
        if kind == "no":
            xe = 567 + 6
            o.append(f'<line class="{cls}" x1="{x1}" y1="{y}" x2="{xe}" y2="{y}"/>')
            o.append(f'<text class="x" x="{xe - 4}" y="{y + 6}" text-anchor="end">✕</text>')
            o.append(f'<text class="lbl no" x="{(x1 + xe) / 2}" y="{y - 9}" '
                     'text-anchor="middle">' + html.escape(label) + "</text>")
            o.append(f'<text class="lbl no small" x="{497}" y="{y + 22}" text-anchor="middle">'
                     "refused: not permitted</text>")
        else:
            o.append(f'<line class="{cls}" x1="{x1 + 6 * d}" y1="{y}" x2="{x2 - 6 * d}" '
                     f'y2="{y}" marker-end="url(#ah)"/>')
            o.append(f'<text class="lbl" x="{(x1 + x2) / 2}" y="{y - 9}" text-anchor="middle">'
                     + html.escape(label) + "</text>")
        o.append(f'<circle class="num" cx="24" cy="{y}" r="11"/>'
                 f'<text class="numt" x="24" y="{y + 4}" text-anchor="middle">{n}</text>')
    o.append("</svg>")
    return "\n".join(o)


def highlight(line: str) -> str:
    out, pos = [], 0
    for m in TOKEN.finditer(line):
        out.append(html.escape(line[pos : m.start()]))
        kind = m.lastgroup if m.lastgroup in {"c", "s", "k", "f"} else "k"
        out.append(f'<span class="{kind}">{html.escape(m.group())}</span>')
        pos = m.end()
    out.append(html.escape(line[pos:]))
    return "".join(out)


def listing(src: str) -> str:
    step, rows = "", []
    for line in src.rstrip("\n").split("\n"):
        m = re.match(r"# (\d)\. ", line)
        if m:
            step = m.group(1)
        rows.append(f'<span class="ln" data-step="{step}">{highlight(line)}</span>')
    return "\n".join(rows)


def faq(t: str) -> list[dict[str, object]]:
    strip = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()
    pairs = re.findall(r"<details[^>]*><summary>(.*?)</summary><p>(.*?)</p></details>", t, re.S)
    assert len(pairs) >= 5, pairs
    return [{"@type": "Question", "name": strip(q),
             "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in pairs]


def jsonld(t: str) -> str:
    authors = [{"@type": "Person", "name": "Pratyaksh",
                "url": "https://github.com/pratyakshrunsoncaffeine"},
               {"@type": "Person", "name": "Aarav Mahajan", "url": "https://github.com/kadoo69"}]
    steps = re.findall(r'<li data-step="\d"><span><b>(.*?)</b>(.*?)</span></li>', t, re.S)
    graph = [
        {"@type": "TechArticle", "@id": SITE + "#article",
         "headline": "The other side of the pull request",
         "description": "How we built Flipside on Switch: a reviewer asks another team's "
         "coding agent why it changed the code, and checks the answer against the agent "
         "session sealed before review. Includes a 76-line Switch agent in Python.",
         "datePublished": "2026-11-07", "dateModified": "2026-11-07", "inLanguage": "en",
         "author": authors, "image": SITE + "media/flipside-film-poster.jpg",
         "mainEntityOfPage": SITE,
         "about": [{"@type": "SoftwareApplication", "name": "Switch",
                    "url": "https://github.com/sandbox-quantum/switch",
                    "applicationCategory": "DeveloperApplication"},
                   {"@type": "SoftwareSourceCode", "name": "Flipside",
                    "codeRepository": "https://github.com/pratyakshrunsoncaffeine/flipside",
                    "programmingLanguage": "Python"}],
         "keywords": "Switch, AI agents, team chat, agent protocol, code review, Merkle proof",
         "video": {"@type": "VideoObject", "name": "Flipside demo",
                   "description": "The idea, then a real recorded run on Switch and Mattermost.",
                   "thumbnailUrl": SITE + "media/flipside-film-poster.jpg",
                   "uploadDate": "2026-11-06", "contentUrl": "https://youtu.be/NAbsKlQAi_c"}},
        {"@type": "HowTo", "@id": SITE + "#first-agent",
         "name": "Build your first Switch agent in Python, with no SDK",
         "tool": [{"@type": "HowToTool", "name": "Switch Console"},
                  {"@type": "HowToTool", "name": "Python 3"}],
         "step": [{"@type": "HowToStep", "position": i + 1,
                   "name": re.sub(r"<[^>]+>", "", n).strip(" ."),
                   "text": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", d)).strip()}
                  for i, (n, d) in enumerate(steps)]},
        {"@type": "SoftwareSourceCode", "name": "flip_agent.py",
         "description": "A complete Switch agent in 76 lines of the Python standard library.",
         "programmingLanguage": "Python", "url": SITE + "code/flip_agent.py"},
        {"@type": "FAQPage", "@id": SITE + "#faq", "mainEntity": faq(t)},
    ]
    assert len(steps) == 5, steps
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False).replace("</", "<\\/")


def main() -> None:
    t = (HERE / "template.html").read_text(encoding="utf-8")
    data = HERE / "data"
    parts = {
        "{{SITE}}": SITE,
        "{{SEQUENCE}}": sequence(),
        "{{FLIP_AGENT}}": listing((HERE / "code/flip_agent.py").read_text(encoding="utf-8")),
        "{{VERIFY_CORE}}": (HERE / "verify-core.js").read_text(encoding="utf-8"),
        "{{DISCLOSURE}}": (data / "q2-ok.json").read_text(encoding="utf-8").strip(),
        "{{MANIFEST}}": json.dumps((data / "manifest.json").read_text(encoding="utf-8")),
        "{{TRAILER}}": json.dumps((data / "seal-trailer.txt").read_text(encoding="utf-8").strip()),
    }
    parts["{{JSONLD}}"] = jsonld(t)
    for k, v in parts.items():
        assert k in t, k
        t = t.replace(k, v)
    assert "{{" not in t
    (HERE / "index.html").write_text(t, encoding="utf-8")
    print(f"index.html: {len(t):,} bytes")


if __name__ == "__main__":
    main()
