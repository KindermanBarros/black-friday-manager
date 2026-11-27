# AGENTS.md — Black Friday Manager

## Scope
Automated collectors publish verified Brazilian Nintendo Switch 2 offers. Do not change UI, schedules, configuration or other collector files during a price run.

## Collector ownership
- Collector 00 (runs at HH:00 Manaus): data/collector-00.json
- Collector 30 (runs at HH:30 Manaus): data/collector-30.json
- Each collector writes only its own file on main. Never overwrite the other collector or reset history.

## Research
Search reputable Brazilian retailers and marketplaces. Verify the actual listing, seller, condition (new), stock, game inclusion, payment method and direct HTTPS URL. Exclude used units, accessories, unavailable listings and unverified prices. Compare equivalent upfront payment conditions. Only apply coupons if verified and disclose conditions. Do not invent offers, game names, prices, availability, discounts or links. Do not include credentials or personal information; this repository is public.

## JSON contract
Each collector file is a JSON object with a runs array. Append one snapshot per execution:
```json
{
  "runs": [
    {
      "at": "2026-11-27T04:00:00-04:00",
      "offers": [
        {
          "store": "Example retailer",
          "price": 3000,
          "games": [],
          "url": "https://example.com/product",
          "inStock": true,
          "payment": "Pix",
          "coupon": "",
          "seller": "",
          "shipping": null,
          "installments": null
        }
      ]
    }
  ]
}
```
The example is illustrative only; never publish it as actual data. Use the actual collection timestamp (ISO 8601 with offset). Price is a positive numeric BRL amount, not formatted text. games is an array of actual included game names; empty for standalone. inStock is boolean true only when verified. Optional seller, shipping, installments may be omitted or null if unavailable. Never replace unknown data with guessed values.

## Write procedure
1. Read this AGENTS.md and the assigned collector file from main before writing.
2. Collect and validate offers, deduplicate equivalent listings, preserve all existing runs.
3. Append one snapshot, even when no offers were verified (offers: []). Use a stable timestamp for retries; if that timestamp already exists, do not duplicate it.
4. Update the assigned file using the current blob SHA. If it changed concurrently, re-fetch, merge the snapshot with the latest history and retry. Never force-push.
5. Commit with message: data: refresh collector XX YYYY-MM-DD HH:mm (Manaus).
6. Confirm the commit succeeded; report any access, validation or write failure honestly. Do not claim deployment success without verification. Do not write outside the assigned file.

## Recommendation
Find the cheapest verified standalone and cheapest verified bundle under comparable conditions. Prefer the bundle if its price is at most 110% of the standalone. If one category is absent, report that explicitly. The dashboard computes the recommendation itself.

## Notification
Every run must send the user the verified prices, recommendation, direct links, payment conditions, and changes from previous observations where available. Include whether GitHub was successfully updated. If research or GitHub fails, still notify the user and explain the limitation. Do not claim a successful publish if no commit was confirmed.

## Collection coverage and URL identity (mandatory; overrides conflicting older instructions)
- Target at least 20 distinct verified product URLs in stock per execution, including both standalone and bundles. Search across multiple reputable retailers and marketplaces; recheck existing URLs before expanding discovery. Equal prices at distinct URLs are valid; do not manufacture different prices. If fewer than 20 can be verified after broad search, report actual count and reasons; never pad with fabricated, inaccessible or duplicate offers.
- Read BOTH collector files for discovery and comparison, but write ONLY your own. Canonical identity is the HTTPS URL with lowercase host, leading www removed, fragment and trailing slash removed (except root), utm_* and gclid/fbclid/msclkid/aff_id/affiliate_id removed, remaining query parameters sorted and retained. Preserve meaningful SKU/seller/variant parameters. Resolve redirects to the actual product listing before canonicalization. Never merge distinct listings on price or title alone.
- For a previously known URL, use the same canonical identity and record the latest verified price instead of creating a duplicate catalog entry. Each run contains at most one observation per canonical URL; historical observations are retained to support the chart. Repeated unchanged prices still count as verified observations and refresh freshness. The dashboard folds both collectors into one catalog keyed by canonical URL; the most recent observation wins. If a known listing is confirmed unavailable, include inStock:false with last known positive price, not counted toward the 20 available offers. Do not mark an inaccessible or unchecked listing as confirmed unavailable. Expire old unverified listings in the dashboard.
- Report distinct verified in-stock count, new URLs, updated prices, unchanged prices, unavailable listings and any shortfall from 20. Commit only to GitHub main; Vercel Git integration handles builds and deployments automatically. No manual Vercel deployment. Notification must link directly to https://black-friday-manager-kindermanbarros-projects.vercel.app.

