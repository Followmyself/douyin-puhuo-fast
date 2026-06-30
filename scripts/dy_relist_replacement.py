"""Relist one replacement product with available inventory."""
import json
import re
import time
from pathlib import Path

from xf_open_internal_route import launch
from dy_probe_target_goods import click_exact, set_input_value

REPORT_DIR = Path(__file__).parent.parent / "reports"
CANDIDATE_IDS = [
    "3828474734023147647",
    "3828475344000778272",
    "3828465164869566774",
    "3828322524802974880",
]


def text(page):
    return page.evaluate("document.body ? document.body.innerText : ''") or ""


def search(page, ids):
    page.goto("https://fxg.jinritemai.com/ffa/g/list", wait_until="domcontentloaded", timeout=90000)
    time.sleep(18)
    click_exact(page, "已下架")
    time.sleep(5)
    set_input_value(page, ",".join(ids))
    click_exact(page, "查询")
    time.sleep(12)


def row_snippet(body_text, goods_id):
    idx = body_text.find("ID:" + goods_id)
    if idx < 0:
        return ""
    return body_text[max(0, idx - 160): min(len(body_text), idx + 420)]


def click_row_action(page, goods_id, action_text):
    return page.evaluate(
        """([goodsId, actionText]) => {
            const roots = [...document.querySelectorAll('tr, div')]
              .filter(e => (e.innerText || '').includes('ID:' + goodsId));
            roots.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
            const root = roots.find(r => [...r.querySelectorAll('button, a, span, div')]
              .some(e => (e.innerText || e.textContent || '').trim() === actionText));
            if (!root) return {ok:false, reason:'row/action not found'};
            const el = [...root.querySelectorAll('button, a, span, div')]
              .filter(e => e.offsetParent)
              .find(e => (e.innerText || e.textContent || '').trim() === actionText);
            if (!el) return {ok:false, reason:'action element not visible'};
            el.scrollIntoView({block:'center', inline:'center'});
            el.click();
            return {ok:true};
        }""",
        [goods_id, action_text],
    )


def click_confirm(page):
    clicked = []
    for label in ["上架", "确认上架", "确定", "确认"]:
        ok = page.evaluate(
            """(label) => {
              const btns = [...document.querySelectorAll('button')].filter(e => e.offsetParent && (e.innerText || '').trim() === label);
              if (!btns.length) return false;
              btns[btns.length - 1].click();
              return true;
            }""",
            label,
        )
        if ok:
            clicked.append(label)
            time.sleep(8)
    return clicked


def main():
    pw, ctx = launch()
    out = {"candidate_ids": CANDIDATE_IDS}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        search(page, CANDIDATE_IDS)
        body = text(page)
        found = [pid for pid in CANDIDATE_IDS if pid in body]
        out["found"] = found
        out["snippets"] = {pid: row_snippet(body, pid) for pid in found}
        chosen = ""
        for pid in found:
            snip = out["snippets"][pid]
            numbers = [int(x) for x in re.findall(r"\n(\d+)\n", snip)]
            if any(n > 0 for n in numbers):
                chosen = pid
                break
        if not chosen and found:
            chosen = found[0]
        out["chosen"] = chosen
        if chosen:
            out["click_action"] = click_row_action(page, chosen, "上架")
            time.sleep(5)
            out["confirm_before"] = text(page)[-4000:]
            out["confirm_clicked"] = click_confirm(page)
            time.sleep(25)
            out["after_action"] = text(page)[:8000]
            page.screenshot(path=str(REPORT_DIR / "dy_relist_replacement_after_action.png"), full_page=True)
            search(page, [chosen])
            out["offline_after"] = {"found": chosen in text(page), "text": text(page)[:6000]}
            page.screenshot(path=str(REPORT_DIR / "dy_relist_replacement_offline_after.png"), full_page=True)
            click_exact(page, "售卖中")
            time.sleep(5)
            set_input_value(page, chosen)
            click_exact(page, "查询")
            time.sleep(10)
            out["selling_after"] = {"found": chosen in text(page), "text": text(page)[:6000]}
            page.screenshot(path=str(REPORT_DIR / "dy_relist_replacement_selling_after.png"), full_page=True)
        (REPORT_DIR / "dy_relist_replacement.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
