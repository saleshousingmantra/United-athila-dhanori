#!/usr/bin/env python3
"""retrofit.py: bring an existing static real-estate site up to the Ceratec standard without changing its design.
Idempotent: run it as the LAST step of a build (after minify). Usage:  python3 scripts/retrofit.py [site_root]
Reads <site_root>/scripts/retrofit.json. Applies:
  - keywords + geo meta (and ICBM / place tags when coordinates are known) on every indexable page
  - ?v= on local CSS/JS = hash of the served css/ and js/ files
  - footer links to About, Privacy and Cookie policy; consent line with privacy link; <noscript> form fallback
  - reveal animation removed from hero copy/form (it hides the headline until JS runs)
  - /about/, /privacy-policy/, /cookie-policy/ pages cloned from the site's own guide-page layout
  - sitemap.xml with honest lastmod (content-hash manifest scripts/lastmod.json), llms.txt, robots.txt Sitemap line
  - .htaccess: one-year immutable caching for versioned assets, security headers
  - JSON-LD: telephone and GeoCoordinates on the organisation, hub ItemList stubs without invalid BlogPosting
Nothing is invented: coordinates, phone and names come from the config (which comes from the site itself)."""
import re, os, sys, json, glob, hashlib, datetime, html

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
CFG = json.load(open(os.path.join(ROOT, "scripts", "retrofit.json"), encoding="utf8"))
TODAY = datetime.date.today().isoformat()
DOMAIN = CFG["domain"]
REL = CFG.get("rel", False)          # site uses relative asset/link paths (../../ style)
UTILITY = {"/thank-you/", "/404.html"}


def read(p):
    return open(p, encoding="utf8").read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf8").write(s)


def pages():
    out = {}
    for p in glob.glob(ROOT + "/**/index.html", recursive=True) + [ROOT + "/404.html"]:
        rel = os.path.relpath(p, ROOT)
        if rel.startswith("scripts") or rel.startswith("node_modules"):
            continue
        out["/" + rel.replace("index.html", "")] = p
    return out


def prefix(url):
    """Path prefix to reach the site root from a page url."""
    if not REL:
        return "/"
    depth = url.strip("/").count("/") + 1 if url not in ("/", "/404.html") else 0
    if url == "/404.html":
        return ""
    return "../" * depth


def asset_hash():
    h = hashlib.md5()
    for f in sorted(glob.glob(ROOT + "/css/*.css") + glob.glob(ROOT + "/js/*.js")):
        h.update(open(f, "rb").read())
    return h.hexdigest()[:8]


VER = None
HOME = read(os.path.join(ROOT, "index.html"))
SUPABASE_ON_LOAD = bool(re.search(r'<script[^>]+src="https://cdn\.jsdelivr\.net/npm/@supabase', HOME))
MAPS_EMBED = "output=embed" in HOME
MAPS_LAZY = bool(re.search(r'data-src="https://(www\.google\.com|maps\.google\.com)/maps', HOME))


# ------------------------------------------------------------------ page edits
def inject_meta(h, url):
    if url in UTILITY:
        return h
    add = ""
    title = re.sub(r"\s*[|–—-]\s*[^|]*$", "", re.search(r"<title>(.*?)</title>", h, re.S).group(1)).replace("&amp;", "&")
    if 'name="keywords"' not in h:
        kw = ", ".join([title] + CFG["keywords"])
        add += f'<meta name="keywords" content="{kw.replace(chr(34), "&quot;").replace("&", "&amp;")}">\n'
    if 'name="geo.region"' not in h:
        add += f'<meta name="geo.region" content="{CFG.get("region", "IN-MH")}">\n'
    if 'name="geo.placename"' not in h:
        add += f'<meta name="geo.placename" content="{CFG["placename"]}">\n'
    if CFG.get("lat") and 'name="geo.position"' not in h:
        add += f'<meta name="geo.position" content="{CFG["lat"]};{CFG["lon"]}">\n'
    if CFG.get("lat") and 'name="ICBM"' not in h:
        add += f'<meta name="ICBM" content="{CFG["lat"]}, {CFG["lon"]}">\n'
    if CFG.get("lat") and url == "/" and "place:location:latitude" not in h:
        add += f'<meta property="place:location:latitude" content="{CFG["lat"]}">\n<meta property="place:location:longitude" content="{CFG["lon"]}">\n'
    if add:
        i = h.find('<link rel="canonical"')
        i = i if i >= 0 else h.find("</head>")
        h = h[:i] + add + h[i:]
    return h


