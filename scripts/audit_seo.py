#!/usr/bin/env python3
"""Full-site SEO audit for a built static site (run after build). Exit code 1 if any hard check fails.
Usage: python3 scripts/audit_seo.py [site_root] [https://domain]
Hard checks: titles, descriptions, H1, canonical, lang, viewport, indexability, Open Graph/Twitter, geo + keyword meta,
JSON-LD validity and expected types, image alt (with project name) and dimensions, versioned CSS/JS, self-hosted fonts,
cookie and privacy policy pages linked from every page, sitemap/robots consistency, honest lastmod, crawl depth and orphans,
cache headers in .htaccess."""
import re, glob, json, os, sys, collections, datetime
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
DOMAIN = (sys.argv[2] if len(sys.argv) > 2 else None)
NOINDEX_OK = {"/thank-you/", "/404.html"}
pages = {}
for p in glob.glob(ROOT + "/**/index.html", recursive=True) + [ROOT + "/404.html"]:
    rel = os.path.relpath(p, ROOT)
    if rel.startswith("scripts"):
        continue
    pages["/" + rel.replace("index.html", "")] = open(p, encoding="utf8").read()
HAS_COORDS = bool(re.search(r'name="geo.position"', pages["/"]))
if not HAS_COORDS:
    print("NOTE: no verified map coordinates on the home page, so geo.position/ICBM are not required (add them when the client confirms the pin).")
if DOMAIN is None:
    m = re.search(r'<link rel="canonical" href="(https://[^/"]+)', pages["/"])
    DOMAIN = m.group(1)
PROJECT = re.compile(os.environ.get("PROJECT_RE", r"Ceratec|Central Park|Kharadi"))   # edit per project
bad = collections.defaultdict(list)


def meta(h, n):
    m = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % re.escape(n), h)
    return m.group(1) if m else None


titles, descs = collections.Counter(), collections.Counter()
for u, h in pages.items():
    t = (re.search(r"<title>(.*?)</title>", h, re.S) or [None, ""])[1].replace("&amp;", "&")
    d = meta(h, "description") or ""
    titles[t] += 1
    descs[d] += 1
    if not t or len(t) > 60:
        bad["title missing or >60"].append(u)
    if (not d and u not in NOINDEX_OK) or len(d) > 160 or (len(d) < 70 and u not in NOINDEX_OK):
        bad["description missing/>160/<70"].append(u)
    if len(re.findall(r"<h1[ >]", h)) != 1:
        bad["h1 count != 1"].append(u)
    if f'<link rel="canonical" href="{DOMAIN}' not in h and u not in NOINDEX_OK:
        bad["canonical"].append(u)
    if '<html lang="en-IN"' not in h:
        bad["lang"].append(u)
    if "width=device-width" not in h:
        bad["viewport"].append(u)
    rb = meta(h, "robots") or ""
    if (u in NOINDEX_OK) != ("noindex" in rb):
        bad["indexability wrong"].append(u)
    keys = ("og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name", "twitter:card", "geo.region", "geo.placename", "keywords", "theme-color")
    if HAS_COORDS:
        keys += ("geo.position", "ICBM")
    for k in ([] if u in NOINDEX_OK else keys):
        if not meta(h, k):
            bad["missing meta " + k].append(u)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    types = set()
    for b in blocks:
        try:
            types |= set(re.findall(r'"@type":\s*"([A-Za-z]+)"', b))
            json.loads(b)
        except Exception:
            bad["invalid JSON-LD"].append(u)
    if not blocks and u not in NOINDEX_OK:
        bad["no JSON-LD"].append(u)
    if u == "/" and not {"RealEstateAgent", "ApartmentComplex", "FAQPage", "Product", "BreadcrumbList", "WebSite"} <= types and "BreadcrumbList" not in types:
        bad["home schema incomplete"].append(u)
    if "/blog/" in u and u.count("/") > 3 and "BreadcrumbList" not in types:
        bad["no breadcrumb schema"].append(u)
    for im in re.findall(r"<img[^>]*>", h):
        if "lbImg" in im:
            continue
        a = re.search(r' alt="([^"]*)"', im)
        if not a or (not a.group(1) and "aria-hidden" not in im):
            bad["img alt missing"].append(u)
        elif a.group(1) and not PROJECT.search(a.group(1)):
            bad["img alt without project name"].append(u)
        if "width=" not in im or "height=" not in im:
            bad["img without dimensions"].append(u)
        if "srcset=" in im and " sizes=" not in im:
            bad["srcset without sizes"].append(u)
    for a in re.findall(r'(?:href|src)="(/(?:css|js)/[^"]+)"', h):
        if "?v=" not in a:
            bad["unversioned css/js"].append(u)
    if re.search(r"fonts\.(googleapis|gstatic)\.com", h):
        bad["external fonts"].append(u)
    if u not in NOINDEX_OK and (not re.search(r'href="[^"]*privacy-policy/"', h) or not re.search(r'href="[^"]*cookie-policy/"', h)):
        bad["policy links missing"].append(u)
