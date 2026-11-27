#!/usr/bin/env python3
"""Deep on-page / semantic / structured-data audit (complements audit_seo.py).
Usage: python3 scripts/audit_deep.py [site_root]   Exit 1 on hard failures; WARN lines are advisory."""
import re, glob, json, os, sys, collections, itertools
import xml.etree.ElementTree as ET
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
NOINDEX = {"/thank-you/", "/404.html"}
pages = {}
for p in glob.glob(ROOT + "/**/index.html", recursive=True) + [ROOT + "/404.html"]:
    rel = os.path.relpath(p, ROOT)
    if not rel.startswith("scripts"):
        pages["/" + rel.replace("index.html", "")] = open(p, encoding="utf8").read()
fail, warn = collections.defaultdict(list), collections.defaultdict(list)
PROJECT = re.compile(os.environ.get("PROJECT_RE", r"Ceratec Central Park|Ceratec"))   # edit per project


def text(h):
    m = re.search(r"<main.*?</main>", h, re.S)
    m = m.group(0) if m else h
    m = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", m, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m)).strip()


T = {u: text(h) for u, h in pages.items()}
titles = {u: re.sub(r"\s*\|.*$", "", re.search(r"<title>(.*?)</title>", h, re.S).group(1)) for u, h in pages.items()}
generic = re.compile(r"^(click here|read more|here|more|link|this page)$", re.I)
for u, h in pages.items():
    lv = [int(x) for x in re.findall(r"<h([1-6])[ >]", h)]
    for a, b in zip(lv, lv[1:]):
        if b - a > 1:
            fail["heading level skipped"].append(u)
            break
    ids = re.findall(r'\sid="([^"]+)"', h)
    dup = [i for i, c in collections.Counter(ids).items() if c > 1]
    if dup:
        fail["duplicate ids"].append((u, dup[:2]))
    for tag in re.findall(r"<a [^>]*target=\"_blank\"[^>]*>", h):
        if "noopener" not in tag:
            fail["target=_blank without noopener"].append(u)
            break
    for href, txt in re.findall(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', h, re.S):
        t = re.sub(r"<[^>]+>", "", txt).strip()
        if generic.match(t):
            warn["generic anchor text"].append((u, t))
    if len(u) > 80 or u != u.lower().replace("%", "%") and "404" not in u:
        warn["long/mixed-case url"].append(u)
    if u not in NOINDEX and not PROJECT.search(" ".join(T[u].split()[:150])):
        warn["project name not in first 150 words"].append(u)
    if u not in NOINDEX and u.count("/") >= 4 and len(T[u].split()) < 450:
        warn["thin page (<450 words incl. nav)"].append((u, len(T[u].split())))
# cannibalisation: near-identical titles / H1s
tok = {u: set(re.findall(r"[a-z0-9.]+", t.lower())) - {"in", "flats", "pune", "from", "the", "a", "and", "of", "bhk"} for u, t in titles.items()}
for a, b in itertools.combinations([u for u in pages if u not in NOINDEX], 2):
    j = len(tok[a] & tok[b]) / max(1, len(tok[a] | tok[b]))
    if j >= 0.85 and titles[a] != titles[b]:
        warn["near-duplicate titles"].append((a, b))
# body similarity across all pages
def sh(t):
    w = t.split()
    return {" ".join(w[i:i + 6]) for i in range(len(w) - 5)}
S = {u: sh(T[u]) for u in pages if u not in NOINDEX}
worst = []
for a, b in itertools.combinations(S, 2):
    if S[a] and S[b]:
        worst.append((round(len(S[a] & S[b]) / len(S[a] | S[b]), 2), a, b))
worst.sort(reverse=True)
for j, a, b in worst[:50]:
    if j > 0.60:
        fail["body overlap > 0.60"].append((a, b, j))
# schema completeness
need = {"Product": ["name", "offers"], "Offer": ["price", "priceCurrency"], "AggregateOffer": ["lowPrice", "priceCurrency"], "Organization": ["name", "url"],
        "BlogPosting": ["headline", "datePublished", "author", "publisher"], "FAQPage": ["mainEntity"], "BreadcrumbList": ["itemListElement"], "WebSite": ["name", "url"],
        "ApartmentComplex": ["name", "address"], "Apartment": ["name"], "ImageObject": ["url"], "Place": [], "RealEstateListing": ["name", "url"]}
def walk(o, fn):
    if isinstance(o, dict):
        fn(o)
        for v in o.values():
            walk(v, fn)
    elif isinstance(o, list):
        for v in o:
            walk(v, fn)
for u, h in pages.items():
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        j = json.loads(b)
        def chk(o):
            ty = o.get("@type")
            for t in (ty if isinstance(ty, list) else [ty]):
                for k in need.get(t, []):
                    if k not in o and "@id" not in o:
                        fail["schema missing property"].append((u, t, k))
        walk(j, chk)
# sitemap xml
try:
    tree = ET.parse(ROOT + "/sitemap.xml")
    n = len(tree.getroot())
    if n > 50000:
        fail["sitemap > 50000 urls"].append(n)
except Exception as e:
    fail["sitemap xml invalid"].append(str(e))
# files and policies
for f, why in (("llms.txt", "llms.txt (AI search summary)"), ("about/index.html", "About page (E-E-A-T)"), ("images/og-image.jpg", "OG image"), (("manifest.webmanifest" if os.path.exists(ROOT + "/manifest.webmanifest") else "site.webmanifest"), "manifest"), ("favicon.ico", "favicon"), ("apple-touch-icon.png", "apple icon")):
    if not os.path.exists(os.path.join(ROOT, f)):
        fail["missing file"].append(why)
ht = open(ROOT + "/.htaccess").read()
for k in ("Strict-Transport-Security", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "ErrorDocument 404", "Options -Indexes"):
    if k not in ht:
        fail["htaccess missing"].append(k)
if "<noscript" not in pages["/"]:
    fail["home has no noscript fallback"].append("/")
try:
    from PIL import Image
    if Image.open(ROOT + "/images/og-image.jpg").size != (1200, 630):
        fail["og-image size"].append(Image.open(ROOT + "/images/og-image.jpg").size)
except Exception:
    pass
print(f"{len(pages)} pages; worst body overlap {worst[0] if worst else None}")
for k, v in sorted(warn.items()):
    print(f"WARN {k}: {len(v)} e.g. {v[:2]}")
if not fail:
    print("DEEP AUDIT PASSED: 0 hard failures")
    sys.exit(0)
for k, v in sorted(fail.items()):
    print(f"FAIL {k}: {len(v)} e.g. {v[:3]}")
sys.exit(1)
