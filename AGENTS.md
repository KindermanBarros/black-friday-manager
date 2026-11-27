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
