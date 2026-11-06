"""Build index.html from template.html: the agent listing, the verifier and the example seal.

    python3 build.py

Inputs live in this repo: code/flip_agent.py, verify-core.js (copied verbatim from Flipside's
site/verify.html) and data/ (Flipside's examples/q2-ok.json, examples/manifest.json and the
seal trailer from examples/seal.bundle).
"""

import html
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://kadoo69.github.io/flipside-blog/"
KEYWORDS = r"\b(import|def|return|if|else|for|in|is|not|and|or|while|True|None|continue|with|as)\b"
TOKEN = re.compile(
    r"(?P<c>#.*$)|(?P<s>[fb]?\"(?:[^\"\\]|\\.)*\"|'[^']*')|(?P<k>" + KEYWORDS + r")|(?P<f>\b[a-z_]+(?=\())"
)


DIAGRAM = HERE / "diagram"
MMDC = HERE / "node_modules/.bin/mmdc"
# Messages drawn in a status colour, by (from, to) participant ids in diagram/sequence.mmd.
TONES = {("O", "SW"): "refused", ("SW", "O"): "refused", ("RA", "O"): "ok"}


def render_diagram() -> None:
    """Render diagram/sequence.mmd to light and dark SVG with Mermaid, when the CLI is installed.

    The SVGs are committed, so the page builds without Node; run `npm install` to re-render.
    """
    if not MMDC.exists():
        return
    for mode in ("light", "dark"):
        subprocess.run([str(MMDC), "-q", "-i", str(DIAGRAM / "sequence.mmd"),
                        "-o", str(DIAGRAM / f"seq-{mode}.svg"), "-c", str(DIAGRAM / f"{mode}.json"),
                        "-C", str(DIAGRAM / "fonts.css"), "-I", f"seq-{mode}", "-b", "transparent"],
                       check=True)


def tidy(svg: str) -> str:
    """Fit the viewBox to Mermaid's group boxes, drop their black outline, tag status messages."""
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    boxes = [(float(x), float(w)) for x, w in re.findall(
        r'<rect x="([-\d.]+)"[^>]*?width="([\d.]+)"[^>]*class="rect"', svg)]
    left = min([vb[0]] + [x - 2 for x, _ in boxes])
    right = max([vb[0] + vb[2]] + [x + w + 2 for x, w in boxes])
    vb[0], vb[2] = left, right - left
    svg = re.sub(r'viewBox="[^"]+"', 'viewBox="%g %g %g %g"' % tuple(vb), svg, count=1)
    svg = re.sub(r'style="max-width: [\d.]+px;', f'style="max-width: {vb[2]:g}px;', svg, count=1)
    svg = svg.replace('stroke="rgb(0,0,0, 0.5)"', 'stroke="none"')

    def tone(m: re.Match) -> str:
        kind = TONES.get((m.group(3), m.group(4)))
        return (m.group(1) + (f" {kind}" if kind else "") + m.group(2)) if kind else m.group(0)

    svg = re.sub(r'(<text[^>]*class="messageText)("(?:(?!<text).)*?<line[^>]*data-from="(\w+)" '
                 r'data-to="(\w+)")', tone, svg, flags=re.S)
    svg = re.sub(r'(<line[^>]*class="messageLine\d)("[^>]*data-from="(\w+)" data-to="(\w+)")',
                 tone, svg)
    assert svg.count(" refused") == 4 and svg.count(" ok") >= 2, "status messages not tagged"
    return svg


def sequence() -> str:
    render_diagram()
    return "".join(f'<div class="mm mm-{m}">' + tidy((DIAGRAM / f"seq-{m}.svg").read_text())
                   + "</div>" for m in ("light", "dark"))


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
