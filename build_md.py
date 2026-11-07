"""Build index.md (the agent-readable copy) from draft.md, the agent code and the page's FAQ."""
import html as H
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
d = (root / "draft.md").read_text()
code = (root / "code/flip_agent.py").read_text()

d = d.replace("""```python
# flip_agent.py: the full file is 82 lines, linked below
```

[Full listing of `code/flip_agent.py`, with the five numbered comments as margin notes.]""",
              "```python\n" + code + "```")
d = d.replace("# The other side of the pull request\n",
              "# The other side of the pull request\n\n"
              "*Canonical, interactive version: https://kadoo69.github.io/flipside-blog/*\n", 1)

seq = ("```mermaid\n" + (root / "diagram/sequence.mmd").read_text().strip() + "\n```\n\n"
       "Every message passes through the Switch room, which is where message 4 is refused.\n")
anchor = "Omar gets the answer, the proof, and a plain line saying what he was *not* shown."
assert anchor in d
d = d.replace(anchor, seq + "\n" + anchor, 1)

stats = """**The recorded run, 6 Nov 2026, 16:56 IST:**

| Sealed steps | Shared | Attacks refused live | Switch message ids | Agent step errors | Judge checks |
|---|---|---|---|---|---|
| 10 | 1 | 4 of 4 | 14 | 0 | 11/11 |

"""
assert "### What Switch enforces for us" in d
d = d.replace("### What Switch enforces for us", stats + "### What Switch enforces for us", 1)

page = (root / "template.html").read_text()
pairs = re.findall(r"<details[^>]*><summary>(.*?)</summary><p>(.*?)</p></details>", page, re.S)


def md(s: str) -> str:
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s)
    s = re.sub(r'<a href="([^"]+)">(.*?)</a>', r"[\2](\1)", s)
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def lines(a: str) -> str:
    parts = re.split(r"(?<=\.) (?=[A-Z`])", md(a))
    return "\n".join(p.strip() for p in parts)


faq = "## Questions people ask us\n\n" + "\n\n".join(
    f"### {md(q)}\n\n{lines(a)}" for q, a in pairs) + "\n\n"
d = d.replace("## Try it in a minute", faq + "## Try it in a minute", 1)
d = re.sub(r"\[Interactive: .*?\]",
           "The interactive version of this post lets you edit the quote and watch the verdict "
           "flip from `OK` to `PROOF_FAIL`, with the Merkle path recomputed live: "
           "https://kadoo69.github.io/flipside-blog/#forge", d, flags=re.S)
d = re.sub(r"\[Diagram:.*?\]\n\n", "", d, flags=re.S)
d = re.sub(r"\[Flip card on each row\..*?\]\n\n", "", d, flags=re.S)
assert "[Diagram" not in d and "[Interactive" not in d and "[Flip card" not in d
(root / "index.md").write_text(d)
print(len(d.split()), "words")
