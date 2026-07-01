# 抖音快速铺货 Skill (douyin-puhuo-fast)

抖音小店快速批量铺货自动化工具。从罗盘选品 → 晓风截流 → 1688以图搜款 → 抖店铺货，一条命令完成。

## 快速开始

```powershell
cd "$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator"

# 一键铺货 3 件雨伞
python scripts/puhuo.py --word 雨伞 --count 3

# 铺货 5 件T恤
python scripts/puhuo.py --word T恤 --count 5
```

## 环境要求

- Windows 11
- Python 3.10+ （Playwright）
- Microsoft Edge 浏览器（系统 Default profile 已登录）
- 晓风电商助手扩展 v30.3.3

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/puhuo.py` | **一键铺货**（推荐） |
| `scripts/xf_extract_products_100.py` | 从罗盘提取候选商品 |
| `scripts/xf_puhuo_publish_each.py` | 逐个商品闭环铺货 |
| `scripts/xf_check_move_variants.py` | 校验晓风上货记录 |
| `scripts/dy_probe_target_goods.py` | 查看抖店商品状态 |
| `scripts/dy_relist_three.py` | 抖店批量上架 |

## 目录结构

```
douyin-puhuo-fast/
├── SKILL.md                    # Skill 定义文件
├── README.md                   # 本文件
└── references/
    └── puhuo-workflow.md       # 详细工作流文档
```

脚本位于项目目录：`$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator\scripts\`

## License

MIT
