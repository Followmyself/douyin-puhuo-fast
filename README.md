# 抖音快速铺货 Skill (douyin-puhuo-fast)

抖音小店快速批量铺货自动化工具，用于"搜索运营/罗盘热品 → 晓风截流 → 1688 以图搜款 → 抖店铺货 → 晓风记录校验"的批量流程。

## 适用场景

- VPN 开启后 Edge/晓风插件按钮点不动
- 晓风弹窗频繁卡住（未提交数据、尺码/侵权预警）
- 需要批量从罗盘选品并铺货到抖店

## 目录结构

```
douyin-puhuo-fast/
├── SKILL.md                    # Skill 定义文件（核心文档）
├── agents/
│   └── openai.yaml             # Agent 配置
├── scripts/                    # 自动化脚本
│   ├── browser_core.py         # Playwright 浏览器核心封装
│   ├── xf_probe_vpn.py         # 诊断 VPN 状态
│   ├── xf_probe_system_profile.py # 检查登录/插件状态
│   ├── xf_open_internal_route.py  # 打开晓风内部路由（绕过按钮点击）
│   ├── xf_extract_products.py  # 从罗盘提取候选商品
│   ├── xf_probe_to_preview.py  # 1688 以图搜款并生成铺货预览
│   ├── xf_open_preview.py      # 打开铺货预览列表
│   ├── xf_publish_three.py     # 小批量测试发布（3个商品）
│   ├── xf_check_move_list.py   # 校验晓风上货记录
│   ├── xf_check_move_variants.py # 多路由校验晓风上货记录
│   ├── dy_probe_goods_list.py  # 探测抖店商品列表
│   ├── dy_probe_target_goods.py # 探测目标商品状态
│   ├── dy_relist_three.py      # 抖店批量上架
│   └── dy_relist_replacement.py # 替换无库存商品后上架
└── references/
    └── puhuo-workflow.md       # 详细工作流文档
```

## 快速开始

### 1. 检查环境

```powershell
python scripts/xf_probe_system_profile.py
```

确保：抖店已登录、罗盘可访问、晓风扩展正常工作。

### 2. 提取候选商品

```powershell
python scripts/xf_extract_products.py
```

输出：`reports/xf_products.json`

### 3. 搜 1688 货源并生成铺货预览

```powershell
python scripts/xf_probe_to_preview.py
python scripts/xf_open_preview.py
```

### 4. 小批量铺货测试

```powershell
python scripts/xf_publish_three.py
```

### 5. 校验结果

```powershell
python scripts/xf_check_move_variants.py
```

## 关键原则

1. 优先使用系统 Edge Default profile，保留已登录状态
2. 开 VPN 后不依赖插件按钮点击，直接走晓风内部路由
3. Edge 启动需带代理绕过列表
4. 晓风上货记录必须带 `activeKey=moveList` 参数
5. 铺货后默认不自动上架，除非用户明确要求
6. 上架前必须检查库存，库存为 0 不可上架

## 环境要求

- Windows 11
- Python 3.10+
- Playwright（`pip install playwright`）
- Microsoft Edge 浏览器
- 晓风电商助手扩展

## 安全边界

- 不改价格（除非用户明确指定）
- 不处理封禁/审核驳回商品（除非用户明确要求）
- 大批量发布前必须先小批量验证
- 使用系统 Edge profile 时可能需要关闭当前 Edge 窗口释放配置锁

## License

MIT
