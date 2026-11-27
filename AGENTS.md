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