## Minimum coverage (mandatory)
Target 20 distinct verified in-stock listing URLs; minimum acceptance threshold is 10 (50%). Search Amazon Brasil, Shopee, Mercado Livre and KaBuM! on every run, then Magalu, Casas Bahia, Ponto, Carrefour, Fast Shop, Nintendo authorized retailers and other reputable stores as needed. Use multiple search terms (standalone, Mario Kart World, other genuine bundles), search engines and retailer search pages. If fewer than 10 verified listings are found, expand the search and retry alternative queries before finishing. Do not count duplicate canonical URLs, inaccessible listings or unverified prices. Equal prices on distinct URLs count as separate offers. If the minimum remains impossible, preserve verified results and explicitly mark the run as below minimum, report stores searched and blockers; never fabricate data. Record coupons and their verification status. The goal is 20 and the floor is 10, not a stopping rule at 10.

## PC category (separate contract; overrides Switch-specific rules for PC collectors)
PC collector 00 owns data/pc-collector-00.json; PC collector 30 owns data/pc-collector-30.json. Read both PC feeds, never write console feeds. Same runs array, timestamps, canonical URL identity, append-only observations, SHA conflict retries and GitHub main deployment procedure. Search Pichau, TerabyteShop, KaBuM!, Amazon Brasil, Mercado Livre, Shopee, Magalu and other trusted retailers every run. Target 20, minimum 10 eligible distinct links; expand search if short, never fabricate or relax requirements. Eligible: new complete preassembled desktop, Intel Core i7 or AMD Ryzen 7, dedicated desktop RTX 5060 or higher verified performance, >=16GB installed RAM, confirmed stock and verified upfront price <=6000 BRL. Exclude notebooks, upgrade kits, used PCs. Near misses with verified specs/price may be stored as candidates, eligible:false with explicit reason, never counted. PC offer fields: store,title,price (number),url,cpu (exact model string),gpu (exact model string),ramGB (number),ssdGB and vramGB (optional numbers),inStock (boolean true only if confirmed),stockStatus ('confirmed','uncertain','unavailable'),eligible (boolean),reason (string if not eligible),seller,payment,coupon,shipping,installments,motherboard,psu,warranty (optional verified values). Report coupon code, conditions and eligibility; unverified discounts cannot qualify for budget. Never include credentials or personal data. Report every run, count eligible URLs only toward goal, explain shortfall, provide direct dashboard link https://black-friday-manager-kindermanbarros-projects.vercel.app/#pcs. Commit only own PC feed on main; Vercel handles deployment.

## Android flagship category (overrides Switch/PC-specific criteria)
Phone collector owns data/phone-collector-00.json. Follow common canonical URL, timestamp, append-only history, SHA retry and GitHub main publishing rules. Target 20 verified distinct eligible in-stock URLs, minimum 10; never fabricate or relax criteria. Eligible: new genuine flagship Android phone strictly below BRL 4000 upfront, confirmed in stock. Search recent and prior-generation true flagship models: Motorola Edge Ultra and flagship Edge Pro, Galaxy S Ultra, Google Pixel Pro/Pro XL, RedMagic flagship, Xiaomi Ultra and flagship Pro, OnePlus flagship, ROG Phone, vivo X flagship, OPPO Find X flagship, Honor Magic Pro and equivalents. Exclude midrange, used, refurbished, accessories and misleading variants. Verify exact model, storage, RAM, chipset, seller, warranty, region, import taxes and network compatibility when available. Search official stores, Amazon Brasil, Mercado Livre, Shopee, KaBuM!, Magalu and trusted importers; compare total known landed cost, disclose unknown taxes or freight and do not mark conditional prices as eligible. Phone fields: store,title,brand,model,price,url,inStock,eligible,reason (if ineligible), optional ramGB,storageGB,chipset,region,warranty,coupon,payment,seller,shipping,installments. Above-budget or uncertain candidates may be saved with eligible:false and explicit reason. Coupons must include code, discount and conditions, distinguish unverified. Commit exclusively to own feed. Report count, shortfall and SHA, link https://black-friday-manager-kindermanbarros-projects.vercel.app/#android. No manual deploy.
