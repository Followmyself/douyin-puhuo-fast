"""Relist the three test Douyin products and verify the result."""
import json
import time
from pathlib import Path

from xf_open_internal_route import launch
from dy_probe_target_goods import DOUYIN_IDS, click_exact, set_input_value

REPORT_DIR = Path(__file__).parent.parent / "reports"


def visible_text(page):
    return page.evaluate("document.body ? document.body.innerText : ''") or ""


def click_target_rows(page):
    coords = page.evaluate(
        """(ids) => {
            const result = [];
            for (const id of ids) {
                const roots = [...document.querySelectorAll('tr, div')]
                  .filter(e => (e.innerText || '').includes('ID:' + id) && e.querySelector('input[type=checkbox]'));
                roots.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
                const root = roots[0];
                if (!root) {
                    result.push({id, ok:false, reason:'row not found'});
                    continue;
                }
                const cb = root.querySelector('input[type=checkbox]');
                cb.scrollIntoView({block:'center', inline:'center'});
                const r = cb.getBoundingClientRect();
                result.push({id, ok:true, x:r.x, y:r.y, w:r.width, h:r.height});
            }
            return result;
        }""",
        DOUYIN_IDS,
    )
    for item in coords:
        if item.get("ok"):
            page.mouse.click(item["x"] + max(4, item.get("w", 16) / 2), item["y"] + max(4, item.get("h", 16) / 2))
            time.sleep(0.8)
    text = visible_text(page)
    return {"coords": coords, "selected_text": "已选3条" in text, "selected_excerpt": text[text.find("已选") : text.find("已选") + 50] if "已选" in text else ""}


def click_toolbar_relist(page):
    return page.evaluate(
        """() => {
            const buttons = [...document.querySelectorAll('button')]
              .filter(e => e.offsetParent && (e.innerText || '').trim() === '批量上架')
              .map(e => ({e, r:e.getBoundingClientRect()}))
              .filter(x => x.r.x < 1200 && x.r.y > 350);
            buttons.sort((a, b) => a.r.y - b.r.y);
            if (!buttons.length) return {ok:false, reason:'toolbar relist button not found'};
            buttons[0].e.scrollIntoView({block:'center', inline:'center'});
            buttons[0].e.click();
            return {ok:true, x:buttons[0].r.x, y:buttons[0].r.y};
        }"""
    )


def click_confirm(page):
    labels = ["上架", "确认上架", "确定上架", "确认", "确定", "我知道了"]
    clicked = []
    for label in labels:
        ok = page.evaluate(
            """(label) => {
                const buttons = [...document.querySelectorAll('button')]
                  .filter(e => e.offsetParent)
                  .filter(e => (e.innerText || e.textContent || '').trim() === label);
                if (!buttons.length) return false;
                buttons[buttons.length - 1].scrollIntoView({block:'center', inline:'center'});
                buttons[buttons.length - 1].click();
                return true;
            }""",
            label,
        )
        if ok:
            clicked.append(label)
            time.sleep(5)
    return clicked


def search_targets(page, tab_text):
    page.goto("https://fxg.jinritemai.com/ffa/g/list", wait_until="domcontentloaded", timeout=90000)
    time.sleep(18)
    click_exact(page, tab_text)
    time.sleep(5)
    set_input_value(page, ",".join(DOUYIN_IDS))
    click_exact(page, "查询")
    time.sleep(12)
    text = visible_text(page)
    return {
        "tab": tab_text,
        "url": page.url,
        "found_ids": [pid for pid in DOUYIN_IDS if pid in text],
        "has_selling": "售卖中" in text,
        "has_offline": "已下架" in text,
        "text": text[:12000],
    }


def main():
    pw, ctx = launch()
    out = {"target_ids": DOUYIN_IDS}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        before = search_targets(page, "已下架")
        out["before"] = before
        if sorted(before["found_ids"]) != sorted(DOUYIN_IDS):
            out["error"] = "target ids not all found before relist"
        else:
            out["select"] = click_target_rows(page)
            time.sleep(2)
            page.screenshot(path=str(REPORT_DIR / "dy_before_relist_three.png"), full_page=True)
            out["click_relist"] = click_toolbar_relist(page)
            time.sleep(5)
            out["confirm_text_before"] = visible_text(page)[-5000:]
            out["confirm_clicked"] = click_confirm(page)
            time.sleep(25)
            out["after_action_text"] = visible_text(page)[:12000]
            page.screenshot(path=str(REPORT_DIR / "dy_after_relist_action.png"), full_page=True)
            out["verify_selling"] = search_targets(page, "售卖中")
            page.screenshot(path=str(REPORT_DIR / "dy_verify_selling_three.png"), full_page=True)
            out["verify_offline"] = search_targets(page, "已下架")
            page.screenshot(path=str(REPORT_DIR / "dy_verify_offline_three.png"), full_page=True)

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "dy_relist_three.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
