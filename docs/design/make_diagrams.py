"""Draw the landing page's diagrams in one style. Run: python3 docs/design/make_diagrams.py

# * Apple design language (apple/DESIGN.md): white canvas, parchment cards at
# * 18px radius, one near-black tile for the part that matters, Action Blue
# * (#0066cc) as the only accent, system fonts at weight 400 / 600, no
# * gradients, no shadows. Every diagram is plain SVG built from the same four
# * helpers, so a change of wording is a one-line edit and a re-run.
"""

from pathlib import Path
from xml.sax.saxutils import escape

# * Writes into livesite/assets/, which GitHub Pages publishes; this script is
# * kept out of that folder so it is not served itself.
HERE = Path(__file__).resolve().parents[2] / "livesite" / "assets"

INK, MUTED, BLUE = "#1d1d1f", "#6e6e73", "#0066cc"
PARCHMENT, TILE, ON_DARK, MUTED_DARK = "#f5f5f7", "#272729", "#ffffff", "#a1a1a6"
FONT = "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif"

STYLE = f"""<style>
text{{font-family:{FONT}}}
.h{{font-size:36px;font-weight:600;fill:{INK};letter-spacing:-0.28px}}
.eyebrow{{font-size:14px;font-weight:600;fill:{BLUE};letter-spacing:0.5px}}
.sub{{font-size:19px;fill:{MUTED}}}
.t{{font-size:20px;font-weight:600;fill:{INK};letter-spacing:-0.2px}}
.s{{font-size:16px;fill:{MUTED}}}
.td{{font-size:20px;font-weight:600;fill:{ON_DARK};letter-spacing:-0.2px}}
.sd{{font-size:16px;fill:{MUTED_DARK}}}
.n{{font-size:14px;font-weight:600;fill:#ffffff}}
.chip{{font-size:18px;font-weight:600;fill:{INK}}}
.foot{{font-size:16px;fill:{INK}}}
.arrow{{stroke:{BLUE};stroke-width:2;fill:none;marker-end:url(#a)}}
.dash{{stroke:{BLUE};stroke-width:2;fill:none;stroke-dasharray:6 6}}
</style>
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker></defs>"""


def svg(w: int, h: int, title: str, desc: str, body: list[str]) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
            f'aria-labelledby="title desc">\n<title id="title">{escape(title)}</title>'
            f'<desc id="desc">{escape(desc)}</desc>\n{STYLE}\n'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>\n' + "\n".join(body) + "\n</svg>\n")


def header(x: int, eyebrow: str, headline: str, sub: str = "") -> list[str]:
    out = [f'<text x="{x}" y="64" class="eyebrow">{escape(eyebrow)}</text>',
           f'<text x="{x}" y="108" class="h">{escape(headline)}</text>']
    if sub:
        out.append(f'<text x="{x}" y="142" class="sub">{escape(sub)}</text>')
    return out


def card(x: int, y: int, w: int, h: int, title: str, lines: list[str],
         num: str = "", dark: bool = False, key: bool = False) -> list[str]:
    """A parchment card (or the one dark tile), optional blue number badge."""
    fill = TILE if dark else ("#ffffff" if key else PARCHMENT)
    stroke = f' stroke="{BLUE}" stroke-width="2"' if key else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}"{stroke}/>']
    top = y + 34
    if num:
        out.append(f'<circle cx="{x + 32}" cy="{y + 32}" r="14" fill="{BLUE}"/>'
                   f'<text x="{x + 32}" y="{y + 37}" text-anchor="middle" class="n">{escape(num)}</text>')
        top = y + 82
    out.append(f'<text x="{x + 22}" y="{top}" class="{"td" if dark else "t"}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + 22}" y="{top + 28 + i * 22}" class="{"sd" if dark else "s"}">{escape(line)}</text>')
    return out


def chip(x: int, y: int, w: int, label: str, note: str = "") -> list[str]:
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="60" rx="18" fill="{PARCHMENT}"/>',
           f'<text x="{x + 22}" y="{y + 26}" class="chip">{escape(label)}</text>']
    if note:
        out.append(f'<text x="{x + 22}" y="{y + 48}" class="s">{escape(note)}</text>')
    return out


def arrow(d: str, dashed: bool = False) -> str:
    return f'<path d="{d}" class="{"dash" if dashed else "arrow"}"/>'


def footer(x: int, y: int, w: int, text: str) -> list[str]:
    return [f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="18" fill="{PARCHMENT}"/>',
            f'<text x="{x + w // 2}" y="{y + 32}" text-anchor="middle" class="foot">{escape(text)}</text>']


# * ------------------------------------------------------------------ intake
def intake() -> str:
    body = header(60, "01 · INTAKE", "State first. Answer less.",
                  "Every question belongs to a signed scheme the worker chose.")
    xs, w, y, h = [60, 280, 500, 720, 940], 200, 190, 170
    steps = [("Consent", ["Nothing that", "identifies her"]),
             ("Her state", ["All 36. A map on", "the web, buttons", "in chat"]),
             ("Which schemes", ["National, her", "state's, or both"]),
             ("Pick from list", ['Tick some, or', '"All of these"']),
             ("Questions", ["Only what those", "schemes need.", '"Don\'t know" ok'])]
    for i, (x, (t, lines)) in enumerate(zip(xs, steps)):
        body += card(x, y, w, h, t, lines, num=str(i + 1), key=(i in (1, 2, 3)))
        if i:
            body.append(arrow(f"M{x - 20} {y + h // 2} H{x - 4}"))
    body.append(arrow(f"M{940 + w // 2} {y + h} V{430} H{844}"))
    body += card(356, 400, 480, 110, "Temporary profile",
                 ["State · age · income band · the facts those schemes need.",
                  'No identity inferred. A missing answer never becomes "no".'], dark=True)
    return svg(1200, 560, "Intake",
               "The worker consents, gives her state, chooses national schemes, her state's or both, "
               "ticks schemes or all of them, and answers only the questions those schemes need. "
               "The answers form a temporary profile in memory; nothing identifies her.", body)


