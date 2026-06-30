---
name: douyin_puhuo_skills
description: 抖音小店快速大量铺货自动化。用于按已验证流程执行：抖店/罗盘选品、晓风截流、1688 以图搜款、去抖音铺货、铺货预览发布、晓风上货记录校验；尤其适用于 VPN 开启后 Edge/晓风插件按钮点不动、晓风弹窗卡住的场景。
---

# 抖音快速铺货 Skill

用于“搜索运营/罗盘热品 -> 晓风截流 -> 1688 以图搜款 -> 抖店铺货 -> 晓风记录校验”的批量流程。

默认交付边界：铺货成功后，抖店商品进入“已下架/审核通过或已提审”即可；不要默认替用户批量上架，除非用户明确要求。

## 关键原则

1. 优先使用系统 Edge Default profile，保留用户已登录的抖店、罗盘、晓风状态。
2. 开 VPN 后不要依赖插件按钮点击；直接打开晓风内部路由更稳。
3. Edge 启动必须带代理绕过：
   `*.jinritemai.com;*.douyin.com;*.zzbtool.com;*.zzbtool.cn;*.1688.com;*.alicdn.com;*.taobao.com;*.tmall.com;api-fuwu.zzbtool.com;plug*.zzbtool.com;<local>`
4. 晓风上货记录不能只打开 `#/move_list`，必须带 `activeKey=moveList`，例如 `#/move_list?type=moveList` 或 `#/iframe/move?type=moveList`。
5. 若用户只要求“铺货”，做到晓风“铺货成功”且抖店商品状态为“已下架/审核通过或已提审”即可停止。
6. 只有用户明确要求“上架”时才进入抖店商品管理批量上架；上架前必须检查库存。库存为 0 的商品即使铺货成功、审核通过，也不能成功上架。
7. 晓风弹窗处理规则：
   - “检测到您上次有未提交的铺货数据，是否继续铺货”：直接点击“继续铺货”。
   - “尺码及规格问题预警 / 商品可能存在侵权风险”：按用户当前偏好，逐个点击“保留商品，继续发布”，不要自动删除。
   - 如果页面白屏或 `document.body.innerText` 为空，重新打开带新时间戳的 `#/home/previewList`，必要时刷新重试。

## 常用脚本

脚本在本 skill 的 `scripts/` 目录中，原项目路径通常是：
`C:\Users\温涛\desktop\vscode\claude-code-douyin-operator\scripts`

优先从原项目运行；若原项目丢失，再使用本 skill 备份脚本。

```powershell
cd C:\Users\温涛\desktop\vscode\claude-code-douyin-operator
```

### 诊断 VPN/登录/插件

```powershell
python scripts\xf_probe_vpn.py
python scripts\xf_probe_system_profile.py
```

### 从罗盘提取商品

```powershell
python scripts\xf_extract_products.py
```

输出：`reports\xf_products.json`

批量 100 件候选使用：

```powershell
python scripts\xf_extract_products_100.py
```

输出：`reports\xf_products_100.json`

### 打开晓风内部截流路由

使用 `xf_open_internal_route.py` 的 `launch()`，它会：
- 关闭普通插件按钮依赖
- 加载晓风扩展
- 使用系统 Edge Default profile
- 添加 VPN 代理绕过

### 获取 1688 货源并进入铺货预览

```powershell
python scripts\xf_probe_to_preview.py
python scripts\xf_open_preview.py
```

批量加入铺货预览使用分批脚本，每批 10 个候选较稳：

```powershell
python scripts\xf_to_preview_batch.py --start 0 --limit 10
python scripts\xf_to_preview_batch.py --start 10 --limit 10
python scripts\xf_to_preview_batch.py --start 20 --limit 10
```

要点：
- 每批结束看 `reports\xf_to_preview_batch_<start>_<limit>.json` 的 `preview_count`。
- `status=no_candidate` 是正常情况，表示该候选没有合适 1688 货源或被平台过滤。
- 如果 `preview_count` 和预期不一致，先运行 `python scripts\xf_open_preview.py` 看真实预览页，不要盲目重复提交。

### 发布铺货预览商品

小批测试：

```powershell
python scripts\xf_publish_three.py
```

大量铺货时使用：

```powershell
python scripts\xf_publish_preview_batch.py --min-count 1
```

该脚本必须具备以下行为：
- 打开 `#/home/previewList` 后，如果白屏或页面文本为空，自动换时间戳/刷新重试。
- 遇到“检测到您上次有未提交的铺货数据”弹窗，自动点击“继续铺货”。
- 遇到“保留商品，继续发布”按钮，逐个点击直到按钮消失。
- 遇到“我同意智能修改，继续发布”“跳过尺码规格异常商品，继续发布”，按页面提示继续。
- 提交后保存 `reports\xf_publish_preview_batch.json`，重点看 `submitted_ids` 和 `final_text` 中的“执行完毕，共铺货 N 个商品”。

### 校验晓风上货记录

```powershell
python scripts\xf_check_move_variants.py
```

优先看 `reports\xf_move_variants.json` 中 `#/move_list?type=moveList` 或 `#/iframe/move?type=moveList` 的结果。

更稳的最近记录校验脚本：

```powershell
python scripts\xf_check_move_recent.py
```

校验标准：
- 上货记录中目标 1688 商品 ID 可找到。
- 状态为“铺货成功”。
- 抖店商品 ID 已生成。
- 抖店商品状态为“已下架”。
- 审核状态为“审核通过”或“已提审”。“审核不通过”要记录并跳过，不默认处理。

### 抖店上架校验（仅用户明确要求时）

```powershell
python scripts\dy_probe_target_goods.py
python scripts\dy_relist_three.py
```

如果某个商品库存为 0，改用 `dy_relist_replacement.py` 搜索有库存的替换商品。

如果用户说“我手动上架”或“只要铺货到已下架”，不要运行上架脚本。

## 本次实战结论（2026-06-30）

- 关键词：雨伞。
- 成功跑通大批量流程：罗盘候选 -> 晓风 1688 找货源 -> 预览列表 -> 单店铺货 -> 晓风记录确认。
- 两个高频卡点已经确认：
  1. 未提交数据弹窗：点“继续铺货”。
  2. 尺码/侵权风险预警：点每条“保留商品，继续发布”。
- 用户当前偏好：不需要自动上架，只要铺货成功后商品进入抖店“已下架”即可，后续用户手动批量上架。
- 上货记录页分页/可见行会影响总数统计；不要只看页面总成功数。应按 `xf_publish_preview_batch.json` 的 `submitted_ids` 到 `xf_move_recent.json` 文本里逐项核对。
- Edge Default profile 经常被占用。自动化前可关闭 Edge：

```powershell
Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 操作流程

详细步骤、已知坑和验证标准见：
`references/puhuo-workflow.md`

## 安全边界

- 不改价格，除非用户明确指定。
- 不处理封禁/审核驳回商品，除非用户明确要求。
- 大批量发布前先小批量验证：晓风记录“铺货成功”、抖店商品“售卖中”、库存大于 0。
- 使用系统 Edge profile 时，脚本可能需要关闭当前 Edge 窗口释放配置锁。