def versions(h):
    def sub(m):
        return f'{m.group(1)}{m.group(2)}?v={VER}'
    return re.sub(r'((?:href|src)=")(?!https?:)((?:[^"?]*/)?(?:css|js)/[^"?/]+\.(?:css|js))(?:\?v=[^"]*)?(?=")', sub, h)


def footer_links(h, url):
    m = re.search(r"<footer.*?</footer>", h, re.S)
    if not m:
        return h
    need = [x[1] for x in CFG.get("extra_footer", []) if x[1] not in m.group(0)]
    if "privacy-policy" in m.group(0) and not need:
        return h
    if "privacy-policy" in m.group(0):      # only the extra links are missing
        s2 = re.search(r'<a href="[^"]*cookie-policy/">[^<]*</a>', m.group(0))
        if s2:
            pf = prefix(url)
            sep = "<br>" if m.group(0)[s2.end():s2.end() + 4] == "<br>" else ""
            ins = "".join(f'{sep}<a href="{pf}{p}">{n}</a>' for n, p in [tuple(x) for x in CFG.get("extra_footer", []) if x[1] in need])
            return h.replace(m.group(0), m.group(0)[:s2.end()] + ins + m.group(0)[s2.end():], 1)
        return h
    pf = prefix(url)
    f = m.group(0)
    links = [("About", "about/"), ("Privacy", "privacy-policy/"), ("Cookies", "cookie-policy/")] + [tuple(x) for x in CFG.get("extra_footer", [])]
    s = re.search(r'<a href="[^"]*sitemap/">[^<]*</a>', f)
    if s:
        sep = "<br>" if f[s.end():s.end() + 4] == "<br>" else ""
        ins = "".join(f'{sep}<a href="{pf}{p}">{n}</a>' for n, p in links)
        if sep:
            f2 = f[:s.end()] + ins + f[s.end():]
        else:
            f2 = f[:s.end()] + ins + f[s.end():]
    else:
        ins = " ".join(f'<a href="{pf}{p}">{n}</a>' for n, p in links)
        f2 = f.replace("</footer>", f'<p class="legal-links">{ins}</p></footer>', 1)
    return h.replace(f, f2, 1)


def footer_br(h):
    """Sites whose footer stacks links with <br>: keep the added links on separate lines (adjacent anchors would run together)."""
    if not CFG.get("footer_br"):
        return h
    m = re.search(r"<footer.*?</footer>", h, re.S)
    if not m:
        return h
    return h.replace(m.group(0), m.group(0).replace("</a><a href=", "</a><br><a href="), 1)


def forms(h, url):
    pf = prefix(url)
    pol = f'<a href="{pf}privacy-policy/">Privacy Policy</a>'

    def fix(m):
        f = m.group(0)
        if "privacy-policy" in f:
            return f
        if re.search(r'<p class="consent">', f):
            f = re.sub(r'(<p class="consent">)([^<]*?)(</p>)', lambda x: f'{x.group(1)}{x.group(2).rstrip()} See our {pol}.{x.group(3)}', f, count=1)
        else:
            f = f.replace("</form>", f'<p class="consent" style="font-size:12px;margin:8px 0 0">By submitting you agree to be contacted. See our {pol}.</p></form>', 1)
        if "<noscript" not in f:
            f = f.replace("</form>", '<noscript><p class="consent">This form needs JavaScript. Please call or WhatsApp the sales team, or enable JavaScript.</p></noscript></form>', 1)
        return f
    return re.sub(r"<form\b.*?</form>", fix, h, flags=re.S)


def hero(h):
    h = h.replace('class="hero-copy rv"', 'class="hero-copy"')
    h = re.sub(r'(class="[^"]*hero-form)\s+rv(")', r"\1\2", h)
    return h