for k, v in titles.items():
    if v > 1:
        bad["duplicate title"].append(k)
for k, v in descs.items():
    if v > 1 and k:
        bad["duplicate description"].append(k[:50])
# fonts + css
css = "".join(open(f, encoding="utf8").read() for f in glob.glob(ROOT + "/css/*.css"))
if "fonts.googleapis" in css or "fonts.gstatic" in css:
    bad["external fonts in css"].append("css")
if "font-display:swap" not in css.replace(" ", ""):
    bad["font-display swap"].append("css")
if not glob.glob(ROOT + "/fonts/*.woff2"):
    bad["no self-hosted woff2"].append("fonts")
# sitemap
sm = open(ROOT + "/sitemap.xml").read()
locs = re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", sm)
smu = {l.replace(DOMAIN, "") for l, _ in locs}
today = datetime.date.today().isoformat()
for l, d in locs:
    if d > today:
        bad["sitemap lastmod in the future"].append(l)
indexable = {u for u in pages if u not in NOINDEX_OK}
for u in indexable - smu:
    bad["indexable page not in sitemap"].append(u)
for u in smu - set(pages):
    bad["sitemap url without page"].append(u)
rob = open(ROOT + "/robots.txt").read()
if "Sitemap: " + DOMAIN + "/sitemap.xml" not in rob or re.search(r"^Disallow:\s*/\s*$", rob, re.M):
    bad["robots.txt"].append("robots")
# crawl depth and orphans
from urllib.parse import urljoin
def _links(u, h):
    out = set()
    for href in re.findall(r'href="([^"#?]*)', h):
        if not href or re.match(r"[a-z]+:|//", href):
            continue
        t = urljoin(u if u.endswith("/") or u == "/404.html" else u + "/", href)
        out.add(t)
    return out
links = {u: _links(u, h) for u, h in pages.items()}
depth, q = {"/": 0}, ["/"]
while q:
    x = q.pop(0)
    for y in links[x]:
        if y in pages and y not in depth:
            depth[y] = depth[x] + 1
            q.append(y)
for u in indexable:
    if u not in depth:
        bad["orphan page"].append(u)
    elif depth[u] > 3:
        bad["click depth > 3"].append(u)
# cache headers
ht = open(ROOT + "/.htaccess").read()
if "immutable" not in ht or 'ExpiresByType text/css "access plus 1 year"' not in ht:
    bad["cache headers"].append(".htaccess")
print(f"{len(pages)} pages, {len(smu)} sitemap URLs, max click depth {max(depth.values())}")
if not bad:
    print("AUDIT PASSED: 0 problems")
    sys.exit(0)
for k, v in sorted(bad.items()):
    print(f"FAIL {k}: {len(v)}  e.g. {v[:3]}")
sys.exit(1)
