"""诊断 VPN 开启时晓风插件是否可用，不执行铺货发布。"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_core import create_browser


REPORT_DIR = Path(__file__).parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def visible_text(page):
    return page.evaluate("document.body ? document.body.innerText : ''") or ""


def main():
    result = {}
    browser = create_browser(False)
    browser.start()
    page = browser.page

    try:
        result["proxy_check_url"] = "system proxy is bypassed by Edge args for key domains"
        result["pages_initial"] = [p.url for p in browser._context.pages]
        result["service_workers"] = [w.url for w in browser._context.service_workers]

        # 先访问晓风站点，确认插件后台服务和账号页面能加载。
        page.goto("https://xfdyorder.zzbtool.com/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        txt = visible_text(page)
        result["xf_url"] = page.url
        result["xf_title"] = page.title()
        result["xf_text_len"] = len(txt)
        result["xf_has_login"] = ("登录" in txt or "退出登录" in txt or "欢迎" in txt)
        page.screenshot(path=str(REPORT_DIR / "probe_xf_home.png"), full_page=True)

        # 打开与视频一致的罗盘搜索词详情页。
        compass_url = (
            "https://compass.jinritemai.com/shop/search/industry-terms/detail"
            "?word=%25E9%259B%25A8%25E4%25BC%259E"
            "&prepages%5B0%5D=%2Fshop%2Fchance%2Fsearch-word"
        )
        page.goto(compass_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        txt = visible_text(page)
        result["compass_url"] = page.url
        result["compass_title"] = page.title()
        result["compass_text_len"] = len(txt)
        result["has_douyin_login"] = ("登录" not in txt[:500] and "词下热门商品" in txt)
        result["has_xf_text"] = ("晓风" in txt)
        result["has_batch_button"] = ("晓风批量截流" in txt or "批量截流" in txt)
        result["has_single_button"] = ("晓风截流" in txt)

        # 只尝试点击“晓风批量截流”或第一个“晓风截流”，不点去铺货。
        click_result = page.evaluate(
            """() => {
                const candidates = [...document.querySelectorAll('button, a, span, div')]
                    .filter(e => e.offsetParent && /晓风.*截流|批量截流/.test(e.innerText || ''));
                const info = candidates.slice(0, 10).map(e => ({
                    text: (e.innerText || '').trim().slice(0, 80),
                    tag: e.tagName,
                    cls: e.className
                }));
                const target = candidates.find(e => /晓风批量截流|批量截流/.test(e.innerText || '')) || candidates[0];
                if (!target) return {clicked: false, reason: 'no button', candidates: info};
                target.scrollIntoView({block: 'center', inline: 'center'});
                target.click();
                return {clicked: true, text: (target.innerText || '').trim().slice(0, 80), candidates: info};
            }"""
        )
        result["click_result"] = click_result
        time.sleep(8)
        txt2 = visible_text(page)
        result["after_click_url"] = page.url
        result["after_click_text_len"] = len(txt2)
        result["after_click_has_xf_panel"] = any(
            key in txt2
            for key in ["模板选择", "AI截流", "1688以图搜款", "去抖音铺货", "晓风截流"]
        )
        result["after_click_excerpt"] = txt2[:2000]
        page.screenshot(path=str(REPORT_DIR / "probe_after_click.png"), full_page=True)

    finally:
        with open(REPORT_DIR / "xf_probe_vpn.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
