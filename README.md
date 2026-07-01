# Douyin Rapid Product Publishing Skill (douyin-puhuo-fast)

Automated rapid batch product publishing for Douyin (TikTok) Shop. From Compass product selection → Xiaofeng interception → 1688 image-based sourcing → Douyin Shop publishing — all in one command.

## Quick Start

```powershell
cd "$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator"

# Publish 3 umbrella products
python scripts/puhuo.py --word umbrella --count 3

# Publish 5 T-shirt products
python scripts/puhuo.py --word "t-shirt" --count 5
```

## Requirements

- Windows 11
- Python 3.10+ (with Playwright)
- Microsoft Edge browser (system Default profile, logged in)
- Xiaofeng E-commerce Assistant extension v30.3.3

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/puhuo.py` | **One-command publishing** (recommended) |
| `scripts/xf_extract_products_100.py` | Extract candidate products from Compass |
| `scripts/xf_puhuo_publish_each.py` | Single-product closed-loop publishing |
| `scripts/xf_check_move_variants.py` | Verify Xiaofeng publishing records |
| `scripts/dy_probe_target_goods.py` | Check Douyin Shop product status |
| `scripts/dy_relist_three.py` | Batch listing on Douyin Shop |

## Directory Structure

```
douyin-puhuo-fast/
├── SKILL.md                    # Skill definition (core document)
├── README.md                   # This file
└── references/
    └── puhuo-workflow.md       # Detailed workflow documentation
```

Scripts are located in the project directory: `$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator\scripts\`

## Key Principles

1. Products are sorted by exposure users (high to low) before publishing
2. Single-product closed loop: one product at a time, end to end
3. 1688 source IDs are deduplicated across runs
4. Products are NOT auto-listed after publishing (manual listing required)
5. No batch preview or batch publish — Xiaofeng preview list is unstable

## License

MIT