# * ----------------------------------------------------------------- verdict
def verdict() -> str:
    body = header(60, "02 · RULE ENGINE", "The rules decide. The bot explains.")
    body += card(60, 170, 300, 150, "Temporary profile",
                 ["Answers from this chat only.", "Never an identity record."], num="A")
    body += card(60, 360, 300, 150, "Scheme files",
                 ["Plain text, cited sources,", "signed by a person."], num="B")
    body += card(430, 220, 330, 240, "Rule engine",
                 ["Same answers, same verdict.", "", "No language model decides", "eligibility."],
                 num="C", dark=True)
    body.append(arrow("M360 245 H395 V300 H426"))
    body.append(arrow("M360 435 H395 V380 H426"))
    body.append(arrow("M760 340 H820"))
    body += chip(830, 180, 310, "✓  Eligible", "Every rule is met")
    body += chip(830, 310, 310, "✕  Ineligible", "A stated rule fails")
    body += chip(830, 440, 310, "?  Unknown", "Missing answer or unsigned rule")
    body.append(arrow("M820 340 V210 H826"))
    body.append(arrow("M820 340 V470 H826"))
    body += footer(60, 548, 1080, "The engine computes first. Language only presents the result.")
    return svg(1200, 630, "Rule engine",
               "The temporary profile and the signed scheme files go into a deterministic rule engine. "
               "It returns eligible, ineligible or unknown. No language model decides a verdict.", body)


# * ----------------------------------------------------------------- privacy
def privacy() -> str:
    body = header(60, "03 · PRIVACY", "Measure the flow. Never identify a person.",
                  "A pilot role separates testing from real use without asking who someone is.")
    body += card(60, 200, 300, 190, "Session profile",
                 ["Exact answers live only", "in memory, for this chat."], num="1", dark=True)
    body += card(430, 200, 340, 190, "Consented event",
                 ["Random session id · channel", "State · age and income bands",
                  "Optional: self / helping / tester", "Never the raw answers"], num="2")
    body += card(840, 200, 300, 190, "Aggregate report",
                 ["Screenings · results", "Sheets · pilot role mix"], num="3")
    body.append(arrow("M360 295 H426"))
    body.append(arrow("M770 295 H836"))
    body.append(arrow("M210 390 V440 H600 V394", dashed=True))
    body.append(f'<text x="405" y="470" text-anchor="middle" class="t">The profile stops here.</text>')
    body += footer(60, 520, 1080, "Never stored: name · phone · Aadhaar · exact income · exact location")
    return svg(1200, 610, "Privacy",
               "Exact answers stay in memory for the chat. With consent, only an event with a random "
               "session id, the channel, the state and coarse bands is logged, and only aggregates are "
               "reported. Name, phone, Aadhaar, exact income and exact location are never stored.", body)


# * -------------------------------------------------------------- system map
def system_map() -> str:
    body = header(60, "SYSTEM MAP", "One conversation. One rule engine. Three channels.")
    for i, name in enumerate(("Telegram", "WhatsApp", "Web page")):
        body += card(60, 180 + i * 110, 220, 90, name, ["Buttons" if i < 2 else "Map + buttons"])
        body.append(arrow(f"M280 {225 + i * 110} H340 V{335} H356" if i != 1 else "M280 335 H356"))
    body += card(360, 250, 280, 170, "Conversation",
                 ["State first, then", "only the questions", "the chosen schemes need"], num="1")
    body += card(700, 220, 300, 230, "Rule engine",
                 ["Signed scheme files in,", "a verdict out.", "", "Eligible · Ineligible ·", "Unknown"],
                 num="2", dark=True)
    body.append(arrow("M640 335 H696"))
    body += card(1060, 180, 290, 150, "Explanation",
                 ["Why, in her language", "What to carry"], num="3")
    body += card(1060, 350, 290, 150, "One-page sheet",
                 ["Documents and", "where to go"], num="4")
    body.append(arrow("M1000 300 H1030 V255 H1056"))
    body.append(arrow("M1000 370 H1030 V425 H1056"))
    body += card(360, 490, 280, 150, "Optional model",
                 ["May suggest an occupation", "for her to confirm.", "Never decides."])
    body.append(arrow("M500 490 V424", dashed=True))
    body += card(700, 520, 650, 90, "Measurement",
                 ["Consented, coarse events under a random id. No name, phone or Aadhaar."])
    body.append(arrow("M850 450 V516", dashed=True))
    return svg(1410, 690, "System map",
               "Telegram, WhatsApp and the web page feed one conversation, which asks the state first "
               "and only the needed questions. A rule engine over signed scheme files returns the "
               "verdict. Outputs are the explanation and a one-page sheet. An optional model may "
               "suggest an occupation for the worker to confirm, never a verdict. Measurement keeps "
               "only consented, coarse events.", body)


if __name__ == "__main__":
    for name, draw in (("backend-intake", intake), ("backend-verdict", verdict),
                       ("backend-privacy", privacy), ("system-map", system_map)):
        (HERE / f"{name}.svg").write_text(draw(), encoding="utf-8")
        print(f"wrote {name}.svg")
