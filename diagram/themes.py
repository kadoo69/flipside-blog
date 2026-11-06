"""Write the Mermaid light and dark configs that build.py renders diagram/sequence.mmd with."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMON = {"fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif", "fontSize": "15px"}
SEQ = {"diagramMarginX": 8, "diagramMarginY": 8, "actorMargin": 56, "messageMargin": 44,
       "boxMargin": 12, "boxTextMargin": 6, "noteMargin": 12, "mirrorActors": False,
       "showSequenceNumbers": True, "messageFontSize": 15, "actorFontSize": 15, "noteFontSize": 14}
LIGHT = dict(COMMON, background="transparent", primaryColor="#fffdf9", primaryBorderColor="#d9cfbf",
             primaryTextColor="#23252a", lineColor="#7a7e86", textColor="#23252a",
             actorBkg="#fffdf9", actorBorder="#d9cfbf", actorTextColor="#23252a",
             actorLineColor="#d6cfc2", signalColor="#55595f", signalTextColor="#23252a",
             sequenceNumberColor="#fffdf9", noteBkgColor="#f6ead2", noteBorderColor="#e6d3a6",
             noteTextColor="#5b4310", labelBoxBkgColor="#fffdf9", labelBoxBorderColor="#d9cfbf",
             labelTextColor="#23252a")
DARK = dict(COMMON, background="transparent", primaryColor="#24272c", primaryBorderColor="#3a3e45",
            primaryTextColor="#ebe8e1", lineColor="#9b9ea5", textColor="#ebe8e1",
            actorBkg="#24272c", actorBorder="#3a3e45", actorTextColor="#ebe8e1",
            actorLineColor="#3a3e45", signalColor="#b4b6bc", signalTextColor="#ebe8e1",
            sequenceNumberColor="#17181b", noteBkgColor="#2d2a22", noteBorderColor="#4a4231",
            noteTextColor="#e8cf98", labelBoxBkgColor="#24272c", labelBoxBorderColor="#3a3e45",
            labelTextColor="#ebe8e1")

if __name__ == "__main__":
    for name, tv in (("light", LIGHT), ("dark", DARK)):
        cfg = {"theme": "base", "themeVariables": tv, "sequence": SEQ}
        (HERE / f"{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
