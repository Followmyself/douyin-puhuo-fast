"""从晓风铺货预览列表保留 3 个商品并执行单店铺货。"""
import json
import re
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"

KEEP_IDS = {"896528132548", "1047092512685", "1026659454588"}


def click_text(page, text, exact=True):
    return page.evaluate(
        """([text, exact]) => {
            const els = [...document.querySelectorAll('button, div, span')]
              .filter(e => e.offsetParent);
            const btn = els.find(e => {
                const t = (e.innerText || e.textContent || '').trim();
                return exact ? t === text : t.includes(text);
            });
            if (!btn) return false;
            btn.scrollIntoView({block:'center', inline:'center'});
            btn.click();
            return true;
        }""",
        [text, exact],
    )


def current_ids(page):
    text = page.evaluate("document.body ? document.body.innerText : ''") or ""
    return re.findall(r"ID:\s*(\d+)", text)


def delete_id(page, goods_id):
    result = page.evaluate(
        """(goodsId) => {
            const roots = [...document.querySelectorAll('div, tr, section, article')]
              .filter(e => (e.innerText || '').includes('ID: ' + goodsId) || (e.innerText || '').includes('ID:' + goodsId));
            roots.sort((a,b) => (a.innerText || '').length - (b.innerText || '').length);
            const root = roots.find(r => (r.innerText || '').includes('删除商品')) || roots[0];
            if (!root) return {ok:false, reason:'root not found'};
            const btn = [...root.querySelectorAll('button, div, span')]
              .filter(e => e.offsetParent)
              .find(e => (e.innerText || e.textContent || '').trim() === '删除商品');
            if (!btn) return {ok:false, reason:'delete button not found', rootText:(root.innerText || '').slice(0,300)};
            btn.scrollIntoView({block:'center', inline:'center'});
            btn.click();
            return {ok:true};
        }""",
        goods_id,
    )
    time.sleep(1)
    for label in ["确定", "确认", "删除", "仍要删除"]:
        if click_text(page, label, exact=True):
            time.sleep(2)
            break
    return result


def main():
    pw, ctx = launch()
    out = {"keep_ids": sorted(KEEP_IDS), "deleted": [], "publish": {}}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        url = f"https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html?t={int(time.time()*1000)}#/home/previewList"
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(25)

        ids = list(dict.fromkeys(current_ids(page)))
        out["initial_ids"] = ids
        for goods_id in ids:
            if goods_id in KEEP_IDS:
                continue
            res = delete_id(page, goods_id)
            out["deleted"].append({"id": goods_id, "result": res})
            time.sleep(2)

        time.sleep(5)
        out["remaining_ids"] = list(dict.fromkeys(current_ids(page)))
        page.screenshot(path=str(REPORT_DIR / "xf_before_publish_three.png"), full_page=True)

        # 若仍有预警弹层/面板，选择智能修改后继续。
        click_text(page, "我同意智能修改，继续发布", exact=True)
        time.sleep(2)

        # 执行单店铺货。
        clicked = page.evaluate(
            """() => {
                const btn = [...document.querySelectorAll('button')]
                  .filter(e => e.offsetParent)
                  .find(e => (e.innerText || '').includes('单店铺货'));
                if (!btn) return false;
                btn.scrollIntoView({block:'center', inline:'center'});
                btn.click();
                return true;
            }"""
        )
        out["publish"]["clicked_single_shop"] = clicked
        time.sleep(5)

        for label in ["我同意智能修改，继续发布", "跳过尺码规格异常商品，继续发布", "保留商品，继续发布", "确定", "确认"]:
            if click_text(page, label, exact=True):
                out["publish"].setdefault("confirm_clicked", []).append(label)
                time.sleep(8)

        time.sleep(60)
        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        out["publish"]["final_text"] = text[:8000]
        out["publish"]["url"] = page.url
        page.screenshot(path=str(REPORT_DIR / "xf_after_publish_three.png"), full_page=True)
        (REPORT_DIR / "xf_publish_three.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
