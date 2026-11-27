"""Free discovery and conservative verification. No paid API or credentials."""
import concurrent.futures as cf
import datetime as dt
import json
import math
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, quote, quote_plus, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
FEEDS = ("collector-00", "collector-30", "pc-collector-00", "pc-collector-30", "phone-collector-00")
STORES = {
    "Amazon Brasil": ("amazon.com.br", "https://www.amazon.com.br/s?k={q}"),
    "Shopee": ("shopee.com.br", "https://shopee.com.br/search?keyword={q}"),
    "Mercado Livre": ("mercadolivre.com.br", "https://lista.mercadolivre.com.br/{slug}"),
    "KaBuM!": ("kabum.com.br", "https://www.kabum.com.br/busca/{slug}"),
    "Magalu": ("magazineluiza.com.br", "https://www.magazineluiza.com.br/busca/{slug}/"),
    "Casas Bahia": ("casasbahia.com.br", "https://www.casasbahia.com.br/{slug}/b"),
    "Ponto": ("pontofrio.com.br", "https://www.pontofrio.com.br/{slug}/b"),
    "Carrefour": ("carrefour.com.br", "https://www.carrefour.com.br/{q}?_q={q}&map=ft"),
    "Fast Shop": ("fastshop.com.br", "https://www.fastshop.com.br/web/s/{q}"),
    "Pichau": ("pichau.com.br", "https://www.pichau.com.br/search?q={q}"),
    "TerabyteShop": ("terabyteshop.com.br", "https://www.terabyteshop.com.br/busca?str={q}"),
    "Nova Era Games": ("lojanovaera.com", "https://www.lojanovaera.com/busca?q={q}"),
    "Motorola": ("motorola.com.br", "https://www.motorola.com.br/{q}?_q={q}&map=ft"),
    "Samsung": ("samsung.com", "https://www.samsung.com/br/search/?searchvalue={q}"),
}
MARKET = {"Amazon Brasil", "Shopee", "Mercado Livre", "Magalu", "KaBuM!", "Casas Bahia", "Ponto", "Carrefour"}
EXTRAS = {
    "switch": ("Nova Era Games",),
    "pc": ("Pichau", "TerabyteShop"),
    "phone": ("Motorola", "Samsung"),
}
CORE = tuple(STORES)[:9]
TERMS = {
    "switch": ("nintendo switch 2 console", "nintendo switch 2 mario kart world", "nintendo switch 2 bundle", "console switch 2 256gb"),
    "pc": ("pc gamer ryzen 7 rtx 5060 16gb", "pc gamer i7 rtx 5060 16gb", "computador gamer ryzen 7 rtx 5070", "pc gamer i7 rtx 4060 ti 16gb"),
    "phone": ("galaxy s25 ultra", "motorola edge 50 ultra", "google pixel 9 pro", "redmagic 10 pro", "xiaomi 15 ultra", "oneplus 13"),
}
GAMES = ("Mario Kart World", "Donkey Kong Bananza", "EA Sports FC 26", "EA Sports FC 27", "Pokémon Legends: Z-A", "Super Mario Bros. Wonder", "Super Mario Galaxy 1 + 2", "Metroid Prime 4: Beyond")
PHONE_PATTERNS = (
    ("Samsung", r"galaxy s(?:2[2-6]) ultra"),
    ("Motorola", r"(?:motorola )?edge (?:(?:30|50|60|70) ultra|(?:30|40) pro)"),
    ("Google", r"pixel (?:[6-9]|10|11) pro(?: xl)?"),
    ("REDMAGIC", r"red ?magic (?:[7-9]|10|11)(?:s)?(?: pro(?: plus)?)?"),
    ("Xiaomi", r"xiaomi (?:1[2-7]) (?:ultra|pro)"),
    ("OnePlus", r"oneplus (?:1[0-5])(?: pro)?"),
    ("ASUS", r"rog phone (?:[6-9]|10)(?: pro)?"),
    ("vivo", r"vivo x(?:80|90|100|200|300) (?:pro|ultra)"),
    ("OPPO", r"oppo find x(?:[5-9]|10) (?:pro|ultra)"),
    ("Honor", r"honor magic ?(?:[4-9]|10) pro"),
)

