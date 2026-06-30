"""Try Xiaofeng move-list route variants and capture visible content."""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"


def main():
    pw, ctx = launch()
    out = []
    try:
        variants = [
            "#/move_list",
            "#/move_list?type=moveList",
            "#/iframe/move",
            "#/iframe/move?type=moveList",
        ]
        for i, route in enumerate(variants, start=1):
            page = ctx.new_page()
            failures = []
            statuses = []
            page.on("requestfailed", lambda req: failures.append({"url": req.url, "failure": str(req.failure)}))
            page.on("response", lambda res: statuses.append({"url": res.url, "status": res.status}) if ("move" in res.url.lower() or "order" in res.url.lower() or "zzb" in res.url.lower()) else None)
            url = f"https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html?t={int(time.time()*1000)}{route}"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(35)
            text = page.evaluate("document.body ? document.body.innerText : ''") or ""
            page.screenshot(path=str(REPORT_DIR / f"xf_move_variant_{i}.png"), full_page=True)
            out.append({
                "route": route,
                "url": page.url,
                "text_len": len(text),
                "text": text[:4000],
                "failures": failures[:20],
                "statuses": statuses[-40:],
            })
            page.close()
        (REPORT_DIR / "xf_move_variants.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
