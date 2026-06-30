# 抖音快速铺货工作流

## 已验证环境

- 系统：Windows 11
- 浏览器：Microsoft Edge，系统 Default profile
- 插件：晓风电商助手，扩展 ID `gcfohjiejngbnepafbldkbmjgeclehdn`
- 关键登录态：抖店、罗盘、晓风都在系统 Edge Default profile 中
- VPN 问题：系统代理开启后，Edge 会继承代理，晓风按钮/iframe/API 容易失效

## VPN 下的稳定启动方式

使用 `xf_open_internal_route.py` 中的 `launch()`：

- `user_data_dir` 指向系统 Edge User Data
- `--profile-directory=Default`
- 加载晓风未打包扩展
- 添加 `--proxy-bypass-list`

如果 profile 被占用，先关闭 Edge：

```powershell
Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 视频流程理解

视频中的人工流程：

1. 抖店“搜索运营”
2. 搜索词：雨伞
3. 罗盘“词下热门商品”
4. 商品卡片点击“晓风截流”
5. 晓风窗口选择模板：`3倍雨伞【默认模板】`
6. 开启 AI 截流，默认 `1688以图搜款`
7. 勾选 1688 货源
8. 点击“去抖音铺货”
9. 进入铺货预览
10. 处理标题、类目、属性、SKU、图片、资质
11. 点击“单店铺货”
12. 到上货记录检查结果

自动化实现中，步骤 4 不依赖按钮点击，而是直接打开晓风内部路由：

```text
https://xfdyorder.zzbtool.com/zzb_super_goods_xf/index.html?t=...#/searchSimilarGoodsIframe?t=2&title=...&img=...&price=0&price2=&plugId=gcfohjiejngbnepafbldkbmjgeclehdn
```

## 推荐执行顺序

### 1. 检查登录和插件

```powershell
python scripts\xf_probe_system_profile.py
```

确认：
- 抖店已登录
- 罗盘可访问
- 晓风 service worker 存在
- 页面能加载 `xfdyorder.zzbtool.com`

### 2. 提取候选商品

```powershell
python scripts\xf_extract_products.py
```

输出：

```text
reports\xf_products.json
```

用于拿商品标题和主图，拼接晓风内部路由。

### 3. 搜 1688 货源并生成铺货预览

```powershell
python scripts\xf_probe_to_preview.py
```

注意：
- 只勾选目标行，不要误点全选。
- 若弹出侵权/异常提示，跳过高风险商品。
- 成功后到铺货预览检查数量。

### 4. 打开铺货预览

```powershell
python scripts\xf_open_preview.py
```

确认预览列表中只保留要发布的商品。

### 5. 单店铺货

小批量测试：

```powershell
python scripts\xf_publish_three.py
```

大量铺货前要改脚本逻辑，避免固定 `KEEP_IDS`。

成功日志形态：

```text
执行完毕，共铺货 N 个商品
提交状态：成功
正在后台进行中
```

### 6. 晓风上货记录校验

不要只打开：

```text
#/move_list
```

它可能白屏或空内容。使用：

```text
#/move_list?type=moveList
#/iframe/move?type=moveList
```

脚本：

```powershell
python scripts\xf_check_move_variants.py
```

成功记录应包含：

- `铺货成功`
- `审核通过`
- 抖店商品 ID
- 完成时间

### 7. 抖店上架

晓风铺货成功后，抖店商品经常是“已下架”。需要在抖店商品管理页搜索抖店商品 ID 后上架。

先探测：

```powershell
python scripts\dy_probe_target_goods.py
```

再上架：

```powershell
python scripts\dy_relist_three.py
```

校验：

- “售卖中”列表能搜到商品 ID
- “已下架”列表搜不到该商品 ID
- 库存大于 0

库存为 0 的商品会失败，需换一个有库存商品或先补库存。

## 这次测试结论

已完成：

- 读懂 `D:\温涛\Videos\屏幕录制\铺货流程.mp4`
- 解决 VPN 后 Edge/晓风按钮点不动的核心问题
- 通过晓风内部路由完成铺货链路
- 晓风上货记录确认 3 个商品“铺货成功、审核通过”
- 抖店侧确认其中 2 个商品进入“售卖中”

遇到的限制：

- 原第 3 个商品库存为 0，抖店不允许上架
- 替换商品仍需逐个确认弹窗/平台约束，不能只看晓风成功

## 大量铺货建议

1. 每批先跑 3-10 个，确认模板、类目、库存、审核都正常。
2. 过滤规则：
   - 跳过库存为 0
   - 跳过侵权提示
   - 跳过类目/属性异常
   - 跳过价格明显异常
3. 每批输出：
   - 1688 商品 ID
   - 抖店商品 ID
   - 晓风铺货状态
   - 抖店审核状态
   - 抖店上架状态
4. 大批量上架前先给用户确认数量和关键词，不自动改价格。