def norm(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value)).lower() if not unicodedata.combining(c))

def canonical(url):
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError("invalid HTTPS URL")
    host = p.hostname.lower().removeprefix("www.")
    query = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                   if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid", "msclkid", "aff_id", "affiliate_id"})
    return urlunsplit(("https", host, p.path.rstrip("/") or "/", urlencode(query), ""))

def store_for(url):
    try:
        h = urlsplit(canonical(url)).hostname
        return next((s for s, (d, _) in STORES.items() if h == d or h.endswith("." + d)), None)
    except (ValueError, TypeError):
        return None

def fetch(url):
    if not store_for(url):
        raise ValueError("unapproved retailer")
    for _ in range(4):
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; BlackFridayManager/1.0)", "Accept-Language": "pt-BR,pt;q=0.9"}, timeout=(5, 12), allow_redirects=False, stream=True)
        with r:
            if r.is_redirect:
                url = urljoin(url, r.headers.get("Location", ""))
                if not store_for(url):
                    raise ValueError("redirect outside approved retailers")
                continue
            r.raise_for_status()
            data = bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data) > 6_000_000:
                    raise ValueError("response too large")
            return r.url, BeautifulSoup(bytes(data), "html.parser")
    raise ValueError("too many redirects")

def category(feed):
    return "pc" if feed.startswith("pc-") else "phone" if feed.startswith("phone-") else "switch"

def number(value):
    try:
        s = str(value).strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        n = float(re.sub(r"[^0-9.]", "", s)) if not s.startswith("-") else -1
        return n if math.isfinite(n) and n > 0 else None
    except (ValueError, TypeError):
        return None

def nodes(obj):
    if isinstance(obj, list):
        for v in obj:
            yield from nodes(v)
    elif isinstance(obj, dict):
        yield obj
        if "@graph" in obj:
            yield from nodes(obj["@graph"])
        if "mainEntity" in obj:
            yield from nodes(obj["mainEntity"])

def types(obj):
    t = obj.get("@type", [])
    return t if isinstance(t, list) else [t]

def tail(v):
    return str(v or "").rstrip("/").split("/")[-1].split(":")[-1]

def products(soup):
    out = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            out.extend(p for p in nodes(json.loads(script.get_text())) if "Product" in types(p))
        except (ValueError, TypeError):
            continue
    return out