def labels(h):
    """Remove aria-labels that differ from the visible text (WCAG 2.5.3 label in name); the visible text names the control."""
    def fix(m):
        tag, attrs1, label, attrs2, inner = m.groups()
        vis = re.sub(r"<(svg|script|style)\b.*?</\1>", "", inner, flags=re.S)
        vis = re.sub(r'<span class="sr-only">.*?</span>', "", vis, flags=re.S)
        vis = re.sub(r"<[^>]+>", "", vis)
        vis = re.sub(r"\s+", " ", html.unescape(vis)).strip().lower()
        if re.search(r"[a-z0-9]", vis) and html.unescape(vis) not in re.sub(r"\s+", " ", label).strip().lower().replace("&amp;", "&"):
            return f"<{tag}{attrs1}{attrs2}>{inner}</{tag}>"
        return m.group(0)
    h = re.sub(r'<(a|button)\b([^>]*?) aria-label="([^"]*)"([^>]*)>(.*?)</\1>', fix, h, flags=re.S)
    def fixrole(m):
        tag = m.group(0)
        if 'role="button"' not in tag:
            return tag
        lab = re.search(r' aria-label="([^"]*)"', tag).group(1)
        name = re.match(r"<(\w+)", tag).group(1)
        depth, inner_end = 0, None
        for t in re.finditer(rf"<(/?){name}\b[^>]*>", h[m.start():]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                inner_end = m.start() + t.start()
                break
        inner = h[m.end():inner_end] if inner_end else ""
        vis = re.sub(r"<(svg|script|style)\b.*?</\1>", "", inner, flags=re.S)
        vis = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", vis))).strip().lower()
        if re.search(r"[a-z0-9]", vis) and vis not in re.sub(r"\s+", " ", html.unescape(lab)).strip().lower():
            return tag.replace(f' aria-label="{lab}"', "", 1)
        return tag
    return re.sub(r'<(?:div|li|span)\b[^>]*aria-label="[^"]*"[^>]*>', fixrole, h)


def structure(h):
    """Landmarks and focusable scroll regions (axe: landmark-one-main, region, scrollable-region-focusable)."""
    if "<main" not in h and "<header" in h and "<footer" in h:
        h = re.sub(r"(</header>)(.*?)(<footer\b)", lambda m: f'{m.group(1)}<main id="main">{m.group(2)}</main>{m.group(3)}', h, count=1, flags=re.S)
    mm = re.search(r"</header>(.*?)(<main\b[^>]*>)", h, re.S)
    if mm and mm.group(1).strip() and "<section" in mm.group(1):      # a hero sits before <main>: make it a labelled region (moving <main> can break the site's CSS)
        between = mm.group(1)
        sec = re.search(r"<section\b(?![^>]*role=)[^>]*>", between)
        if sec:
            t = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
            label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t.group(1))).strip() if t else "Introduction"
            tag = sec.group(0)[:-1] + f' role="region" aria-label="{label}">'
            between2 = between.replace(sec.group(0), tag, 1)
            h = h.replace(between, between2, 1)
    h = re.sub(r"<th(\s[^>]*)?>\s*</th>", lambda m: f'<th{m.group(1) or ""}><span style="display:block;width:0;height:0;overflow:hidden;white-space:nowrap">Item</span></th>', h)
    for cls in CFG.get("tabindex_classes", []):      # horizontally scrolling rows must be keyboard-focusable
        h = re.sub(rf'<div class="([^"]*\b{cls}\b[^"]*)"(?![^>]*tabindex)', rf'<div class="\1" tabindex="0"', h)
    for cls, label in CFG.get("region_classes", {}).items():     # content outside landmarks (e.g. a mobile action bar)
        h = re.sub(rf'<div class="([^"]*\b{cls}\b[^"]*)"(?![^>]*role=)', rf'<div class="\1" role="region" aria-label="{label}"', h)
    n = [0]

    def tw(m):
        n[0] += 1
        return f'<div class="tw" tabindex="0" role="region" aria-label="Table {n[0]}, scrolls sideways on small screens">'
    return re.sub(r'<div class="tw">', tw, h)


