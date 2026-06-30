"""Search target Douyin product IDs on the off-shelf list."""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"
DOUYIN_IDS = ["3828502999379083379", "3828502724442456211", "3828500873236054417"]


def set_input_value(page, value):
    return page.evaluate(
        """(value) => {
            const inputs = [...document.querySelectorAll('input')]
              .filter(e => e.offsetParent)
              .filter(e => (e.placeholder || '').includes('商品名称') || (e.placeholder || '').includes('商品ID'));
            const input = inputs[0];
            if (!input) return {ok:false, reason:'input not found'};
            input.scrollIntoView({block:'center', inline:'center'});
            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(input, value);
            input.dispatchEvent(new Event('input', {bubbles:true}));
            input.dispatchEvent(new Event('change', {bubbles:true}));
            return {ok:true, placeholder:input.placeholder};
        }""",
        value,
    )


def click_exact(page, text):
    return page.evaluate(
        """(text) => {
            const el = [...document.querySelectorAll('button, span, div')]
              .filter(e => e.offsetParent)
              .find(e => (e.innerText || e.textContent || '').trim() === text);
            if (!el) return false;
            el.scrollIntoView({block:'center', inline:'center'});
            el.click();
            return true;
        }""",
        text,
    )


def main():
    pw, ctx = launch()
    out = {}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://fxg.jinritemai.com/ffa/g/list", wait_until="domcontentloaded", timeout=90000)
        time.sleep(20)
        click_exact(page, "已下架")
        time.sleep(5)
        input_res = set_input_value(page, ",".join(DOUYIN_IDS))
        click_exact(page, "查询")
        time.sleep(12)
        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        controls = page.evaluate(
            """() => [...document.querySelectorAll('input, button, [role=button]')]
              .filter(e => e.offsetParent)
              .map((e, i) => ({
                i,
                tag: e.tagName,
                type: e.getAttribute('type') || '',
                checked: e.checked || false,
                text: (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || '').trim().slice(0, 120),
                rect: (() => { const r = e.getBoundingClientRect(); return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)} })()
              }))
              .slice(0, 260)
            """
        )
        out = {
            "url": page.url,
            "input": input_res,
            "found_ids": [pid for pid in DOUYIN_IDS if pid in text],
            "text": text[:16000],
            "controls": controls,
        }
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "dy_target_goods_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        page.screenshot(path=str(REPORT_DIR / "dy_target_goods_probe.png"), full_page=True)
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