def classify(cat, title, desc, offer):
    t, d = norm(title), norm(desc)
    text = t + " " + d
    if re.search(r"\b(usado|seminovo|recondicionado|refurbished|open box|vitrine)\b", t):
        return None
    if cat == "switch":
        if not re.search(r"\b(?:nintendo )?switch\s*2\b", t) or not re.search(r"\b(console|nintendo switch 2)\b", t):
            return None
        if re.search(r"\b(capa|case|pelicula|protetor|suporte|carregador|controle|controlador|joystick|acessorio|dock|cartao|bolsa|jogo para|game para)\b", t) and (not "console" in t or re.search(r"\b(?:capa|case|pelicula|protetor|suporte|carregador|controle|controlador|joystick|acessorio|dock|cartao|bolsa)\b.*\b(?:para|compativel com)\b.*\b(?:console|switch)\b", t)):
            return None
        games = [g for g in GAMES if norm(g) in t]
        if not games and re.search(r"\b(bundle|pacote|kit|com jogo|game incluso|jogo incluso)\b", t):
            return None
        if games and not re.search(r"\b(console|bundle|pacote|kit|com|inclui)\b", t):
            return None
        return {**offer, "games": games}
    if cat == "pc":
        if not re.search(r"\b(pc gamer|computador gamer|desktop|microcomputador|computador)\b", t) or re.search(r"\b(notebook|laptop|kit upgrade|placa de video|barebone|gabinete vazio)\b", t):
            return None
        cpu = re.search(r"\b(?:intel\s+)?(?:core\s+)?i7[\s-]*\d{4,5}[a-z]{0,3}\b|\b(?:amd\s+)?ryzen\s*7\s+\d{4}[a-z0-9]*\b", text)
        gpu = re.search(r"\brtx\s*(?:5060(?:\s*ti)?|5070(?:\s*ti)?|5080|5090|4070(?:\s*(?:ti|super))*|4080(?:\s*super)?|4090|3080(?:\s*ti)?|3090(?:\s*ti)?)\b", text)
        ram = re.search(r"\b(\d{2,3})\s*gb\s*(?:de\s*)?(?:ram|ddr[345])\b|\b(?:ram|memoria ram|ddr[345])\s*[: -]*\s*(\d{2,3})\s*gb\b", text)
        if not (cpu and gpu and ram):
            return None
        gb = int(ram.group(1) or ram.group(2))
        if gb < 16 or offer["price"] > 6000:
            return None
        return {**offer, "title": title, "cpu": cpu.group().upper(), "gpu": gpu.group().upper(), "ramGB": gb, "eligible": True, "stockStatus": "confirmed"}
    if offer["price"] >= 4000 or re.search(r"\b(capa|case|pelicula|display|tela de reposicao|importado|taxas a parte)\b", t):
        return None
    if re.search(r"\b(lite|fe|neo|fusion|ace|nord|r)\b", t):
        return None
    for brand, pattern in PHONE_PATTERNS:
        m = re.search(pattern, t)
        if m:
            return {**offer, "title": title, "brand": brand, "model": m.group(), "eligible": True}
    return None

def verify(url, cat, known):
    store = store_for(url)
    final, soup = fetch(url)
    identity = canonical(final)
    if store_for(final) != store:
        return None, "retailer changed after redirect"
    ps = products(soup)
    if len(ps) != 1:
        matches = []
        for p in ps:
            try:
                if p.get("url") and canonical(urljoin(final, p["url"])) == identity:
                    matches.append(p)
            except (TypeError, ValueError):
                pass
        ps = matches
    if len(ps) != 1:
        return None, "no unique product structured data"
    p = ps[0]
    title = str(p.get("name") or "").strip()
    desc = BeautifulSoup(str(p.get("description") or ""), "html.parser").get_text(" ", strip=True)
    offers = p.get("offers", [])
    offers = offers if isinstance(offers, list) else [offers]
    if len(offers) != 1 or not isinstance(offers[0], dict):
        return None, "ambiguous offer"
    o = offers[0]
    if "AggregateOffer" in types(o):
        return None, "aggregate price does not identify seller"
    if o.get("url"):
        try:
            if canonical(urljoin(final, o["url"])) != identity:
                return None, "offer URL differs from listing"
        except (ValueError, TypeError):
            return None, "invalid offer URL"
    avail = tail(o.get("availability"))
    if avail in {"OutOfStock", "SoldOut", "Discontinued"} and identity in known:
        return {**known[identity], "url": identity, "inStock": False, **({"eligible": False, "reason": "indisponibilidade confirmada"} if cat != "switch" else {}), **({"stockStatus": "unavailable"} if cat == "pc" else {})}, None
    if avail not in {"InStock", "LimitedAvailability"}:
        return None, "stock not positively confirmed"
    condition = tail(o.get("itemCondition") or p.get("itemCondition"))
    if condition != "NewCondition" and not (not condition and re.search(r"\b(novo|lacrado|new)\b", norm(title + " " + desc))):
        return None, "new condition not confirmed"
    if str(o.get("priceCurrency") or "").upper() != "BRL":
        return None, "currency not confirmed"
    price = number(o.get("price"))
    if not price:
        return None, "no positive full offer price"
    seller = o.get("seller")
    seller = seller.get("name") if isinstance(seller, dict) else seller
    if not isinstance(seller, str) or not seller.strip():
        return None, "seller not confirmed"
    offer = {"store": store, "price": price, "url": identity, "inStock": True, "payment": "Preço integral anunciado (forma de pagamento não especificada)", "coupon": "", "couponStatus": "not_verified", "seller": seller.strip(), "shipping": None, "installments": None}
    # SmartTracker MIT selectors: use as corroboration, never infer stock or replace structured price.
    selectors = {"Amazon Brasil": ["span.a-price > span.a-offscreen", "#priceblock_ourprice", "#priceblock_dealprice"], "KaBuM!": ["span.finalPrice", "h4.finalPrice"]}
    for sel in selectors.get(store, []):
        tag = soup.select_one(sel)
        if tag and "R$" in tag.get_text():
            displayed = number(tag.get_text(strip=True))
            if displayed and abs(displayed - price) > 0.01:
                return None, "displayed price and structured price disagree"
            break
    result = classify(cat, title, desc, offer)
    return (result, None) if result else (None, "category or budget not confirmed")