def css_append():
    block = CFG.get("css_append")
    if not block:
        return
    for f in glob.glob(ROOT + "/css/*.css"):
        t = read(f)
        if "/*retrofit-a11y*/" in t:
            t = t[:t.index("/*retrofit-a11y*/")]
        write(f, t.rstrip() + "\n/*retrofit-a11y*/\n" + block + "\n")


def hero_variants(h, page_path):
    """Add a 640 px version of the first-screen (fetchpriority=high) image so phones do not download the 960+ px file."""
    from PIL import Image
    def resolve(u):
        return os.path.normpath(os.path.join(ROOT, u.lstrip("/"))) if u.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(page_path), u))

    def expand(srcset):
        ents = [e.strip().rsplit(" ", 1) for e in srcset.split(",") if e.strip()]
        if not ents or any(not e[1].endswith("w") for e in ents if len(e) == 2) or len(ents[0]) != 2:
            return srcset
        small = min(int(e[1][:-1]) for e in ents)
        if small <= 700:
            return srcset
        big = max(ents, key=lambda e: int(e[1][:-1]))
        src = resolve(big[0])
        if not os.path.exists(src):
            return srcset
        base, ext = os.path.splitext(big[0])
        new_rel = re.sub(r"-(?:md|\d+)$", "", base) + "-640" + ext
        dst = resolve(new_rel)
        if not os.path.exists(dst):
            im = Image.open(src).convert("RGB")
            im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS).save(dst, "WEBP", quality=72, method=6)
        return f"{new_rel} 640w, " + srcset

    h = re.sub(r'(<link rel="preload" as="image"[^>]*?imagesrcset=")([^"]*)(")', lambda m: m.group(1) + expand(m.group(2)) + m.group(3), h)
    h = re.sub(r'(<img\b[^>]*?fetchpriority="high"[^>]*?srcset=")([^"]*)(")', lambda m: m.group(1) + expand(m.group(2)) + m.group(3), h)
    h = re.sub(r'(<img\b[^>]*?srcset=")([^"]*)("[^>]*?fetchpriority="high")', lambda m: m.group(1) + expand(m.group(2)) + m.group(3), h)
    return h


def balance_gcards(h):
    """Guide hubs: the cards container <div class="gcards"> must be closed before the empty-state message (one site left it open)."""
    if '<div class="gcards"' in h and h.count("<div") == h.count("</div>") + 1:
        h = re.sub(r'(</a>\s*)(<div class="empty">)', r"\1</div>\n\2", h, count=1)
    return h


def misc(h, url):
    h = balance_gcards(h)
    h = h.replace('style="font-size:12px;opacity:.8;margin:8px 0 0"', 'style="font-size:12px;margin:8px 0 0"')
    h = structure(h)
    h = labels(h)
    h = re.sub(r'<link[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>\n?', "", h)
    if url == "/sitemap/":
        h = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">', h)
    # decorative logo/emblem images still carry the project name
    h = re.sub(r'(<img\b[^>]*?src="[^"]*(?:emblem|logo)[^"]*"[^>]*?) alt=""', lambda m: m.group(1) + f' alt="{CFG["short"]} logo"', h)
    return h


