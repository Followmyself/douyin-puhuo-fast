---
name: douyin-puhuo-fast
description: Douyin (TikTok Shop) rapid product publishing — from Douyin Compass product selection → Xiaofeng interception → 1688 image-based sourcing → single-store publish → record verification. Use when the user mentions publishing products, sourcing from 1688, or batch listing to Douyin Shop.
---

# Douyin Rapid Product Publishing Skill (v2)

## TL;DR

Select products from Douyin Compass search terms → Xiaofeng 1688 image-based sourcing → single-store publish, all in one command.

## Prerequisites

- Windows 11 + Python 3.10+
- Microsoft Edge (system Default profile logged into Douyin Shop / Compass / Xiaofeng)
- Xiaofeng E-commerce Assistant extension (`gcfohjiejngbnepafbldkbmjgeclehdn`)
- Playwright: `pip install playwright`

## Quick Start

### One-command publishing

```powershell
cd "$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator"
python scripts/puhuo.py --word <search_term> --count <number>
```

**Examples**:

```powershell
# Publish 3 umbrella products
python scripts/puhuo.py --word umbrella --count 3

# Publish 5 T-shirt products with longer wait for slow network
python scripts/puhuo.py --word "t-shirt" --count 5 --wait-scale 3.0
```

### Step-by-step (for debugging)

```powershell
# 1. Extract candidate products from Compass
python scripts/xf_extract_products_100.py --word umbrella --target 120

# 2. Publish one by one (single-product closed loop)
python scripts/xf_puhuo_publish_each.py --start 0 --limit 3 --target 3 --wait-scale 2.0
```

## Core Principles

1. **Sort by exposure**: Candidate products are sorted by "product exposure users" from high to low
2. **Single-product closed loop**: Each product independently completes: find 1688 source → publish to Douyin → open preview → single-store publish
3. **1688 deduplication**: The same 1688 source ID is never published twice (unless `--allow-duplicate-goods` is set)
4. **No auto-listing**: Products are in "delisted" status after publishing; manual listing is required
5. **No batch preview**: Xiaofeng's preview list is unstable — never batch-add then batch-publish

## Workflow

```
Compass search term → Hot products under term (sorted by exposure) → Xiaofeng interception
    → 1688 image-based sourcing → Select 1688 source (dedup, exclude brand/infringement risks)
    → Publish to Douyin → Fetch product data → Open preview list → Single-store publish
    → Submit success (under review / delisted)
```

## Popup Handling

| Popup | Action |
|-------|--------|
| "Unsubmitted publishing data" | Click "Continue publishing" |
| Size/spec warning | Click "Keep product and continue" |
| Infringement risk warning | Click "Keep product and continue" |
| Blank page | Re-open Xiaofeng page with timestamped URL |

## Post-Publish Verification

```powershell
# Verify Xiaofeng publishing records
python scripts/xf_check_move_variants.py

# Check Douyin Shop product status
python scripts/dy_probe_target_goods.py
```

## Report Interpretation

Report file: `reports/xf_puhuo_publish_each_<start>_<limit>.json`

Common statuses:

| Status | Meaning |
|--------|---------|
| `published_clicked` + non-empty `submitted_ids` | **Publish successful** |
| `no_candidate` | No suitable 1688 source found |
| `duplicate_candidate` | All sources already published (dedup blocked) |
| `not_enough_items` | Preview list empty — 1688 source has no distributable data |
| `all_sources_failed` | All attempted sources failed to fetch product data |
| `unknown_after_click` | Did not enter preview state after clicking publish |

## Known Bug Fix (v2)

### `fetch_failed` False Positive

**Root cause**: The code checked `"失败" (failed) in text` to detect fetch failures, but the summary line always contains `"成功 15, 失败 5"` (15 succeeded, 5 failed), causing **every product to be falsely flagged as failed**.

**Fix**: Changed to only check whether the currently selected 1688 ID's specific line contains failure keywords, not the global summary.

### "Open Preview List" Button Detection

**Root cause**: The modal search required a single div to contain both `"获取商品数据"` and `"打开铺货预览列表"`, but they may appear in separate elements.

**Fix**: Three-tier button search strategy: (1) scope within "fetch data" modal → (2) document-wide search → (3) any clickable element containing the text. Added retry loop with up to 5 attempts.

## Project Directory

All scripts are located at: `$env:USERPROFILE\desktop\vscode\claude-code-douyin-operator\scripts\`

## Disabled (Do Not Use)

- Do not use `xf_puhuo_fast_runner.py`
- Do not use `xf_to_preview_batch.py` for batch preview
- Do not use `xf_publish_preview_batch.py` for batch publishing
- Do not expand candidate range just to inflate success count
- Do not publish the same 1688 source ID twice