def discovery(store, query):
    _, pattern = STORES[store]
    url = pattern.format(q=quote_plus(query), slug=quote(query.replace(" ", "-")))
    final, soup = fetch(url)
    links = {}
    for a in soup.select("a[href]"):
        href = urljoin(final, a["href"])
        if store_for(href) != store:
            continue
        try:
            p = urlsplit(href)
            text = norm(a.get_text(" ", strip=True) + " " + p.path)
            if re.search(r"/(?:dp/|gp/product/|produto/|product/|p/|ip/|MLB-?\d+)|-i\.\d+\.\d+|/p$", p.path, re.I) or (len(p.path.split("/")) > 2 and re.search(r"switch.?2|ryzen|rtx|galaxy|pixel|edge|redmagic", text)):
                links[canonical(href)] = href
        except (ValueError, TypeError):
            continue
        if len(links) >= 20:
            break
    return list(links.values())


def radar_links(cat):
    """Use existing public Radar Ofertas output only to discover URLs, not prices.
    No upstream code copied. Promotion links are not verified listings."""
    feed = "https://raw.githubusercontent.com/gglucche/radar-ofertas/main/docs/dados.json"
    response = requests.get(feed, timeout=(5, 12), allow_redirects=False)
    response.raise_for_status()
    if len(response.content) > 12_000_000:
        raise ValueError("Radar feed too large")
    rows = response.json().get("ofertas", [])
    result = []
    promo_hosts = {"promobit.com.br", "www.promobit.com.br", "gatry.com", "www.gatry.com", "pelando.com.br", "www.pelando.com.br"}
    for row in rows:
        title = norm(row.get("titulo", ""))
        relevant = (re.search(r"switch\s*2", title) if cat == "switch" else re.search(r"pc gamer|computador gamer|desktop", title) if cat == "pc" else any(re.search(pattern, title) for _, pattern in PHONE_PATTERNS))
        if not relevant:
            continue
        url = row.get("url")
        if not isinstance(url, str):
            continue
        if store_for(url):
            result.append(url)
        else:
            p = urlsplit(url)
            if p.scheme != "https" or p.hostname not in promo_hosts or p.username or p.password:
                continue
            try:
                page = requests.get(url, timeout=(5, 8), allow_redirects=False)
                if page.status_code != 200 or len(page.content) > 4_000_000:
                    continue
                soup = BeautifulSoup(page.content, "html.parser")
                for a in soup.select("a[href]"):
                    dest = urljoin(url, a["href"])
                    if store_for(dest):
                        result.append(dest)
            except requests.RequestException:
                continue
        if len(result) >= 30:
            break
    return result[:30]