def jsonld(h, url):
    def fix(m):
        raw = m.group(1)
        try:
            j = json.loads(raw)
        except Exception:
            return m.group(0)
        changed = False

        def walk(o):
            nonlocal changed
            if isinstance(o, dict):
                t = o.get("@type")
                ts = t if isinstance(t, list) else [t]
                if ("Organization" in ts or "RealEstateAgent" in ts) and "url" not in o and "@id" not in o:
                    o["url"] = DOMAIN + "/"; changed = True
                if "ContactPoint" in ts and CFG.get("phone") and "telephone" not in o:
                    o["telephone"] = CFG["phone"]; changed = True
                if ("Organization" in ts or "RealEstateAgent" in ts) and CFG.get("lat") and "geo" not in o:
                    o["geo"] = {"@type": "GeoCoordinates", "latitude": float(CFG["lat"]), "longitude": float(CFG["lon"])}; changed = True
                if ("ApartmentComplex" in ts or "Residence" in ts) and CFG.get("lat") and "geo" not in o:
                    o["geo"] = {"@type": "GeoCoordinates", "latitude": float(CFG["lat"]), "longitude": float(CFG["lon"])}; changed = True
                if "CollectionPage" in ts:
                    for it in o.get("hasPart", []):
                        if isinstance(it, dict) and it.get("@type") == "BlogPosting" and "datePublished" not in it:
                            it["@type"] = "WebPage"; it["name"] = it.pop("headline", it.get("name")); changed = True
                if "ItemList" in ts:
                    for it in o.get("itemListElement", []):
                        x = it.get("item") if isinstance(it, dict) else None
                        if isinstance(x, dict) and x.get("@type") == "BlogPosting":
                            it["url"] = x.get("url") or x.get("@id") or x.get("mainEntityOfPage")
                            it["name"] = x.get("name") or x.get("headline")
                            del it["item"]; changed = True
                for v in list(o.values()):
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(j)
        if not changed:
            return m.group(0)
        return '<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False, separators=(",", ":")) + "</script>"
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, h, flags=re.S)


