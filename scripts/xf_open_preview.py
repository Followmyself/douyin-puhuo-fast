"""打开晓风铺货预览列表并导出页面文本/截图。"""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"


def main():
    pw, ctx = launch()
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        url = f"https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html?t={int(time.time()*1000)}#/home/previewList"
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(25)
        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        controls = page.evaluate(
            """() => [...document.querySelectorAll('button, input, textarea, select, [class*=btn], [class*=Button]')]
              .filter(e => e.offsetParent)
              .map((e,i) => ({i, tag:e.tagName, text:(e.innerText || e.value || e.placeholder || '').trim().slice(0,100), cls:String(e.className||'').slice(0,80)}))
              .filter(x => x.text)
              .slice(0,200)
            """
        )
        out = {"url": page.url, "text": text[:8000], "controls": controls}
        (REPORT_DIR / "xf_preview.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        page.screenshot(path=str(REPORT_DIR / "xf_preview.png"), full_page=True)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
