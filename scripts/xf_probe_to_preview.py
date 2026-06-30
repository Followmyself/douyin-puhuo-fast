"""选择一个 1688 货源并进入晓风铺货预览页。"""
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from xf_open_internal_route import launch, PLUG_ID

REPORT_DIR = Path(__file__).parent.parent / "reports"


def parse_price(text: str):
    m = re.search(r"\n\s*([0-9]+(?:\.[0-9]+)?)\s*$", text)
    return float(m.group(1)) if m else None


def main():
    products = json.loads((REPORT_DIR / "xf_products.json").read_text(encoding="utf-8"))
    prod = products[0]
    pw, ctx = launch()
    out = {"product": prod}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        url = (
            "https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html"
            f"?t={int(time.time()*1000)}#/searchSimilarGoodsIframe"
            f"?t=2&title={quote(prod['title'])}&img={quote(prod['img'], safe='')}"
            f"&price=0&price2=&plugId={PLUG_ID}"
        )
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(20)
        candidates = page.evaluate(
            """() => {
                const rows = [...document.querySelectorAll('tr, [class*=row], [class*=item], [class*=goods]')];
                const out = [];
                for (const row of rows) {
                    const text = (row.innerText || '').trim();
                    if (!/ID：\\d+/.test(text) || !/回头率/.test(text)) continue;
                    const r = row.getBoundingClientRect();
                    const cb = row.querySelector('input[type=checkbox], .el-checkbox, [class*=checkbox], [class*=Checkbox]');
                    let cbr = cb ? cb.getBoundingClientRect() : null;
                    out.push({
                        text: text.slice(0, 500),
                        x: r.x, y: r.y, w: r.width, h: r.height,
                        cb: cbr ? {x:cbr.x, y:cbr.y, w:cbr.width, h:cbr.height} : null
                    });
                }
                return out.slice(0, 30);
            }"""
        )
        scored = []
        for c in candidates:
            text = c["text"]
            rate_m = re.search(r"回头率(\d+)%", text)
            price = parse_price(text)
            rate = int(rate_m.group(1)) if rate_m else 0
            ok = price is not None and 5 <= price <= 25 and rate >= 45 and ("包邮" in text or "7天无理由" in text)
            scored.append({**c, "price": price, "rate": rate, "ok": ok})
        chosen = next((c for c in scored if c["ok"]), scored[0] if scored else None)
        chosen_id = re.search(r"ID：(\d+)", chosen["text"]).group(1) if chosen and re.search(r"ID：(\d+)", chosen["text"]) else ""
        out["candidates"] = scored[:10]
        out["chosen"] = chosen
        out["chosen_id"] = chosen_id
        if not chosen:
            raise RuntimeError("没有找到可选货源")
        selected = page.evaluate(
            """(goodsId) => {
                const rows = [...document.querySelectorAll('tr, [class*=row], [class*=item], [class*=goods]')];
                const row = rows.find(r => (r.innerText || '').includes(goodsId));
                if (!row) return {ok:false, reason:'row not found'};
                row.scrollIntoView({block:'center', inline:'center'});
                const cb = row.querySelector('input[type=checkbox]');
                if (cb) {
                    cb.click();
                    cb.dispatchEvent(new Event('change', {bubbles:true}));
                    return {ok:true, by:'input'};
                }
                const box = row.querySelector('.el-checkbox, [class*=checkbox], [class*=Checkbox]');
                if (box) {
                    box.click();
                    return {ok:true, by:'box'};
                }
                return {ok:false, reason:'checkbox not found', text:(row.innerText || '').slice(0,200)};
            }""",
            chosen_id,
        )
        out["select_result"] = selected
        time.sleep(1)
        page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button,div,span')]
                  .filter(e => e.offsetParent)
                  .find(e => (e.innerText || '').trim() === '去抖音铺货');
                if (btn) btn.click();
            }"""
        )
        time.sleep(35)
        page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button,div,span')]
                  .filter(e => e.offsetParent)
                  .find(e => (e.innerText || '').trim() === '打开铺货预览列表');
                if (btn) btn.click();
            }"""
        )
        time.sleep(20)
        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        out["after_text"] = text[:5000]
        out["has_preview"] = any(k in text for k in ["晓风铺货预览", "预览商品数据", "单店铺货", "SKU价格库存"])
        out["url_after"] = page.url
        page.screenshot(path=str(REPORT_DIR / "xf_probe_to_preview.png"), full_page=True)
        (REPORT_DIR / "xf_probe_to_preview.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
