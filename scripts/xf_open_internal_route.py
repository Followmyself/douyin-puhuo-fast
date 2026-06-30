"""直接打开晓风截流内部路由，绕过按钮点击失效问题。"""
import json
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

REPORT_DIR = Path(__file__).parent.parent / "reports"
EDGE_USER_DATA = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"
XF_EXTENSION = EDGE_USER_DATA / "Default" / "UnpackedExtensions" / "晓风电商助手正式版30.3.3_23608_221725413"
PLUG_ID = "gcfohjiejngbnepafbldkbmjgeclehdn"


def launch():
    args = [
        "--profile-directory=Default",
        "--enable-extensions",
        "--proxy-bypass-list=*.jinritemai.com;*.douyin.com;*.zzbtool.com;*.zzbtool.cn;*.1688.com;*.alicdn.com;*.taobao.com;*.tmall.com;api-fuwu.zzbtool.com;plug*.zzbtool.com;<local>",
    ]
    if XF_EXTENSION.exists():
        ext = str(XF_EXTENSION)
        args.extend([f"--disable-extensions-except={ext}", f"--load-extension={ext}"])
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(EDGE_USER_DATA),
        channel="msedge",
        headless=False,
        viewport={"width": 2560, "height": 1534},
        locale="zh-CN",
        ignore_default_args=["--disable-extensions"],
        args=args,
    )
    return pw, ctx


def main():
    pw, ctx = launch()
    result = {}
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(
            "https://compass.jinritemai.com/shop/search/industry-terms/detail"
            "?word=%25E9%259B%25A8%25E4%25BC%259E&prepages%5B0%5D=%2Fshop%2Fchance%2Fsearch-word",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        time.sleep(10)
        product = page.evaluate(
            """() => {
                const imgs = [...document.images].map(img => img.src).filter(src => /ecom|com|alicdn|p9|p3/.test(src));
                const text = document.body.innerText;
                const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
                const title = lines.find(s => s.length > 20 && /雨伞|伞/.test(s)) || '';
                return {title, img: imgs[0] || '', plugId: localStorage.getItem('xiaofengDyOrderPlugId') || ''};
            }"""
        )
        plug_id = product.get("plugId") or PLUG_ID
        url = (
            "https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html"
            f"?t={int(time.time()*1000)}#/searchSimilarGoodsIframe"
            f"?t=2&title={quote(product['title'])}&img={quote(product['img'], safe='')}"
            f"&price=0&price2=&plugId={quote(plug_id)}"
        )
        result["product"] = product
        result["url"] = url
        xf = ctx.new_page()
        xf.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(20)
        text = xf.evaluate("document.body ? document.body.innerText : ''") or ""
        result["text_len"] = len(text)
        result["has_search_panel"] = any(k in text for k in ["模板选择", "1688以图搜款", "去抖音铺货", "来源商品信息"])
        result["excerpt"] = text[:3000]
        xf.screenshot(path=str(REPORT_DIR / "xf_internal_route.png"), full_page=True)
        (REPORT_DIR / "xf_internal_route.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