# ------------------------------------------------------------------ new pages
def balanced(h, start_re, repl):
    """Replace the whole element (balanced <div>) whose opening tag matches start_re with repl."""
    m = re.search(start_re, h)
    if not m:
        return h
    tag = re.match(r"<(\w+)", m.group(0)).group(1)
    depth, i = 0, m.start()
    for t in re.finditer(rf"<(/?){tag}\b[^>]*>", h[m.start():]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return h[:m.start()] + repl + h[m.start() + t.end():]
    return h


def template():
    cands = sorted(glob.glob(ROOT + "/blog/*/*/index.html"), key=lambda p: len(read(p)))
    for p in cands:
        h = read(p)
        if "<article" in h and 'class="bhero"' in h:
            return h
    raise SystemExit("no guide-page template found")


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def make_page(slug, title, desc, h1, dek, body, tpl):
    url = f"/{slug}/"
    pf = prefix(url)
    h = tpl
    if REL:
        h = h.replace("../../../", pf)
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    h = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h, count=1)
    h = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + DOMAIN + url + m.group(2), h)
    h = re.sub(r'(<link rel="alternate" hreflang="[^"]*" href=")[^"]*(")', lambda m: m.group(1) + DOMAIN + url + m.group(2), h)
    for k in ("og:title", "twitter:title"):
        h = re.sub(rf'(<meta (?:property|name)="{k}" content=")[^"]*(")', lambda m: m.group(1) + esc(title) + m.group(2), h)
    for k in ("og:description", "twitter:description"):
        h = re.sub(rf'(<meta (?:property|name)="{k}" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h)
    h = re.sub(r'(<meta property="og:url" content=")[^"]*(")', lambda m: m.group(1) + DOMAIN + url + m.group(2), h)
    h = re.sub(r'(<meta property="og:type" content=")[^"]*(")', r"\1website\2", h)
    h = re.sub(r'<meta name="keywords" content="[^"]*">\n?', "", h)
    h = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">', h)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": DOMAIN + url + "#webpage", "url": DOMAIN + url, "name": title, "description": desc, "inLanguage": "en-IN", "isPartOf": {"@id": DOMAIN + "/#website"}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"}, {"@type": "ListItem", "position": 2, "name": h1, "item": DOMAIN + url}]}]}
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>', h, re.S))
    if blocks:
        first = blocks[0]
        h = h[:first.start()] + '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>" + h[first.end():]
        for b in list(re.finditer(r'<script type="application/ld\+json">.*?</script>', h, re.S))[1:][::-1]:
            h = h[:b.start()] + h[b.end():]
    h = re.sub(r'(<h1>).*?(</h1>)', lambda m: m.group(1) + esc(h1) + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r'(<p class="dek">).*?(</p>)', lambda m: m.group(1) + esc(dek) + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r'(<span class="tag-pill">).*?(</span>)', lambda m: m.group(1) + "Information" + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r'<p class="crumbs">.*?</p>', f'<p class="crumbs"><a href="{pf}">Home</a> &rsaquo; {esc(h1)}</p>', h, count=1, flags=re.S)
    h = balanced(h, r'<div class="metarow"[^>]*>', f'<div class="metarow"><span>Updated {TODAY}</span></div>')
    am = re.search(r"<article[^>]*>", h)
    if am:
        end = h.find("</article>", am.end())
        h = h[:am.end()] + "\n" + body + "\n" + h[end:]
    toc = "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in heads)
    h = re.sub(r'(<details class="toc"[^>]*>.*?<ol[^>]*>).*?(</ol>)', lambda m: m.group(1) + toc + m.group(2), h, count=1, flags=re.S)
    h = h.replace(' aria-current="page"', "")
    return h


def legal_pages(tpl):
    L = CFG["legal"]
    name, dev = CFG["short"], CFG["developer"]
    pf = "../" if REL else "/"
    root = "../" if REL else "/"
    supa = ("When you open any page, a script for the enquiry form is loaded from a content delivery network, and your enquiry is sent to a managed database service when you submit it. Those providers may receive your IP address and browser details."
            if SUPABASE_ON_LOAD else
            "When you start filling a form, the page loads a script from a content delivery network and sends your enquiry to a managed database service. Those providers may receive your IP address and browser details.")
    maps = ("<li><strong>Google Maps:</strong> the map is loaded only when you open it. Google may then set its own cookies, under Google's policies.</li>" if MAPS_EMBED and MAPS_LAZY else
            "<li><strong>Google Maps:</strong> the map on this site loads with the page. Google may set its own cookies, under Google's policies.</li>" if MAPS_EMBED else
            "<li><strong>Google Maps:</strong> map links open Google Maps on a new tab only when you click them. Google may then set its own cookies, under Google's policies.</li>")
    partner = L["partner_text"]
    about = f"""
<h2 id="who">Who we are</h2>
<p>{partner}</p>
{('<h2 id="independence">What that means for you</h2><p>' + L["independence"] + '</p>') if L.get("independence") else ""}
<h2 id="sources">Where the information comes from</h2>
<ul><li>Prices, carpet areas, home types and offers come from the developer's launch and sales material shared with the sales team.</li>
<li>Calculations, such as price per sq ft or EMI examples, are our own arithmetic on those figures and are labelled as illustrations.</li>
<li>Locality information points to live map links. We do not state distances or travel times we have not verified.</li>
<li>We do not publish reviews or testimonials that we cannot verify. Items that are not confirmed are marked as such.</li></ul>
<h2 id="accuracy">Keeping it accurate</h2>
<p>Plans, specifications, amenities and prices change with approvals, so ask the sales team for the current cost sheet before you decide, and verify the project's registration on <a href="https://maharera.maharashtra.gov.in/" target="_blank" rel="noopener">MahaRERA</a>.</p>
<h2 id="corrections">Corrections and contact</h2>
<p>If you spot an error, tell us through the enquiry form on the <a href="{root}#{L.get("contact_id", "contact")}">home page</a> and we will check and correct it. Our <a href="{pf}privacy-policy/">Privacy Policy</a> and <a href="{pf}cookie-policy/">Cookie Policy</a> explain how we handle your details.</p>
"""
    privacy = f"""
<h2 id="who">Who runs this website</h2>
<p>{partner} This policy explains what we collect when you use it.</p>
<h2 id="collect">What we collect</h2>
<ul><li><strong>Details you give us:</strong> your name, mobile number, email address and the home type you are interested in, when you submit an enquiry form.</li>
<li><strong>Where you came from:</strong> the page or campaign that brought you here (for example a search result or an advertisement), kept for the visit so that we know which enquiry came from where.</li>
<li><strong>Technical data:</strong> like any website, our host and the services described below may receive your IP address, browser type and the pages you open.</li></ul>
<h2 id="use">How we use it</h2>
<ul><li>To call, message or email you about the project, prices, offers and site visits that you asked about.</li>
<li>To share your enquiry with the developer's sales team so that they can follow up.</li>
<li>To understand which pages and campaigns work, and to improve the website.</li></ul>
<p>We do not sell your details. We share them only with the developer and with service providers who help us run the website and manage enquiries, and when the law requires it.</p>
<h2 id="store">Where your details are stored</h2>
<p>Enquiries are saved in a managed database service so that the sales team can see them. We keep them for as long as needed to follow up on your enquiry and to meet legal requirements, and then delete or anonymise them.</p>
<h2 id="rights">Your choices and rights</h2>
<ul><li>You can ask us to show, correct or delete the details we hold about you.</li><li>You can tell us to stop contacting you, and we will do so.</li><li>You can withdraw your consent at any time. This does not affect what was done before you withdrew it.</li></ul>
<p>To make a request, use the enquiry form on the <a href="{root}#{L.get("contact_id", "contact")}">home page</a> and mention your request and the mobile number you used.</p>
<h2 id="links">Links to other websites</h2>
<p>This website links to other sites, including Google Maps, WhatsApp and the MahaRERA website. They have their own privacy policies and we are not responsible for them.</p>
<h2 id="children">Children</h2>
<p>This website is for adults who are considering a home purchase. We do not knowingly collect details from children.</p>
<h2 id="changes">Changes to this policy</h2>
<p>We may update this policy as the website changes. The date at the top of the page shows when it was last updated. See also our <a href="{pf}cookie-policy/">Cookie Policy</a>.</p>
"""
    cookie = f"""
<h2 id="what">What cookies are</h2>
<p>Cookies are small text files that a website saves in your browser. Similar technologies, such as session storage, work in much the same way. This page lists what this website actually uses.</p>
<h2 id="own">What this website itself stores</h2>
<ul><li><strong>No tracking cookies:</strong> this website does not set advertising or analytics cookies of its own.</li>
<li><strong>Session storage (essential):</strong> when you arrive, the website remembers in your browser session where you came from (for example a search result or an advertisement) so that an enquiry you make a few pages later can be linked to it. It is deleted when you close the tab.</li></ul>
<h2 id="third">Third-party services</h2>
<ul><li><strong>Enquiry form service:</strong> {supa}</li>
{maps}
<li><strong>Links you click:</strong> WhatsApp, MahaRERA and other sites you open have their own cookie practices.</li></ul>
<h2 id="control">How to control cookies</h2>
<p>You can block or delete cookies and site storage in your browser settings. If you do, the website will still work, but the source of an enquiry may not be recorded. Because we do not set non-essential cookies ourselves, there is no cookie banner on this website.</p>
<h2 id="future">If this changes</h2>
<p>If we add analytics, advertising pixels or a chat widget, we will update this page and ask for your consent where the law requires it. See also our <a href="{pf}privacy-policy/">Privacy Policy</a>.</p>
"""
    specs = [("about", f"About This Website | {name}", f"Who runs this website, where its information about {name} comes from, how we keep it accurate and how to reach us.", f"About This Website: {name}", "Who runs this website, where its information comes from and how we keep it accurate.", about),
             ("privacy-policy", f"Privacy Policy | {name}", f"How this website collects, uses and protects the details you share when you enquire about {name}.", f"Privacy Policy: {name}", "How this website collects, uses and protects the details you share when you enquire.", privacy),
             ("cookie-policy", f"Cookie Policy | {name}", "What cookies and similar storage this website uses, why, and how to control them.", f"Cookie Policy: {name}", "What cookies and similar storage this website uses, why, and how to control them.", cookie)]
    for slug, title, desc, h1, dek, body in specs:
        if os.path.exists(os.path.join(ROOT, slug, "index.html")) and not os.environ.get("RETROFIT_FORCE"):
            continue      # keep existing policy pages stable (dates and lastmod); RETROFIT_FORCE=1 rewrites them
        if len(title) > 60:
            title = title[:57].rstrip() + "..."
        write(os.path.join(ROOT, slug, "index.html"), make_page(slug, title, desc[:160], h1, dek, body, tpl))


# ------------------------------------------------------------------ site files
def sitemap_and_files(allpages):
    mf = os.path.join(ROOT, "scripts", "lastmod.json")
    old = json.load(open(mf)) if os.path.exists(mf) else {}
    urls = []
    for u, p in sorted(allpages.items()):
        h = read(p)
        if "noindex" in (re.search(r'name="robots" content="([^"]*)"', h) or [None, ""])[1] or u in UTILITY:
            continue
        urls.append(u)
    new, lines = {}, []
    for u in urls:
        h = read(allpages[u])
        norm = re.sub(r"\?v=[0-9a-f]+", "", re.sub(r"20\d\d-\d\d-\d\d", "", h))
        dg = hashlib.md5(norm.encode()).hexdigest()
        date = old[u]["date"] if u in old and old[u]["hash"] == dg else TODAY
        new[u] = {"hash": dg, "date": date}
        lines.append(f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{date}</lastmod></url>")
    write(os.path.join(ROOT, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(lines) + "\n</urlset>\n")
    json.dump(new, open(mf, "w"), indent=0, sort_keys=True)
    rb = os.path.join(ROOT, "robots.txt")
    r = read(rb) if os.path.exists(rb) else "User-agent: *\nAllow: /\n"
    if f"Sitemap: {DOMAIN}/sitemap.xml" not in r:
        r = re.sub(r"\n?Sitemap:.*\n?", "\n", r).rstrip() + f"\n\nSitemap: {DOMAIN}/sitemap.xml\n"
    write(rb, r)
    ks = "\n".join(f"- [{n}]({DOMAIN}{p})" for n, p in CFG["key_pages"])
    write(os.path.join(ROOT, "llms.txt"), f"# {CFG['short']}\n\n> {CFG['summary']}\n\n## Key pages\n\n{ks}\n")


def htaccess():
    p = os.path.join(ROOT, ".htaccess")
    t = read(p) if os.path.exists(p) else ""
    t = re.sub(r'ExpiresByType text/css "access plus [^"]*"', 'ExpiresByType text/css "access plus 1 year"', t)
    t = re.sub(r'ExpiresByType application/javascript "access plus [^"]*"', 'ExpiresByType application/javascript "access plus 1 year"', t)
    if "immutable" not in t:
        block = '''
<IfModule mod_headers.c>
  # CSS, JS, fonts and images are versioned (?v=hash) or never change: browsers may keep them for a year
  <FilesMatch "\\.(css|js|woff2|webp|png|jpg|jpeg|svg)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
  <FilesMatch "\\.(html)$">
    Header set Cache-Control "public, max-age=0, must-revalidate"
  </FilesMatch>
</IfModule>
'''
        t = t.rstrip() + "\n" + block
    need = [("Strict-Transport-Security", 'Header always set Strict-Transport-Security "max-age=31536000"'), ("X-Content-Type-Options", 'Header always set X-Content-Type-Options "nosniff"'),
            ("Referrer-Policy", 'Header always set Referrer-Policy "strict-origin-when-cross-origin"'), ("X-Frame-Options", 'Header always set X-Frame-Options "SAMEORIGIN"'),
            ("Permissions-Policy", 'Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"')]
    missing = [l for k, l in need if k not in t]
    if missing:
        t = t.rstrip() + "\n<IfModule mod_headers.c>\n  " + "\n  ".join(missing) + "\n</IfModule>\n"
    write(p, t)


def main():
    global VER
    tpl = template()
    css_append()
    VER = asset_hash()
    legal_pages(tpl)
    allp = pages()
    for u, p in allp.items():
        h = read(p)
        h0 = h
        h = inject_meta(h, u)
        h = footer_links(h, u)
        h = footer_br(h)
        h = forms(h, u)
        h = hero(h)
        h = misc(h, u)
        h = hero_variants(h, p)
        h = jsonld(h, u)
        h = versions(h)
        if h != h0:
            write(p, h)
    sitemap_and_files(allp)
    htaccess()
    print(f"retrofit done: {len(allp)} pages, asset version {VER}")


if __name__ == "__main__":
    main()
