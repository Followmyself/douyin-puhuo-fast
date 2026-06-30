"""用系统 Edge 默认 Profile 诊断晓风插件和抖店登录态。"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


REPORT_DIR = Path(__file__).parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

EDGE_USER_DATA = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"
XF_EXTENSION = (
    EDGE_USER_DATA
    / "Default"
    / "UnpackedExtensions"
    / "晓风电商助手正式版30.3.3_23608_221725413"
)


def txt(page):
    return page.evaluate("document.body ? document.body.innerText : ''") or ""


def main():
    result = {}
    args = [
        "--profile-directory=Default",
        "--enable-extensions",
        "--proxy-bypass-list=*.jinritemai.com;*.douyin.com;*.zzbtool.com;*.zzbtool.cn;*.1688.com;*.alicdn.com;*.taobao.com;*.tmall.com;<local>",
    ]
    if XF_EXTENSION.exists():
        ext = str(XF_EXTENSION)
        args.extend([f"--disable-extensions-except={ext}", f"--load-extension={ext}"])

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(EDGE_USER_DATA),
            channel="msedge",
            headless=False,
            viewport={"width": 1600, "height": 1000},
            locale="zh-CN",
            ignore_default_args=["--disable-extensions"],
            args=args,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(30000)
        try:
            result["service_workers"] = [w.url for w in context.service_workers]
            page.goto("https://fxg.jinritemai.com/ffa/mcompass/search", wait_until="domcontentloaded", timeout=60000)
            time.sleep(8)
            t1 = txt(page)
            result["fxg_url"] = page.url
            result["fxg_title"] = page.title()
            result["fxg_text_len"] = len(t1)
            result["fxg_logged"] = "扫码登录" not in t1 and ("搜索运营" in t1 or "抖店" in t1)
            page.screenshot(path=str(REPORT_DIR / "system_profile_fxg.png"), full_page=True)

            compass_url = (
                "https://compass.jinritemai.com/shop/search/industry-terms/detail"
                "?word=%25E9%259B%25A8%25E4%25BC%259E"
                "&prepages%5B0%5D=%2Fshop%2Fchance%2Fsearch-word"
            )
            page.goto(compass_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(10)
            t2 = txt(page)
            result["compass_url"] = page.url
            result["compass_title"] = page.title()
            result["compass_text_len"] = len(t2)
            result["compass_logged"] = "扫码登录" not in t2 and ("词下热门商品" in t2 or "搜索词分析" in t2)
            result["has_xf"] = "晓风" in t2
            result["has_button"] = any(k in t2 for k in ["晓风批量截流", "晓风截流", "批量截流"])
            page.screenshot(path=str(REPORT_DIR / "system_profile_compass.png"), full_page=True)

            click = page.evaluate(
                """() => {
                    const all = [...document.querySelectorAll('button,a,span,div')]
                      .filter(e => e.offsetParent)
                      .map(e => ({el:e, text:(e.innerText || e.textContent || '').trim()}))
                      .filter(x => x.text && x.text.length < 40 && /晓风.*截流|批量截流/.test(x.text));
                    const target = (all.find(x => /^晓风批量截流/.test(x.text)) || all.find(x => x.text === '晓风截流') || all[0])?.el;
                    if (!target) return {clicked:false, count:0, candidates: all.map(x => x.text)};
                    target.scrollIntoView({block:'center', inline:'center'});
                    target.click();
                    return {clicked:true, count:all.length, text:(target.innerText || target.textContent || '').trim(), candidates: all.map(x => x.text).slice(0,20)};
                }"""
            )
            result["click"] = click
            time.sleep(8)
            t3 = txt(page)
            result["after_click_has_panel"] = any(k in t3 for k in ["模板选择", "AI截流", "1688以图搜款", "去抖音铺货"])
            result["after_click_excerpt"] = t3[:2000]
            page.screenshot(path=str(REPORT_DIR / "system_profile_after_click.png"), full_page=True)
        finally:
            with open(REPORT_DIR / "xf_probe_system_profile.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            context.close()


if __name__ == "__main__":
    main()
