"""
make_tutorial_screenshots.py – takes the annotated screenshots for the tutorial tab (0a).

Opens the running LAGER web page in headless Google Chrome, goes through the steps
with the example target, and saves the pictures with numbered markers and arrows to
static/tutorial/. The numbers match the lists in templates/webpage_tutorial.html.
Run it again after changing the page layout.

    python data_prep/make_tutorial_screenshots.py --url http://127.0.0.1:5000

Needs: a running LAGER server, google-chrome, and the Python packages
websocket-client (pip install websocket-client) and Pillow. The example search takes ~1 minute.
"""
import argparse
import base64
import io
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "static" / "tutorial"
EXAMPLE = "Clc1c(Cl)cc(NC(=O)CC(=O)NO)cc1"
SCALE = 2                       # device pixels per CSS pixel (sharp on high-resolution screens)
WIDTH = 1400                    # wide enough for all six tabs in one row
MARK = (232, 89, 12)            # orange markers
PAD = 70                        # page margin around a panel, room for the markers


# ---------------------------------------------------------------------------
# A small Chrome DevTools client
# ---------------------------------------------------------------------------
class Browser:
    def __init__(self):
        with socket.socket() as sock:              # a free port for Chrome's DevTools
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.profile = tempfile.mkdtemp(prefix="lager-chrome-")
        self.proc = subprocess.Popen(
            ["google-chrome", "--headless=new", f"--remote-debugging-port={port}",
             f"--user-data-dir={self.profile}", "--hide-scrollbars", "--no-first-run", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                pages = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                ws = next(p["webSocketDebuggerUrl"] for p in pages if p["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        else:
            self.close()
            raise RuntimeError("Chrome did not start.")
        try:
            self.ws = websocket.create_connection(ws, timeout=120, suppress_origin=True)
        except Exception:
            self.close()
            raise
        self.next_id = 0

    def call(self, method, **params):
        self.next_id += 1
        self.ws.send(json.dumps({"id": self.next_id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.next_id:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in result:
            raise RuntimeError(f"JavaScript error in: {expression}\n{result['exceptionDetails']}")
        return result["result"].get("value")

    def wait_for(self, expression, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            if self.js(f"!!({expression})"):
                return
            time.sleep(0.3)
        raise RuntimeError(f"Timed out waiting for: {expression}")

    def viewport(self, height):
        self.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=height,
                  deviceScaleFactor=SCALE, mobile=False)

    def rect(self, selector):
        """Position of an element on the page in CSS pixels: (x, y, width, height)."""
        r = self.js(f"""(() => {{ const e = document.querySelector({json.dumps(selector)});
            if (!e) return null; const b = e.getBoundingClientRect();
            return [b.x + scrollX, b.y + scrollY, b.width, b.height]; }})()""")
        if r is None:
            raise RuntimeError(f"Not on the page: {selector}")
        return r

    def shot(self, x, y, w, h):
        data = self.call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                         clip={"x": x, "y": y, "width": w, "height": h, "scale": 1})["data"]
        return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")

    def close(self):
        self.proc.terminate()
        self.proc.wait()
        shutil.rmtree(self.profile, ignore_errors=True)


# ---------------------------------------------------------------------------
# Markers: an orange frame around an element, a numbered circle beside it and an arrow
# ---------------------------------------------------------------------------
def font(size):
    for name in ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def annotate(image, origin, marks):
    """marks: [(number, (x, y, w, h) on the page, side of the circle: left/right/top/bottom)]"""
    draw = ImageDraw.Draw(image)
    s = SCALE
    for number, (x, y, w, h), side in marks:
        x0, y0 = (x - origin[0] - 4) * s, (y - origin[1] - 4) * s
        x1, y1 = (x - origin[0] + w + 4) * s, (y - origin[1] + h + 4) * s
        draw.rounded_rectangle((x0, y0, x1, y1), radius=8 * s, outline=MARK, width=3 * s)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        gap, r = 46 * s, 15 * s
        circle, tip = {
            "left": ((x0 - gap, cy), (x0 - 2 * s, cy)),
            "right": ((x1 + gap, cy), (x1 + 2 * s, cy)),
            "top": ((cx, y0 - gap), (cx, y0 - 2 * s)),
            "bottom": ((cx, y1 + gap), (cx, y1 + 2 * s)),
        }[side]
        # arrow from the circle to the frame
        dx, dy = tip[0] - circle[0], tip[1] - circle[1]
        length = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / length, dy / length
        start = (circle[0] + ux * r, circle[1] + uy * r)
        base = (tip[0] - ux * 10 * s, tip[1] - uy * 10 * s)
        draw.line((start, base), fill=MARK, width=3 * s)
        draw.polygon([tip, (base[0] - uy * 6 * s, base[1] + ux * 6 * s),
                      (base[0] + uy * 6 * s, base[1] - ux * 6 * s)], fill=MARK)
        draw.ellipse((circle[0] - r, circle[1] - r, circle[0] + r, circle[1] + r), fill=MARK)
        draw.text(circle, str(number), fill="white", font=font(17 * s), anchor="mm")
    return image


def save(image, name):
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name, optimize=True)
    print("saved", OUT / name)


def panel_shot(b, panel, marks, name, bottom=None):
    """Screenshot of a panel (with a margin) and its markers. bottom: selector to stop after."""
    x, y, w, h = b.rect(panel)
    if bottom:
        bx, by, bw, bh = b.rect(bottom)
        h = by + bh - y
    origin = (x - PAD, y - 20)
    image = b.shot(origin[0], origin[1], w + 2 * PAD, h + 40)
    save(annotate(image, origin, [(n, b.rect(sel), side) for n, sel, side in marks]), name)


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    b = Browser()
    try:
        b.viewport(2400)
        b.call("Page.navigate", url=args.url.rstrip("/") + "/#tutorial")
        b.wait_for("document.readyState === 'complete' && window.LagerRules && LagerRules.selectedCount() > 0")
        b.wait_for("window.JSApplet && JSApplet.JSME && document.querySelector('#editor .jsa-resetDiv')", 60)
        b.js("localStorage.clear()")

        # Example target (the tutorial's "Try this example" button)
        b.js("document.querySelector('[data-example-smiles]').click()")
        time.sleep(1.5)

        # 1. Overview: a normal window with the tabs and the bar at the bottom
        b.viewport(820)
        time.sleep(0.5)
        image = b.shot(0, 0, WIDTH, 820)
        save(annotate(image, (0, 0), [
            (1, b.rect("#tab-tutorial"), "left"),
            (2, b.js("""(() => { const a = document.querySelector('#tab-target').getBoundingClientRect(),
                        z = document.querySelector('#tab-results').getBoundingClientRect();
                        return [a.x, a.y, z.right - a.x, a.height]; })()"""), "top"),
            (3, b.rect("#run-summary"), "left"),
            (4, b.rect("#run"), "top"),
        ]), "overview.png")
        b.viewport(2400)

        # 2. Target molecule
        panel_shot(b, "#panel-target", [(1, "#editor", "left"), (2, "#smiles", "left")], "target.png")

        # 3. Starting materials
        b.js("LagerTabs.show('reagents')")
        panel_shot(b, "#panel-reagents", [(1, "#reactants-status", "left"),
                                         (2, "label[for='reactants-file']", "left")], "materials.png")

        # 4. Reaction rules: open a folder and show one rule
        b.js("LagerTabs.show('rules')")
        b.js("""[...document.querySelectorAll('.group-toggle')]
                .find(t => t.textContent.includes('Grignard')).click()""")
        b.js("""[...document.querySelectorAll('.rule-row .rule-name')]
                .find(t => t.textContent === 'Grignard keto aldeh').click()""")
        b.wait_for("document.querySelector('#rule-detail svg')")
        b.js("""(() => { const g = [...document.querySelectorAll('.rule-group')]
                .find(g => g.textContent.includes('Grignard'));
                const list = document.querySelector('#rules-list');
                list.scrollTop += g.getBoundingClientRect().top - list.getBoundingClientRect().top - 50; })()""")
        time.sleep(0.5)
        b.js("""(() => { const g = [...document.querySelectorAll('.rule-group')]
                .find(g => g.textContent.includes('Grignard'));
                g.querySelector(':scope > .rule-head').id = 'tutorial-group';
                g.querySelector('.rule-row.selected').id = 'tutorial-rule'; })()""")
        panel_shot(b, "#rules-card", [
            (1, "#rules-filter", "left"),
            (2, "#tutorial-group", "left"),
            (3, "#tutorial-rule", "left"),
            (4, "#rule-detail .direction-toggle", "left"),
            (5, "#rule-detail .rv-panel, #rule-detail svg", "left"),
            (6, "#rule-add > summary", "left"),
        ], "rules.png")

        # 5. Results: start the search, show the progress, then the pathways
        b.js("document.querySelector('#run').click()")
        b.wait_for("!document.querySelector('#progress').hidden && document.querySelector('#log').textContent.length > 0", 60)
        time.sleep(4)
        panel_shot(b, "#progress", [(1, "#status", "left"), (2, "#log", "left")], "progress.png")
        b.wait_for("!document.querySelector('#results').hidden || !document.querySelector('#results-empty').hidden", 900)
        b.wait_for("[...document.querySelectorAll('#pathways img')].every(i => i.complete && i.naturalWidth)", 60)
        panel_shot(b, "#results", [
            (1, "#zip", "right"),
            (2, "#pathways .pathway img", "left"),
            (3, "#pathways .pathway .links", "left"),
        ], "results.png", bottom="#pathways .pathway")
    finally:
        b.close()


if __name__ == "__main__":
    main()
