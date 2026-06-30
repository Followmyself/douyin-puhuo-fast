"""从罗盘搜索词页提取可用于晓风截流的商品标题和主图。"""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"


def main():
    pw, ctx = launch()
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(
            "https://compass.jinritemai.com/shop/search/industry-terms/detail"
            "?word=%25E9%259B%25A8%25E4%25BC%259E&prepages%5B0%5D=%2Fshop%2Fchance%2Fsearch-word",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        time.sleep(10)
        products = page.evaluate(
            """() => {
                const rows = [...document.querySelectorAll('tr, [class*=table] [class*=row], [class*=Table] [class*=row]')];
                const out = [];
                for (const row of rows) {
                    const text = (row.innerText || '').trim();
                    if (!/晓风截流/.test(text) || !/店铺：/.test(text)) continue;
                    const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
                    const title = lines.find(s => s.length > 18 && /伞|雨/.test(s) && !/晓风|店铺|价格|曝光/.test(s));
                    const img = [...row.querySelectorAll('img')]
                        .map(i => i.currentSrc || i.src)
                        .find(src => src && !/svg|data:/.test(src));
                    if (title && img) out.push({title, img, text: text.slice(0, 300)});
                }
                if (!out.length) {
                    const cards = [...document.querySelectorAll('div')].filter(d => /晓风截流/.test(d.innerText || '') && /店铺：/.test(d.innerText || ''));
                    for (const card of cards) {
                        const text = (card.innerText || '').trim();
                        const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
                        const title = lines.find(s => s.length > 18 && /伞|雨/.test(s) && !/晓风|店铺|价格|曝光/.test(s));
                        const img = [...card.querySelectorAll('img')]
                            .map(i => i.currentSrc || i.src)
                            .find(src => src && !/svg|data:/.test(src));
                        if (title && img) out.push({title, img, text: text.slice(0, 300)});
                    }
                }
                const seen = new Set();
                return out.filter(p => {
                    const key = p.title + p.img;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                }).slice(0, 10);
            }"""
        )
        (REPORT_DIR / "xf_products.json").write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(products, ensure_ascii=False, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
