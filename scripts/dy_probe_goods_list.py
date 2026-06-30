"""Probe Douyin goods list using the system Edge profile."""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"


def main():
    pw, ctx = launch()
    out = {}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://fxg.jinritemai.com/ffa/g/list?status=2", wait_until="domcontentloaded", timeout=90000)
        time.sleep(20)
        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        controls = page.evaluate(
            """() => [...document.querySelectorAll('input, textarea, button, [role=button]')]
              .filter(e => e.offsetParent)
              .map((e, i) => ({
                i,
                tag: e.tagName,
                type: e.getAttribute('type') || '',
                text: (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || '').trim().slice(0, 120),
                cls: String(e.className || '').slice(0, 120)
              }))
              .filter(x => x.text || x.tag === 'INPUT')
              .slice(0, 240)
            """
        )
        out = {"url": page.url, "text": text[:12000], "controls": controls}
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "dy_goods_list_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        page.screenshot(path=str(REPORT_DIR / "dy_goods_list_probe.png"), full_page=True)
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
