---
name: douyin-puhuo-fast
description: 抖音小店快速铺货 — 从罗盘选品→晓风截流→1688以图搜款→单店发布→记录校验。用于抖音店铺货、选品上架、批量铺货。当用户提到"铺货"、"上货"、"抖店铺货"、"1688铺货"时使用。
---

# 抖音快速铺货 Skill (v2)

## 一句话

从抖店罗盘搜索词选品 → 晓风1688以图搜款 → 单店铺货，一条命令搞定。

## 前置条件

- Windows 11 + Python 3.10+
- Microsoft Edge（系统 Default profile 已登录抖店/罗盘/晓风）
- 晓风电商助手扩展（`gcfohjiejngbnepafbldkbmjgeclehdn`）
- Playwright：`pip install playwright`

## 快速使用

### 一条命令铺货

```powershell
cd "$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator"
python scripts/puhuo.py --word <搜索词> --count <数量>
```

**示例**：

```powershell
# 铺3件雨伞
python scripts/puhuo.py --word 雨伞 --count 3

# 铺5件T恤，网络慢加大等待
python scripts/puhuo.py --word T恤 --count 5 --wait-scale 3.0
```

### 分步执行（调试用）

```powershell
# 1. 提取候选商品
python scripts/xf_extract_products_100.py --word 雨伞 --target 120

# 2. 逐个铺货（单产品闭环）
python scripts/xf_puhuo_publish_each.py --start 0 --limit 3 --target 3 --wait-scale 2.0
```

## 核心原则

1. **按曝光排序**：候选商品按"商品曝光用户数"从高到低
2. **单产品闭环**：每个商品独立完成"找1688源→去抖音铺货→打开预览→单店铺货"
3. **1688去重**：同一1688货源ID不重复铺货（除非 `--allow-duplicate-goods`）
4. **不自动上架**：铺货后商品为"已下架"状态，需手动上架
5. **不批量添加预览**：晓风预览列表不稳定，不能批量添加后再批量发布

## 工作流

```
罗盘搜索词 → 词下热门商品（按曝光排序）→ 晓风截图 → 1688以图搜款
    → 选1688货源（去重、排除品牌/侵权）→ 去抖音铺货 → 获取商品数据
    → 打开铺货预览 → 单店铺货 → 提交成功（审核通过/已下架）
```

## 弹窗处理

| 弹窗 | 操作 |
|------|------|
| "有未提交的铺货数据" | 点击"继续铺货" |
| 尺码/规格异常警告 | 点击"保留商品，继续发布" |
| 侵权风险提示 | 点击"保留商品，继续发布" |
| 页面空白 | 重新打开晓风页面（带时间戳URL） |

## 铺货后校验

```powershell
# 校验晓风上货记录
python scripts/xf_check_move_variants.py

# 查看抖店商品状态
python scripts/dy_probe_target_goods.py
```

## 报告解读

报告文件：`reports/xf_puhuo_publish_each_<start>_<limit>.json`

常见状态：
- `published_clicked` + 非空 `submitted_ids`：**铺货成功**
- `no_candidate`：没有符合条件的1688货源
- `duplicate_candidate`：所有货源都已铺过（去重拦截）
- `all_sources_failed`：所有尝试的货源都获取数据失败
- `unknown_after_click`：点击"去抖音铺货"后未进入预览状态

## 项目目录

所有脚本位于：`$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator\scripts\`

## 禁用项（不要用）

- 不要用 `xf_puhuo_fast_runner.py`
- 不要用 `xf_to_preview_batch.py` 批量添加预览
- 不要用 `xf_publish_preview_batch.py` 批量发布
- 不要为了凑成功数而扩大候选范围
- 不要重复铺同一1688货源ID
