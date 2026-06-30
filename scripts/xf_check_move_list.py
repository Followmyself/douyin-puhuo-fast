"""Open Xiaofeng move list and export the latest publish records."""
import json
import re
import time
from pathlib import Path

from xf_open_internal_route import launch

REPORT_DIR = Path(__file__).parent.parent / "reports"
TARGET_IDS = {"896528132548", "1047092512685", "1026659454588"}


def extract_records(text):
    records = []
    for goods_id in sorted(TARGET_IDS):
        idx = text.find(goods_id)
        if idx < 0:
            records.append({"id": goods_id, "found": False})
            continue
        start = max(0, idx - 500)
        end = min(len(text), idx + 1000)
        snippet = text[start:end]
        status = ""
        for candidate in ["成功", "失败", "进行中", "正在后台进行中", "已完成", "铺货中", "异常"]:
            if candidate in snippet:
                status = candidate
                break
        records.append({"id": goods_id, "found": True, "status_hint": status, "snippet": snippet})
    return records


def main():
    pw, ctx = launch()
    out = {}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        url = f"https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html?t={int(time.time()*1000)}#/move_list"
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(25)

        # Switch common filters to the latest records if the page exposes tabs/buttons.
        for label in ["全部", "近7天", "今天", "刷新"]:
            page.evaluate(
                """(label) => {
                    const el = [...document.querySelectorAll('button, span, div')]
                      .filter(e => e.offsetParent)
                      .find(e => (e.innerText || e.textContent || '').trim() === label);
                    if (el) el.click();
                }""",
                label,
            )
            time.sleep(1)

        text = page.evaluate("document.body ? document.body.innerText : ''") or ""
        out["url"] = page.url
        out["records"] = extract_records(text)
        out["ids_on_page"] = sorted(set(re.findall(r"\b\d{11,14}\b", text)))
        out["text"] = text[:12000]
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "xf_move_list_check.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        page.screenshot(path=str(REPORT_DIR / "xf_move_list_check.png"), full_page=True)
        print(json.dumps(out, ensure_ascii=True, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
