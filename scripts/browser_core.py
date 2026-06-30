"""
抖店浏览器自动化核心封装
基于 Playwright，替代 OpenClaw 的 browser 工具

主要改进 vs 原版 OpenClaw browser:
- page.evaluate() 无表达式限制，支持完整 JS 语句
- page.fill() 自动触发 React 合成事件，无需手动 dispatchEvent
- CSS 选择器定位，彻底解决 ref 失效问题
- 原生 try/catch 错误处理，不需要 || 'ok' 防 undefined
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional, Any
from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
)

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent / "config"
AUTH_STATE_FILE = CONFIG_DIR / "auth_state.json"

# 抖店基础 URL
BASE_URL = "https://fxg.jinritemai.com"


class DouyinBrowser:
    """抖店浏览器操作封装"""

    def __init__(
        self,
        headless: bool = False,
        viewport: dict = None,
        timeout: int = 30000,
    ):
        """
        初始化浏览器

        Args:
            headless: 是否无头模式（首次登录需要 False）
            viewport: 视窗大小，默认 1440x900
            timeout: 默认超时时间（毫秒）
        """
        self.headless = headless
        self.viewport = viewport or {"width": 1440, "height": 900}
        self.timeout = timeout

        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        """启动 Edge 浏览器"""
        import os
        self._playwright = sync_playwright().start()

        # 使用项目内持久化 Profile，保留抖店/晓风登录态。
        user_dir = str(CONFIG_DIR / "browser_profile")
        xf_extension_dir = (
            Path.home()
            / "AppData"
            / "Local"
            / "Microsoft"
            / "Edge"
            / "User Data"
            / "Default"
            / "UnpackedExtensions"
            / "晓风电商助手正式版30.3.3_23608_221725413"
        )

        args = [
            "--enable-extensions",
            # VPN 开启后 Edge 会继承系统代理；晓风/抖店/1688 这些站点直连更稳定。
            "--proxy-bypass-list=*.jinritemai.com;*.douyin.com;*.zzbtool.com;*.zzbtool.cn;*.1688.com;*.alicdn.com;*.taobao.com;*.tmall.com;<local>",
        ]
        if xf_extension_dir.exists():
            ext = str(xf_extension_dir)
            args.extend([f"--disable-extensions-except={ext}", f"--load-extension={ext}"])

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=user_dir,
            channel="msedge",
            headless=self.headless,
            viewport=self.viewport,
            locale="zh-CN",
            ignore_default_args=["--disable-extensions"],
            args=args,
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.timeout)
        logger.info("Edge 已启动 (headless=%s)", self.headless)

    def close(self):
        """关闭浏览器"""
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("浏览器已关闭")

    @property
    def page(self) -> Page:
        """获取当前页面"""
        if not self._page:
            raise RuntimeError("浏览器未启动，请先调用 start()")
        return self._page

    # ─── 导航 ───────────────────────────────────────────

    def navigate(self, path: str, wait_seconds: float = 3.0) -> bool:
        """
        导航到抖店后台页面

        Args:
            path: URL 路径，如 '/ffa/g/list?status=2'
            wait_seconds: 页面加载后等待秒数（抖店 React 渲染慢）

        Returns:
            是否导航成功
        """
        url = f"{BASE_URL}{path}" if path.startswith("/") else path
        logger.info("导航到: %s", url)
        try:
            self.page.goto(url, wait_until="domcontentloaded")
            time.sleep(wait_seconds)  # 等待 React 渲染
            return True
        except PlaywrightTimeout:
            logger.warning("导航超时: %s", url)
            return False

    # ─── 截图 ───────────────────────────────────────────

    def screenshot(self, path: str = None, full_page: bool = False) -> bytes:
        """
        页面截图

        Args:
            path: 保存路径，None 则只返回 bytes
            full_page: 是否全页截图

        Returns:
            截图的 PNG bytes
        """
        return self.page.screenshot(path=path, full_page=full_page)

    # ─── JS 执行 ────────────────────────────────────────

    def evaluate(self, expression: str) -> Any:
        """
        在页面中执行 JavaScript（无表达式限制！）

        相比原版 OpenClaw evaluate：
        - ✅ 支持 const/let/var 声明
        - ✅ 支持多行语句
        - ✅ 支持 async/await
        - ✅ 原生返回，不需要 || 'ok' 防 undefined

        Args:
            expression: JavaScript 代码字符串

        Returns:
            JS 执行结果
        """
        try:
            return self.page.evaluate(expression)
        except Exception as e:
            logger.error("JS 执行失败: %s", str(e)[:200])
            return None

    def evaluate_async(self, expression: str) -> Any:
        """
        执行异步 JS（返回 Promise）

        Args:
            expression: JavaScript 代码（可包含 await）

        Returns:
            Promise resolve 的结果
        """
        try:
            # 包装为 async 函数执行
            wrapped = f"(async () => {{ {expression} }})()"
            return self.page.evaluate(wrapped)
        except Exception as e:
            logger.error("异步 JS 执行失败: %s", str(e)[:200])
            return None

    # ─── 点击操作 ───────────────────────────────────────

    def click(self, selector: str, timeout: int = None) -> bool:
        """
        点击元素（用选择器，不依赖 ref）

        Args:
            selector: CSS 选择器
            timeout: 超时（ms）

        Returns:
            是否点击成功
        """
        try:
            self.page.click(selector, timeout=timeout or self.timeout)
            return True
        except Exception as e:
            logger.warning("点击失败 [%s]: %s", selector, str(e)[:100])
            return False

    def click_by_text(self, text: str, tag: str = "button") -> bool:
        """
        按文本内容点击元素

        替代原版:
          [...document.querySelectorAll('button')].find(b => b.innerText.includes('下架'))?.click()

        Args:
            text: 要匹配的文本
            tag: HTML 标签类型

        Returns:
            是否点击成功
        """
        try:
            self.page.click(f"{tag}:has-text('{text}')")
            return True
        except Exception as e:
            logger.warning("按文本点击失败 [%s]: %s", text, str(e)[:100])
            return False

    # ─── 输入操作 ───────────────────────────────────────

    def fill(self, selector: str, text: str) -> bool:
        """
        填写输入框（自动触发 React 合成事件！）

        Playwright 的 fill() 会自动触发:
        - focus → input → change → blur
        - 不需要原版的 nativeInputValueSetter hack

        Args:
            selector: CSS 选择器
            text: 要填入的文本

        Returns:
            是否填写成功
        """
        try:
            self.page.fill(selector, text)
            return True
        except Exception as e:
            logger.warning("填写失败 [%s]: %s", selector, str(e)[:100])
            return False

    # ─── 等待 ───────────────────────────────────────────

    def wait_for_selector(self, selector: str, timeout: int = None) -> bool:
        """
        等待元素出现

        Args:
            selector: CSS 选择器
            timeout: 超时（ms）

        Returns:
            是否等到
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
            return True
        except PlaywrightTimeout:
            logger.warning("等待元素超时: %s", selector)
            return False

    def wait_for_text(self, text: str, timeout: int = None) -> bool:
        """
        等待页面出现指定文本

        Args:
            text: 文本内容
            timeout: 超时（ms）

        Returns:
            是否等到
        """
        try:
            self.page.wait_for_function(
                f"document.body.innerText.includes('{text}')",
                timeout=timeout or self.timeout,
            )
            return True
        except PlaywrightTimeout:
            logger.warning("等待文本超时: %s", text)
            return False

    def sleep(self, seconds: float):
        """等待指定秒数"""
        time.sleep(seconds)

    # ─── 登录态管理 ─────────────────────────────────────

    def save_auth_state(self):
        """保存当前登录态到文件"""
        storage = self._context.storage_state()
        AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTH_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(storage, f, ensure_ascii=False, indent=2)
        logger.info("登录态已保存到: %s", AUTH_STATE_FILE)

    @staticmethod
    def has_auth_state() -> bool:
        """检查是否已有登录态"""
        return AUTH_STATE_FILE.exists()

    # ─── 常用选择器 ─────────────────────────────────────

    # 以下选择器对应原版 browser-automation.md 中的常用选择器
    SELECTORS = {
        "搜索框": 'input[placeholder*="商品名称"]',
        "全选复选框": 'thead input[type="checkbox"]',
        "分页下一页": '.ecom-g-pagination-next, [class*=pagination] [class*=next]',
        "虚拟滚动容器": '.ecom-table-body',
        "商品行ID": '[class*=row] [class*=id], a[href*="goods"]',
    }

    def get_selector(self, name: str) -> str:
        """获取预定义选择器"""
        return self.SELECTORS.get(name, name)


# ─── 快捷函数（供其他脚本直接使用）─────────────────────


def create_browser(headless: bool = None) -> DouyinBrowser:
    """
    创建浏览器实例，自动读取配置

    Args:
        headless: 覆盖配置文件中的 headless 设置

    Returns:
        DouyinBrowser 实例
    """
    import yaml

    settings_file = CONFIG_DIR / "settings.yaml"
    config = {}
    if settings_file.exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    browser_config = config.get("operation", {}).get("browser", {})

    return DouyinBrowser(
        headless=headless if headless is not None else browser_config.get("headless", False),
        viewport={
            "width": browser_config.get("viewport_width", 1440),
            "height": browser_config.get("viewport_height", 900),
        },
        timeout=browser_config.get("timeout", 30000),
    )


if __name__ == "__main__":
    # 简单自测
    logging.basicConfig(level=logging.INFO)
    with create_browser() as browser:
        browser.navigate("/ffa/mcompass/overview")
        browser.screenshot("test_screenshot.png")
        print("截图已保存到 test_screenshot.png")