def history(cat):
    known = {}
    observations = []
    for feed in FEEDS:
        if category(feed) != cat:
            continue
        doc = json.loads((ROOT / "data" / (feed + ".json")).read_text())
        for r in doc["runs"]:
            for o in r["offers"]:
                observations.append((r["at"], o))
    for _, o in sorted(observations, key=lambda pair: pair[0]):
        try:
            known[canonical(o["url"])] = o
        except (KeyError, TypeError, ValueError):
            continue
    return known

def collect(feed, at, output):
    cat = category(feed)
    known = history(cat)
    stores = CORE + EXTRAS[cat]
    attempted, blockers, found, seen = set(), set(), {}, set()
    started = time.monotonic()
    def check(url):
        try:
            return verify(url, cat, known)
        except Exception as exc:
            return None, type(exc).__name__ + (f" HTTP {exc.response.status_code}" if isinstance(exc, requests.HTTPError) and exc.response is not None else "")
    def run_checks(urls):
        batch = []
        for url in urls:
            s = store_for(url)
            if not s or s not in stores:
                continue
            k = canonical(url)
            if k not in seen:
                seen.add(k)
                attempted.add(s)
                batch.append((s, url))
        with cf.ThreadPoolExecutor(max_workers=8) as pool:
            pending = {pool.submit(check, u): s for s, u in batch}
            for f in cf.as_completed(pending):
                o, err = f.result()
                if o:
                    found[o["url"]] = o
                if err:
                    blockers.add(pending[f] + ": " + err)
    def count():
        return sum(o["inStock"] and o.get("eligible", True) for o in found.values())
    def checkpoint(finished=False):
        n = count()
        reasons = sorted(blockers | (set() if finished else {"research checkpoint: collection may have been interrupted"}))
        result = {"at": at, "offers": sorted(found.values(), key=lambda o: (not o["inStock"], o["price"], o["url"])), "metadata": {"status": "complete" if n >= 10 else "below_minimum", "eligibleCount": n, "target": 20, "minimum": 10, "storesSearched": sorted(attempted), "blockers": reasons, "targetMet": n >= 20, "newLinks": sum(o["url"] not in known for o in found.values() if o["inStock"]), "changedPrices": sum(o["url"] in known and o["price"] != known[o["url"]]["price"] for o in found.values() if o["inStock"]), "unchangedPrices": sum(o["url"] in known and o["price"] == known[o["url"]]["price"] for o in found.values() if o["inStock"])}}
        path = Path(output)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)
        return result
    # Search all required stores even when known links already meet the target.
    checkpoint()
    run_checks(list(known)[-32:])
    checkpoint()
    # Every required retailer is searched; alternate queries if target not met.
    for q in TERMS[cat]:
        if q != TERMS[cat][0] and time.monotonic() - started > 240:
            blockers.add("research time budget reached")
            break
        candidates = {}
        with cf.ThreadPoolExecutor(max_workers=8) as pool:
            pending = {}
            for s in stores:
                attempted.add(s)
                pending[pool.submit(discovery, s, q)] = s
            for f in cf.as_completed(pending):
                s = pending[f]
                try:
                    candidates[s] = f.result()
                    if not candidates[s]:
                        blockers.add(s + ": no direct product links discovered")
                except Exception as exc:
                    blockers.add(s + ": search " + type(exc).__name__)
        # Round-robin prevents one retailer consuming all validation slots.
        batch = [v[i] for i in range(8) for v in candidates.values() if i < len(v)]
        run_checks(batch[:48])
        checkpoint()
        if count() >= 20:
            break
    if count() < 20 and time.monotonic() - started < 330:
        try:
            links = radar_links(cat)
            if not links:
                blockers.add("Radar Ofertas: no direct retailer links extracted")
            run_checks(links)
        except Exception as exc:
            blockers.add("Radar Ofertas: " + type(exc).__name__)
        checkpoint()
    return checkpoint(finished=True)

if __name__ == "__main__":
    feed, at, output = sys.argv[1:]
    if feed not in FEEDS:
        raise SystemExit("invalid collector")
    collect(feed, at, output)
