#!/usr/bin/env python3
"""kwpages.py: keyword-targeting pages for an EXISTING site (the Ceratec pseo/seo_pages idea, data-driven, no generator needed).
Usage:  python3 scripts/kwpages.py [site_root]   then   python3 scripts/retrofit.py [site_root]
Reads scripts/kwpages.json (the site's own facts: home types with carpet areas and prices, locality, landmarks) and writes native-looking pages
by cloning the site's own guide layout (via retrofit.make_page):
  <type>-flats-in-<locality>, <type>-flats-in-<city>   (only for types the project sells)
  flats-in-<locality>, flats-in-<city>                 (overview pages)
  flats-under-<budget>-in-<locality>                   (computed from the price data)
  home-loan-emi-calculator, total-flat-cost-calculator (static JS)
  brochure, possession date, location, reviews (honest), site visit, carpet-area explainer, home-loan checklist
  flat-guides                                          (hub page that links all of them; linked from the footer)
Nothing is invented: figures come from the config, which comes from the site; unknowns are framed as "what to ask / where to verify"."""
import sys, os, re, json, importlib.util

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.argv = ["retrofit", ROOT]
spec = importlib.util.spec_from_file_location("rf", os.path.join(ROOT, "scripts", "retrofit.py"))
rf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rf)
K = json.load(open(os.path.join(ROOT, "scripts", "kwpages.json"), encoding="utf8"))
NAME, SHORT, DEV, LOC, CITY = K["name"], K["short"], K["developer"], K["loc"], K["city"]
LOCS, CITYS = K["loc_slug"], K["city_slug"]
PFX = K["slug_prefix"]
TYPES = K["types"]
PRE = "../" if rf.REL else "/"          # prefix from a depth-1 page to the site root


def emi(p, rate, years):
    r = rate / 1200.0
    n = years * 12
    return round(p * r * (1 + r) ** n / ((1 + r) ** n - 1))


def inr(v):
    return f"₹{v / 1e7:.2f} Cr" if v >= 1e7 else f"₹{v / 1e5:.2f} Lakh"


def li(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def maps(q):
    from urllib.parse import quote_plus
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(q)


def link(slug, text):
    return f'<a href="{PRE}{slug}/">{text}</a>'


PAGES = []     # (slug, title, desc, h1, dek, body, pill)
FROM = inr(min(t["p_lo"] for t in TYPES))
TO = inr(max(t["p_hi"] for t in TYPES))
LOCGUIDE = K.get("locality_guide", "")
CTA = f'<p class="soft-cta">Want the current cost sheet and brochure for {SHORT}? <a href="{PRE}#{K.get("contact_id", "contact")}">Send an enquiry</a> or use the Call and WhatsApp buttons on this site.</p>'
BASIS = K.get("price_basis", "as given in the sales material")


def tbl(rows):
    trs = "".join(f"<tr><td>{t['label']}</td><td>{t['area']} sq ft</td><td>{inr(t['p_lo'])}{' onwards' if t.get('open') else (' – ' + inr(t['p_hi']) if t['p_hi'] != t['p_lo'] else '')}</td><td>{(lambda a, b: f"₹{a:,.0f}" if a == b else f"₹{a:,.0f} – ₹{b:,.0f}")(round(t['p_lo'] / t['a_lo'], -1), round(t['p_hi'] / t['a_hi'], -1))}</td></tr>" for t in rows)
    return f'<table class="tbl"><thead><tr><th>Home type</th><th>Carpet area</th><th>Price*</th><th>Approx. per sq ft of carpet</th></tr></thead><tbody>{trs}</tbody></table><p class="note">*Prices {BASIS}; subject to change, so ask for the current cost sheet. The per sq ft figure is our own arithmetic on the listed price and carpet area.</p>'


def emi_table():
    return '<table class="tbl"><thead><tr><th>Interest rate</th><th>15 years</th><th>20 years</th><th>25 years</th></tr></thead><tbody>' + "".join(
        f"<tr><th>{r}% a year</th>" + "".join(f"<td>₹{emi(1000000, r, y):,}</td>" for y in (15, 20, 25)) + "</tr>" for r in (8, 9, 10)) + "</tbody></table><p class=\"note\">EMI per ₹10 lakh borrowed.</p>"


def place_block(place, is_city):
    if is_city:
        about = f"Buyers comparing across {CITY} usually start with their own commute: where they work, where family lives and where the children will study. {SHORT} is in {K['loc_full']}."
        why = "Then compare total cost and carpet area, not just the headline rate, and check the route on the live map at your own hours."
    else:
        about = K["about_loc"]
        why = f"Use the live map links below to check the route and travel time at the hours you travel, instead of relying on a quoted distance."
    maps_ = "".join(f'<li><a href="{maps(m)}" target="_blank" rel="noopener">{n}</a> (live map, check route and time)</li>' for n, m in K["landmarks"])
    return f'<h2 id="place">Looking in {place}</h2><p>{about}</p><p>{why}</p><ul>{maps_}</ul>'


def siblings(exclude=None):
    items = [(f"{t['slug']}-flats-in-{LOCS}", f"{t['label']} flats in {LOC}") for t in TYPES]
    items += [(f"flats-in-{LOCS}", f"All flats in {LOC}"), ("home-loan-emi-calculator", "Home loan EMI calculator"), ("flat-guides", "All flat guides")]
    return "<ul>" + "".join(f'<li>{link(s, t)}</li>' for s, t in items if s != exclude) + "</ul>"


def scenario(kind, t):
    lo = t["p_lo"]
    if kind == "income":
        e = emi(int(lo * 0.8), 9, 20)
        return ("A rough affordability check", f"A common rule of thumb keeps total loan EMIs below about 40% of monthly take-home income, though lenders differ. On that basis, an EMI of about ₹{e:,} (80% of the lowest listed {t['label']} price, 9% a year, 20 years) points to a household take-home income of roughly ₹{round(e / 0.4, -3):,.0f} a month. Treat it as a conversation starter with your bank.")
    if kind == "upfront":
        return ("Upfront cash to plan for", f"A 20% down payment on the lowest listed {t['label']} price ({inr(lo)}) is about {inr(int(lo * 0.2))}. Stamp duty, registration, GST where applicable, maintenance deposits and parking may be separate depending on how the quoted price is built, so ask for them in writing on the cost sheet.")
    rate = round(lo / t["a_lo"], -1)
    return ("What your budget buys", f"At the lowest listed rate of about ₹{rate:,.0f} per sq ft of carpet area, ₹1 crore buys roughly {round(1e7 / rate):,} sq ft of carpet area in this home type. Use the same sum on every project you compare, using carpet area and the full payable price.")


# ---------------------------------------------------------------- type pages
SUIT = {1: "suits a couple, a small family or a first-time buyer, with a lower EMI and lower maintenance bill.",
        2: "suits a family that wants a flexible extra room, such as a study or nursery.",
        3: "suits a growing family or a household that works from home, with a bedroom for each member."}
CHECK = {1: ["Is the second bedroom big enough for a double bed and a wardrobe?", "Does the kitchen have room for a utility or washing area?", "Which way do the balconies face?"],
         2: ["Is the extra room a proper room with a window?", "Can it fit a desk and a bed, or only one?", "Which way do the balconies face?"],
         3: ["Do all three bedrooms get a window and a usable wall for a bed?", "Is there a separate utility area and a dry balcony?", "How many parking spaces come with the home?"]}
for place, slug_place, is_city, kind in ((LOC, LOCS, False, "income"), (CITY, CITYS, True, "budget")):
    for i, t in enumerate(TYPES):
        title = f"{t['label']} Flats in {place}{'' if is_city else ', ' + CITY} from {inr(t['p_lo'])}"
        if len(title) > 60:
            title = f"{t['label']} Flats in {place} from {inr(t['p_lo'])}"
        loan = int(t["p_lo"] * 0.8)
        sc = scenario(kind, t)
        key = {2: 1, 2.5: 2, 3: 3}.get(t["beds"], 1)
        body = (f'<h2 id="overview">{t["label"]} homes at {NAME}</h2>'
                f'<p>If you are looking for a {t["label"]} in {place}, {SHORT} by {DEV} offers {t["label"]} homes with carpet areas of {t["area"]} sq ft, priced from {inr(t["p_lo"])}{" onwards" if t.get("open") else ((" to " + inr(t["p_hi"])) if t["p_hi"] != t["p_lo"] else "")} ({BASIS}).</p>' + tbl([t]) +
                place_block(place, is_city) +
                (f'<h2 id="across">Comparing {t["label"]} homes across {CITY}</h2><p>If you are comparing {t["label"]} flats across {CITY}, line up each project on the same five numbers: carpet area, total price with every charge, price per sq ft of carpet area, declared possession date and your commute. At {SHORT}, the {t["label"]} works out to about ₹{round(t["p_lo"] / t["a_lo"], -1):,.0f} per sq ft of carpet area at its starting price, so a project quoting a lower headline rate on saleable area may not be cheaper once converted.</p>' if is_city else
                 f'<h2 id="living">Living in {LOC}</h2><p>Before you commit to a {t["label"]} in {LOC}, read the locality guides on this site and then check each place on the live map at your own hours.</p><ul>' + "".join(f'<li><a href="{u}">{x}</a></li>' for x, u in K.get("locality_links", [])) + '</ul>') +
                f'<h2 id="who">Who a {t["label"]} suits</h2><p>A {t["label"]} {SUIT[key]}</p>'
                f'<h2 id="cost">What a {t["label"]} costs per month</h2><p>As an illustration only, borrowing 80% of the lowest listed {t["label"]} price ({inr(t["p_lo"])}) means a loan of about {inr(loan)}. Over 20 years the EMI is about ₹{emi(loan, 8, 20):,} a month at 8%, ₹{emi(loan, 9, 20):,} at 9% and ₹{emi(loan, 10, 20):,} at 10%. Your own rate, tenure and down payment will change this.</p>{emi_table()}'
                f'<h2 id="scenario">{sc[0]}</h2><p>{sc[1]}</p>'
                f'<h2 id="check">What to check inside a {t["label"]}</h2>{li(CHECK[key])}'
                f'<h2 id="faq">Quick answers</h2><p><strong>What is the price of a {t["label"]}?</strong> From {inr(t["p_lo"])}, depending on the unit and floor ({BASIS}).</p><p><strong>What is the carpet area?</strong> {t["area"]} sq ft.</p><p><strong>Is the project RERA registered?</strong> {K["rera_text"]}</p>'
                f'<h2 id="more">More in {place}</h2>{siblings(f"{t["slug"]}-flats-in-{LOCS}" if not is_city else None)}' + CTA)
        PAGES.append((f"{t['slug']}-flats-in-{slug_place}", title, f"{t['label']} homes at {SHORT} ({place}): {t['area']} sq ft carpet from {inr(t['p_lo'])}, with price table and EMI examples.", f"{t['label']} Flats in {place}: {SHORT}", f"{t['label']} homes, prices, EMI examples and a buyer checklist for {place}.", body, "Home types"))

# ---------------------------------------------------------------- overview pages
for place, slug_place, is_city in ((LOC, LOCS, False), (CITY, CITYS, True)):
    types_li = "".join(f"<li>{link(t['slug'] + '-flats-in-' + slug_place, t['label'] + ' flats in ' + place)}: {t['area']} sq ft carpet, from {inr(t['p_lo'])}</li>" for t in TYPES)
    body = (f'<h2 id="overview">Flats in {place} at {NAME}</h2><p>{SHORT}, by {DEV}, offers {", ".join(t["label"] for t in TYPES)} homes at {K["loc_full"]}, priced from {FROM}{" onwards" if any(t.get("open") for t in TYPES) else " to " + TO} ({BASIS}). If you are searching for flats in {place}, this is how the home types compare.</p><ul>{types_li}</ul>' + tbl(TYPES) +
            place_block(place, is_city) +
            (f'<h2 id="compare">How the home types compare</h2><p>The lowest listed price rises from {inr(TYPES[0]["p_lo"])} for the {TYPES[0]["label"]} to {inr(TYPES[-1]["p_lo"])} for the {TYPES[-1]["label"]}, a step of {inr(TYPES[-1]["p_lo"] - TYPES[0]["p_lo"])}. With an 80% loan at 9% over 20 years, that moves the monthly EMI from about ₹{emi(int(TYPES[0]["p_lo"] * 0.8), 9, 20):,} to about ₹{emi(int(TYPES[-1]["p_lo"] * 0.8), 9, 20):,}. Carpet area grows from {TYPES[0]["area"]} sq ft to {TYPES[-1]["area"]} sq ft, so compare the extra space with the extra cost, not just the headline price.</p>'
             f'<h2 id="ask">Questions to ask the sales team</h2>' + li(["What is the total payable for the unit and floor you want, and what is included?", "Which towers or floors are available at the starting price?", "What is the declared possession date on the RERA registration?", "How many parking spaces come with the home?"]) if not is_city else
             f'<h2 id="framework">A simple way to compare projects across {CITY}</h2><p>Make a table with one row per project and these columns: carpet area, total price including every charge, price per sq ft of carpet area, declared possession date, RERA number and your commute in minutes. Fill it from the cost sheet, not from advertisements. At {SHORT}, the lowest listed rate works out to about ₹{round(min(t["p_lo"] / t["a_lo"] for t in TYPES), -1):,.0f} per sq ft of carpet area, which gives you a number to test other projects against.</p>'
             f'<h2 id="budget">What a budget buys across the range</h2><p>At the lowest listed rate, ₹1 crore buys roughly {round(1e7 / min(t["p_lo"] / t["a_lo"] for t in TYPES)):,} sq ft of carpet area here. Use the same sum on every project you shortlist, and keep a reserve for charges, interiors and moving.</p>') +
            f'<h2 id="next">Before you decide</h2><p>Verify the RERA registration on MahaRERA, ask for the current cost sheet and visit the site. {K["rera_text"]}</p>' +
            f'<h2 id="more">More guides</h2>{siblings(f"flats-in-{LOCS}" if not is_city else None)}' + CTA)
    PAGES.append((f"flats-in-{slug_place}", f"Flats in {place}: {', '.join(t['label'] for t in TYPES)} from {FROM}"[:60], f"New flats in {place} at {SHORT}: {', '.join(t['label'] for t in TYPES)} from {FROM}. Prices, carpet areas and what to check.", f"Flats in {place}: {SHORT}", f"{', '.join(t['label'] for t in TYPES)} homes from {FROM}, compared.", body, "Home types"))

# ---------------------------------------------------------------- budget pages
for B, bl, bs in K["budgets"]:
    fit = [t for t in TYPES if t["p_lo"] <= B]
    if not fit:
        continue
    loan = int(B * 0.8)
    rate_lo = min(t["p_lo"] / t["a_lo"] for t in TYPES)
    rate_hi = max(t["p_lo"] / t["a_lo"] for t in fit)
    rows = "".join(f"<tr><td>{t['label']}</td><td>{t['area']} sq ft</td><td>{inr(t['p_lo'])}{' onwards' if t.get('open') else (' – ' + inr(t['p_hi']) if t['p_hi'] != t['p_lo'] else '')}</td><td>{'Whole range within budget' if (t['p_hi'] <= B and not t.get('open')) else 'Starting price within budget'}</td></tr>" for t in fit)
    body = (f'<h2 id="overview">What {bl} buys at {NAME}</h2><p>With a budget of {bl}, {len(fit)} of the {len(TYPES)} home types at {SHORT} start within it: {", ".join(t["label"] for t in fit)}.</p>'
            f'<table class="tbl"><thead><tr><th>Home type</th><th>Carpet area</th><th>Price*</th><th>Fit</th></tr></thead><tbody>{rows}</tbody></table><p class="note">*Prices {BASIS}; subject to change. Set your budget against the total cost sheet, not the base price.</p>'
            f'<h2 id="emi">Monthly cost at {bl}</h2><p>Borrowing 80% of {bl} ({inr(loan)}) over 20 years gives an EMI of about ₹{emi(loan, 8, 20):,} a month at 8%, ₹{emi(loan, 9, 20):,} at 9% and ₹{emi(loan, 10, 20):,} at 10%. A lender applying a 40% EMI-to-income rule of thumb at 9% would look for take-home income of roughly ₹{round(emi(loan, 9, 20) / 0.4, -3):,.0f} a month; lenders differ.</p>{emi_table()}'
            f'<h2 id="upfront">Down payment</h2><p>A 20% down payment on {bl} is about {inr(int(B * 0.2))}. Ask what is included in the quoted price and what is extra.</p>'
            f'<h2 id="area">How much carpet area {bl} buys</h2><p>At the project\'s listed rates of roughly ₹{round(rate_lo, -1):,.0f} to ₹{round(rate_hi, -1):,.0f} per sq ft of carpet area, {bl} buys about {round(B / rate_hi):,} to {round(B / rate_lo):,} sq ft of carpet area. Use the same sum on every project you compare.</p>'
            f'<h2 id="suits">Who this budget suits</h2><p>' + (f'Every home type at {SHORT} starts within {bl}, so the decision is about layout, floor and orientation rather than affordability, and the smaller types leave room for parking, interiors and a reserve.' if len(fit) == len(TYPES) else f'Only the {fit[0]["label"]} starts within {bl}, so you are choosing among its units and floors; the larger types need a bigger budget or a longer plan.' if len(fit) == 1 else f'{len(fit)} of the {len(TYPES)} home types start within {bl}; the larger types need a bigger budget, so compare the biggest {fit[-1]["label"]} you can afford with the smallest of the next type up.') + f' A buyer with take-home income near ₹{round(emi(loan, 9, 20) / 0.4, -3):,.0f} a month could carry an 80% loan on the full {bl} at 9%, on the usual 40% rule of thumb.</p>'
            f'<h2 id="variants">EMI and down payment per home type</h2><p>For the lowest price of each home type that fits, with an 80% loan at 9% over 20 years:</p><table class="tbl"><thead><tr><th>Home type</th><th>EMI a month</th><th>20% down payment</th></tr></thead><tbody>' + "".join(f"<tr><td>{t['label']}</td><td>₹{emi(int(t['p_lo'] * 0.8), 9, 20):,}</td><td>{inr(int(t['p_lo'] * 0.2))}</td></tr>" for t in fit) + "</tbody></table>"
            f'<h2 id="headroom">How much room the budget leaves</h2><p>The lowest-priced {fit[0]["label"]} leaves about {inr(B - fit[0]["p_lo"])} of headroom under {bl}, which could cover parking, interiors or moving costs.' + (f' A home type that starts above the budget, such as the {nxt["label"]} from {inr(nxt["p_lo"])}, would need about {inr(nxt["p_lo"] - B)} more.' if (nxt := next((t for t in TYPES if t["p_lo"] > B), None)) else " Every home type at the project starts within this budget.") + '</p>'
            f'<h2 id="trap">Before you set the budget</h2>{li(["Ask for the full cost sheet and see which charges are included in the quoted price.", "Decide your maximum total, then work backwards.", "Keep a reserve for interiors and moving.", "Verify the RERA registration before paying any token."])}'
            f'<h2 id="more">More guides</h2>{siblings()}' + CTA)
    PAGES.append((f"flats-under-{bs}-in-{LOCS}", f"Flats Under {bl} in {LOC}: Home Options"[:60], f"What {bl} buys at {SHORT}: {len(fit)} home types, EMI, down payment and carpet area, with a price table and buyer checklist.", f"Flats Under {bl} in {LOC}: {SHORT}", f"What {bl} buys, EMI, down payment and carpet area.", body, "By budget"))

# ---------------------------------------------------------------- calculators
CALC_JS = """<script>
(function(){var $=function(i){return document.getElementById(i)};var f=function(n){return '\\u20b9'+Math.round(n).toLocaleString('en-IN')};
function emi(){var p=+$('c-price').value||0,d=+$('c-down').value||0,r=(+$('c-rate').value||0)/1200,n=(+$('c-years').value||0)*12;var loan=p*(1-d/100),e=r?loan*r*Math.pow(1+r,n)/(Math.pow(1+r,n)-1):loan/(n||1);
$('o-loan').textContent=f(loan);$('o-emi').textContent=f(e);$('o-int').textContent=f(e*n-loan);$('o-down').textContent=f(p*d/100);$('o-inc').textContent=f(e/0.4)}
function cost(){var t=0;['k-base','k-floor','k-park','k-club','k-stamp','k-reg','k-gst','k-other'].forEach(function(i){t+=+$(i).value||0});$('k-total').textContent=f(t);var a=+$('k-area').value||0;$('k-ps').textContent=a?f(t/a):'-'}
['c-price','c-down','c-rate','c-years'].forEach(function(i){if($(i))$(i).addEventListener('input',emi)});
['k-base','k-floor','k-park','k-club','k-stamp','k-reg','k-gst','k-other','k-area'].forEach(function(i){if($(i))$(i).addEventListener('input',cost)});
if($('c-price'))emi();if($('k-base'))cost();var s=$('c-pick');if(s)s.addEventListener('change',function(){if(this.value){$('c-price').value=this.value;emi()}});})();
</script>"""
CALC_CSS = '<style>.calc{display:grid;gap:14px;margin:18px 0;padding:18px;border:1px solid #d9dedc;border-radius:14px;background:#fff}.calc .cf{display:flex;flex-direction:column;gap:6px}.calc label{font-weight:600;font-size:15px}.calc input,.calc select{width:100%;padding:12px 14px;border:1px solid #b9c2bf;border-radius:10px;font-size:16px;background:#fff;color:#1b2523}.calc .out{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:6px 0 0}.calc .out>div{background:#f2f5f4;border-radius:12px;padding:14px}.calc .out dt{font-size:13px;color:#4a5855}.calc .out dd{margin:4px 0 0;font-weight:700;font-size:20px;color:#1b2523;overflow-wrap:anywhere}</style>'


def field(i, lab, val, step="1"):
    return f'<div class="cf"><label for="{i}">{lab}</label><input id="{i}" type="number" inputmode="decimal" min="0" step="{step}" value="{val}"></div>'


opts = '<option value="">Choose a home type to fill the price</option>' + "".join(f'<option value="{t["p_lo"]}">{t["label"]}: from {inr(t["p_lo"])}</option>' for t in TYPES)
t0 = TYPES[0]
emi_body = (CALC_CSS + '<h2 id="calc">Home loan EMI calculator</h2><p>Enter the price, down payment, interest rate and tenure. All numbers are illustrative; your bank\'s offer will differ.</p><form class="calc" onsubmit="return false"><div class="cf"><label for="c-pick">Start from a home type</label><select id="c-pick">' + opts + '</select></div>' +
            field("c-price", "Home price (₹)", t0["p_lo"], "1000") + field("c-down", "Down payment (%)", 20) + field("c-rate", "Interest rate (% a year)", 9, "0.05") + field("c-years", "Loan tenure (years)", 20) +
            '<dl class="out" aria-live="polite"><div><dt>Loan amount</dt><dd id="o-loan"></dd></div><div><dt>Monthly EMI</dt><dd id="o-emi"></dd></div><div><dt>Total interest</dt><dd id="o-int"></dd></div><div><dt>Down payment</dt><dd id="o-down"></dd></div><div><dt>Income at 40% EMI rule</dt><dd id="o-inc"></dd></div></dl></form>'
            '<p class="note">The 40% income figure is a common rule of thumb, not a lender decision. Maintenance, parking and other charges are not included.</p>'
            '<h2 id="formula">How the EMI is worked out</h2><p>The calculator uses the standard reducing-balance formula: EMI = P x r x (1 + r)^n / ((1 + r)^n - 1), where P is the loan amount, r is the monthly rate (yearly rate divided by 12 and by 100) and n is the number of monthly instalments. Banks may round differently, add processing fees or change the rate over time, so your bank\'s schedule is the one that counts.</p>'
            '<h2 id="how">How to use it</h2>' + li(["Start with the total payable from the cost sheet, not the base price.", "Try 8%, 9% and 10% to see how a rate change affects the EMI.", "Compare 15, 20 and 25 years: a longer tenure lowers the EMI but raises total interest."]) +
            f'<p>Related: {link("total-flat-cost-calculator", "total flat cost calculator")} and {link("flat-guides", "all flat guides")}.</p>' + CALC_JS + CTA)
PAGES.append(("home-loan-emi-calculator", f"Home Loan EMI Calculator for a {CITY} Flat"[:60], f"Free home loan EMI calculator for a new flat in {CITY}. Start from a {SHORT} home type and see EMI, total interest and the income needed.", f"Home Loan EMI Calculator: {SHORT}", "See your EMI, total interest and the income a lender may look for.", emi_body, "Calculator"))
cost_body = (CALC_CSS + '<h2 id="calc">Total flat cost calculator</h2><p>Add up everything on the cost sheet. We pre-fill only the lowest listed price, because stamp duty, registration, GST and other charges depend on your case and change over time. Type the amounts from your own cost sheet.</p><form class="calc" onsubmit="return false">' +
             field("k-base", "Base price (₹)", t0["p_lo"], "1000") + field("k-floor", "Floor rise and other add-ons (₹)", 0, "1000") + field("k-park", "Parking (₹)", 0, "1000") + field("k-club", "Club and amenity charges (₹)", 0, "1000") + field("k-stamp", "Stamp duty (₹)", 0, "1000") + field("k-reg", "Registration (₹)", 0, "1000") + field("k-gst", "GST where applicable (₹)", 0, "1000") + field("k-other", "Maintenance deposit and other charges (₹)", 0, "1000") + field("k-area", "Carpet area (sq ft)", t0["a_lo"]) +
             '<dl class="out" aria-live="polite"><div><dt>Total payable</dt><dd id="k-total"></dd></div><div><dt>Total per sq ft of carpet area</dt><dd id="k-ps"></dd></div></dl></form>'
             '<h2 id="items">What usually appears on a cost sheet</h2>' + li(["Base price: carpet (or saleable) area multiplied by the rate.", "Floor rise, view or corner premiums, if any.", "Parking, often charged separately.", "Club and amenity charges and a maintenance deposit.", "Stamp duty, registration and GST where applicable; rates change, so confirm current figures with a registered professional."]) +
             f'<p>Related: {link("home-loan-emi-calculator", "home loan EMI calculator")} and {link("flat-guides", "all flat guides")}.</p>' + CALC_JS + CTA)
PAGES.append(("total-flat-cost-calculator", "Total Flat Cost Calculator: Price Plus Charges"[:60], f"Add the base price, parking, club charges, stamp duty, registration, GST and deposits to see the total payable and the true price per sq ft of carpet area at {SHORT}.", f"Total Flat Cost Calculator: {SHORT}", "Add every line of the cost sheet and see the true price per sq ft.", cost_body, "Calculator"))


MORE = {
 "brochure": '<h2 id="digital">Floor plans and the cost sheet</h2><p>When you enquire, ask for the floor plan of the exact home type you want, not just the typical plan, and for the cost sheet for the unit and floor. Compare the carpet area on the plan with the figure on the price list. Differences between the brochure, the price list and the RERA registration are worth raising before you pay anything.</p>',
 "possession-date": '<h2 id="why">Why the declared date matters</h2><p>The date in the RERA registration is the one the developer commits to in law. Compare it with the stage of construction you see on site, and with how earlier projects by the same developer performed against their own declared dates. A project that is far from the declared stage on a site visit deserves a direct question in writing.</p><h2 id="agreement">Read the agreement clause</h2><p>The agreement for sale usually states the possession date and what happens if it is missed. Read that clause, and the clauses on force majeure and on changes to the plan, before you sign. If a clause is unclear, ask a property lawyer to explain it.</p>',
 "location-map": '<h2 id="future">Questions about the surroundings</h2>' + '<ul><li>Which roads will serve the project once all its towers are occupied?</li><li>Is public transport planned near the entrance?</li><li>What is being built on the adjacent plots?</li></ul><p>A confident sales team can answer these with specifics. If an answer is vague, check the municipal plans or ask residents of nearby buildings.</p>',
 "reviews-is-it-worth-buying": '<h2 id="visit">Talk to people who live there</h2><p>The most useful review of a developer is a conversation with residents of a completed project. Ask about build quality in the first two years, how quickly defects were fixed, how maintenance is run and whether promised amenities exist. Visit on a weekend evening, when residents are home and the common areas are in use.</p>',
 "site-visit-guide": '<h2 id="family">Bring the people who will live there</h2><p>Parents, partners and older children notice different things: the walk from the lift, the light in the bedroom, the noise at night. Ask each person to list two things they like and two they would change, and compare the lists on the way home.</p>',
 "carpet-area-vs-built-up-vs-super-built-up": '<h2 id="compare2">A quick comparison</h2><p>Imagine two projects each quoting ₹10,000 per sq ft. If one quotes on carpet area and the other on super built-up area, the second can be 25 to 35 percent cheaper per usable sq ft than it looks, or the other way round, depending on its loading. Only a carpet-to-carpet comparison tells you which is cheaper.</p><h2 id="rera">What RERA changed</h2><p>RERA requires developers to sell by carpet area and to state it in the agreement, which makes projects easier to compare than they used to be. Always read the carpet area figure in the agreement itself, not just the brochure.</p>',
 "home-loan-checklist-for-new-flat": '<h2 id="tips">Practical tips</h2><ul><li>Compare offers from at least three lenders, including the processing fee.</li><li>Ask about prepayment charges on a floating-rate loan.</li><li>Do not borrow more than you can service through a rate rise.</li></ul><p>Keep a reserve equal to several months of EMI, maintenance and rent, because a delay in possession means paying interest and rent together.</p>',
}

MORE["brochure"] += '<h2 id="mistakes">Common mistakes with brochures</h2><ul><li>Treating an artist\'s impression as a promise: a render can differ from what is built.</li><li>Missing the fine print on the price page, where inclusions and exclusions are listed.</li><li>Assuming every amenity opens at possession when some arrive in later phases.</li><li>Not asking for the version date, so a later "updated" brochure cannot be compared.</li></ul><p>A short note of what was promised verbally, with the date and the name of the person, saves arguments later.</p>'
MORE["possession-date"] += '<h2 id="questions">Questions to put in writing</h2><ol><li>What is the declared possession date for my tower, and has it been revised?</li><li>What is the stage of construction today, and what is the next milestone?</li><li>What happens to my payments if the date is missed?</li><li>Who confirms the occupation certificate, and when do you expect it?</li></ol><p>Keep the written answers with your booking papers. If the date matters to you, for example because your lease ends or a child starts school, say so before you pay, and ask for a payment plan that follows construction stages.</p>'
MORE["location-map"] += '<h2 id="test">A simple route test</h2><p>Pick the three places you will go most often: your workplace, a school or hospital, and a market. Open each on the map from the project, set the departure time you would really leave, and note the journey time at a weekday morning, a weekday evening and a weekend. Do it again on the day you visit. A route that looks short on a map can be slow at peak time, and the reverse is also true, so measure instead of assuming.</p><h2 id="everyday">Everyday needs</h2><p>List what you need within a short drive: a clinic, a pharmacy, a grocery store, a school and a bank. Find each on the map and check that the road to it is not one that floods or jams. Our locality guides on this site list what to check for the area.</p>'
MORE["reviews-is-it-worth-buying"] += '<h2 id="paper">Check the paperwork, not the promises</h2><p>Reviews can be written by anyone, so lean on documents. The RERA registration shows the promoter, the land and the declared dates. The draft agreement shows what you are really buying and what happens if either side fails. A cost sheet with every charge listed shows whether the headline price is honest. If a seller is uncomfortable with you checking these, that is information too.</p><h2 id="compare">Compare before you decide</h2><p>Put two other projects in the same area next to this one and compare carpet area, total payable, declared possession date and the developer\'s record. The right project is the one that wins on the facts you can verify, not the one with the best brochure.</p>'
MORE["site-visit-guide"] += '<h2 id="questions">Ten questions to take with you</h2><ol><li>What is the total payable for my unit, line by line?</li><li>What is the declared possession date for my tower?</li><li>Which amenities are ready at handover?</li><li>How many parking spaces are included?</li><li>What are the maintenance charges and what do they cover?</li><li>What are the payment stages and their triggers?</li><li>Can I see the draft agreement today?</li><li>What happens if I cancel after the token?</li><li>Who will maintain the buildings after handover?</li><li>Can you put the key promises in writing?</li></ol>'
MORE["carpet-area-vs-built-up-vs-super-built-up"] += '<h2 id="mistakes">Mistakes buyers make</h2><ul><li>Comparing a rate per sq ft on saleable area with a rate on carpet area.</li><li>Ignoring the loading: two projects with the same carpet area can differ by many sq ft of saleable area.</li><li>Forgetting that balconies and utility areas may or may not be counted.</li><li>Not asking for the RERA carpet area of the exact unit.</li></ul><p>When in doubt, ask for the carpet area of the unit on the agreement and divide the total payable by it. That single number, the total per sq ft of carpet area, is the fairest way to compare any two projects.</p>'
MORE["home-loan-checklist-for-new-flat"] += '<h2 id="questions">Questions for your bank</h2><ol><li>What interest rate and processing fee do you offer for my profile?</li><li>Is the project approved by your bank?</li><li>How are disbursements linked to construction stages?</li><li>What are the prepayment and foreclosure charges?</li><li>Can I add a co-applicant to raise eligibility?</li></ol><h2 id="credit">Keep your credit healthy</h2><p>Avoid taking new loans or missing card payments in the months before you apply. A higher score can mean a lower rate, which over twenty years is worth far more than a small discount on the flat.</p>'

# ---------------------------------------------------------------- topic pages
def topic(slug, title, desc, h1, dek, body, pill="Buyer guide"):
    key = slug[len(PFX) + 1:] if slug.startswith(PFX + "-") else slug
    PAGES.append((slug, title[:60], desc[:160], h1, dek, body + MORE.get(key, "") + CTA, pill))


topic(f"{PFX}-brochure", f"{SHORT} Brochure: What to Ask For", f"{SHORT} brochure: what a good brochure should show, and how to request the current brochure, cost sheet and floor plans.", f"{SHORT} Brochure", "What to ask for and how to check it.",
      f'<h2 id="overview">Getting the {NAME} brochure</h2><p>Send an enquiry from this site or use the Call and WhatsApp buttons, and the sales team will share the current brochure, cost sheet and floor plans. We do not host a brochure file here because details change with approvals.</p><h2 id="contents">What a good brochure should contain</h2>' + li(["Master plan showing towers, amenities and access roads.", "Typical floor plans with carpet area for each home type.", "Specifications: flooring, kitchen, bathrooms, doors, windows, lifts.", "The RERA registration number and possession date.", "Parking details and what is included in the quoted price."]) +
      '<h2 id="whyask">Why not rely on the brochure alone</h2><p>Brochures are designed to sell. Renders show the best light, and an amenity list may include items that open in later phases. Treat every claim as a question: where is it on the master plan, when does it open and is it in the price? Keep a copy of the version you were given, with the date, so that you can compare it with the agreement later.</p>'
      '<h2 id="verify">Check it against the paperwork</h2><p>Compare the brochure\'s areas and amenities with the RERA registration and the draft agreement, and ask for any difference to be explained in writing.</p>' + f'<p>See also {link("flat-guides", "all flat guides")} and {link("total-flat-cost-calculator", "the total cost calculator")}.</p>')
topic(f"{PFX}-possession-date", f"{SHORT} Possession Date: How to Verify", f"{SHORT} possession date: how to check the declared date on MahaRERA and what to ask about delays before you pay a token.", f"{SHORT} Possession Date", "How to verify the declared date and what to ask about delays.",
      f'<h2 id="overview">What matters about possession</h2><p>The date that matters is the one declared in the project\'s RERA registration. {K["rera_text"]} Marketing phrases such as "possession soon" are not binding.</p><h2 id="find">How to find the declared date</h2><ol><li>Search the project on the MahaRERA website using its registration number.</li><li>Open the project details and note the proposed completion date.</li><li>Check for any extension or revision recorded after registration.</li></ol>'
      '<h2 id="ask">Ask about delays</h2>' + li(["What compensation or interest applies if possession is late, as per the agreement?", "Will possession be tower-wise, and when does your tower complete?", "Which amenities will be ready at handover?", "When is the occupation certificate expected?"]) +
      '<h2 id="plan">Plan your finances around the date</h2><p>Until possession you may pay rent and, once disbursements begin, pre-EMI interest. A delay of a year can cost a family a large sum, so build a buffer into your plan and prefer construction-linked payment schedules that follow progress you can see.</p>' + f'<p>See also {link("home-loan-emi-calculator", "the EMI calculator")}.</p>')
lm = "".join(f'<li><a href="{maps(m)}" target="_blank" rel="noopener">{n}</a></li>' for n, m in K["landmarks"])
topic(f"{PFX}-location-map", f"{SHORT} Location and Map", f"Where is {SHORT}? {K['loc_full']}. Live map links, nearby places and how to test the route before you buy.", f"{SHORT} Location", f"{K['loc_full']}: live map links and how to test the route.",
      f'<h2 id="overview">Where is {NAME}</h2><p>{SHORT} is at {K["loc_full"]}. <a href="{maps(K["map_query"])}" target="_blank" rel="noopener">Open it on the live map</a>.</p><h2 id="near">Places to check on the map</h2><ul>{lm}</ul><p>We show no distances. Open each link, set your own departure time and read the travel time.</p>'
      '<h2 id="visit">Before you visit</h2>' + li(["Use the live map to plan the route and note landmarks.", "Visit at a weekday peak hour and on a weekend.", "Check the access road and how it joins the main roads."]) +
      '<h2 id="reading">Reading a location honestly</h2><p>A map shows where a project sits, not how it feels to live there. Check the roads at the hours you travel, find the nearest hospital, school and grocery store, and ask residents of nearby buildings about water supply, power cuts and traffic.</p>' + (f'<p>More: <a href="{LOCGUIDE}">living in {LOC}</a>.</p>' if LOCGUIDE else ""))
topic(f"{PFX}-reviews-is-it-worth-buying", f"{SHORT} Reviews: Is It Worth Buying?", f"Looking for {SHORT} reviews? How to judge the project and developer yourself: RERA, delivery record, resident visits, cost sheet and agreement.", f"{SHORT} Reviews", "How to judge the project and developer yourself.",
      f'<h2 id="overview">An honest note on reviews</h2><p>We publish no reviews or testimonials that we cannot verify. Here is how to form your own view of {NAME} and {DEV}.</p><h2 id="how">How to evaluate the project</h2><ol><li>Ask for a list of completed {DEV} projects and visit one. Talk to residents about build quality, maintenance and handover.</li><li>Look up the project and the developer on MahaRERA, including any complaints.</li><li>Read the agreement draft and ask a property lawyer to review it.</li><li>Compare the total cost sheet with two other projects in {LOC}.</li><li>Visit the site and the sales gallery, and check the access road.</li></ol>'
      '<h2 id="signs">Good signs and red flags</h2><p><strong>Good signs:</strong> a RERA number you can verify, a clear cost sheet, willingness to put promises in writing. <strong>Red flags:</strong> pressure to pay a large amount before the agreement, vague possession dates, refusing to share the draft agreement.</p>'
      f'<h2 id="questions">Questions to put to the developer</h2>' + li([f"How many projects has {DEV} delivered, and where?", "Were they delivered on the declared date?", "Who maintains the buildings after handover, and for how long?", "Have there been any legal disputes or complaints on any project?"]) + f'<p>See also {link(PFX + "-possession-date", "how to verify the possession date")}.</p>')
topic(f"{PFX}-site-visit-guide", f"{SHORT} Site Visit: What to Check", f"Planning a {SHORT} site visit? A checklist for the sales gallery, the site, the access road and the questions to ask before you pay.", f"{SHORT} Site Visit", "A checklist for the sales gallery and the site.",
      '<h2 id="overview">Before you go</h2><p>Book a visit through the enquiry form or the Call and WhatsApp buttons. Take your ID, your budget and a printed list of questions, and bring a family member who will help decide.</p><h2 id="gallery">At the sales gallery</h2>' + li(["See the model flat and note it is a sample, not the final fit-out.", "Ask for the cost sheet for the exact home and floor you want.", "Ask for the RERA number, floor plans and draft agreement.", "Ask about token terms and cancellation terms."]) +
      '<h2 id="site">At the site</h2>' + li(["Check the access road and how it joins the main roads.", "Look at the surroundings of the tower you prefer.", "Ask where amenities and parking will be.", "Check the state of construction of the tower you are considering."]) +
      '<h2 id="notes">Take notes and photographs</h2><p>Photograph every page of the cost sheet you are shown and note the name of the person who gave it. Write down any promise made verbally, then ask for it in writing. Visit a second time without the sales team, at a different hour.</p>' + f'<p>Then test your budget on the {link("home-loan-emi-calculator", "EMI calculator")}.</p>')
topic("carpet-area-vs-built-up-vs-super-built-up", "Carpet vs Built-up vs Super Built-up Area", f"Carpet area, built-up area and super built-up area explained, with an example from {SHORT}, and why carpet area is the fair way to compare.", f"Carpet vs Built-up vs Super Built-up Area: {SHORT}", "Why carpet area is the fair way to compare projects.",
      f'<h2 id="overview">Three areas, three numbers</h2><ul><li><strong>Carpet area:</strong> the usable floor area inside the walls.</li><li><strong>Built-up area:</strong> carpet area plus wall thickness and balconies, depending on the definition.</li><li><strong>Super built-up (saleable) area:</strong> built-up area plus a share of common areas such as lobbies and lifts.</li></ul><p>Under RERA, sale is defined by carpet area, which is why {NAME}\'s material lists carpet areas.</p>'.replace("</ul></ul>", "</ul>").replace("<ul><li><strong>Carpet", "<ul><li><strong>Carpet", 1) +
      f'<h2 id="example">Why it changes the rate</h2><p>A {t0["a_lo"]} sq ft carpet {t0["label"]} priced at {inr(t0["p_lo"])} works out to about ₹{round(t0["p_lo"] / t0["a_lo"], -1):,.0f} per sq ft of carpet area. If another project quotes a lower rate on super built-up area, the same flat could cost more per sq ft of carpet area. Always convert to carpet area before you compare.</p>'
      '<h2 id="ask">What to ask</h2>' + li(["Is the quoted rate per sq ft on carpet or saleable area?", "How much is the loading from carpet to saleable area?", "Are balconies and terraces counted in the carpet area?", "What is the RERA carpet area for this exact home?"]) +
      '<h2 id="check">Check on the floor plan</h2><p>Ask for a dimensioned plan and measure the main rooms. If the sum of the room areas is far below the stated carpet area, ask where the difference is.</p>' + f'<p>See also {link("flats-in-" + LOCS, "flats in " + LOC)}.</p>')
topic("home-loan-checklist-for-new-flat", "Home Loan for a New Flat: Documents and Eligibility", f"Home loan checklist for a new flat in {CITY}: documents, eligibility factors, EMI planning and what to ask your bank before booking at {SHORT}.", f"Home Loan for a New Flat: {SHORT}", "Documents, eligibility and EMI planning.",
      '<h2 id="overview">Before you book</h2><p>A loan decision depends on you and on the project. Ask your bank for an in-principle eligibility check before you pay a token, and ask whether the project is approved by the bank.</p><h2 id="docs">Documents banks usually ask for</h2>' + li(["Identity and address proof.", "Income proof: salary slips and bank statements, or ITRs for the self-employed.", "Bank statements for several months.", "The booking letter or agreement and the cost sheet.", "Details of existing loans and EMIs."]) +
      '<h2 id="factors">What affects eligibility</h2>' + li(["Monthly income and stability of employment.", "Existing EMIs and credit card dues.", "Credit score.", "Age and loan tenure.", "The share of the price you pay upfront."]) +
      '<h2 id="staged">How disbursement works on a new flat</h2><p>For an under-construction flat the bank usually pays the developer in stages tied to construction progress. You pay interest only on the amount disbursed until the last stage, and then the full EMI starts. Ask your bank and the developer to align the payment schedule with the construction stages.</p>' + f'<p>Test your numbers on the {link("home-loan-emi-calculator", "EMI calculator")}.</p>')

# ---------------------------------------------------------------- hub
hub_items = [(s, t, d) for s, t, d, h1, dek, b, p in PAGES]
hub_body = (f'<h2 id="overview">Flat guides for {SHORT}</h2><p>Home types, budgets, calculators and answers to the questions buyers ask before they book at {NAME}.</p>' +
            "<ul>" + "".join(f'<li>{link(s, t)}: {d}</li>' for s, t, d in hub_items) + "</ul>" + CTA)
PAGES.append(("flat-guides", f"Flat Guides: {SHORT}"[:60], f"Home types, budgets, EMI and cost calculators and buyer checklists for {SHORT}.", f"Flat Guides: {SHORT}", "Home types, budgets, calculators and buyer checklists.", hub_body, "Guides"))

# ---------------------------------------------------------------- write
import shutil
gf = os.path.join(ROOT, "scripts", "kwpages.generated.json")
prev = json.load(open(gf)) if os.path.exists(gf) else []
for old in prev:
    if old not in [p[0] for p in PAGES] and os.path.isdir(os.path.join(ROOT, old)):
        shutil.rmtree(os.path.join(ROOT, old))        # a page that is no longer generated is removed
json.dump([p[0] for p in PAGES], open(gf, "w"))
tpl = rf.template()
for slug, title, desc, h1, dek, body, pill in PAGES:
    if len(desc) > 160:
        desc = desc[:157].rstrip() + "..."
    body = re.sub(r'<table class="tbl">(.*?)</table>', r'<div class="tw"><table class="compare">\1</table></div>', body, flags=re.S)   # the sites' own table style
    page = rf.make_page(slug, title, desc, h1, dek, body, tpl)
    page = re.sub(r'(<span class="tag-pill">).*?(</span>)', lambda m: m.group(1) + pill + m.group(2), page, count=1, flags=re.S)
    rf.write(os.path.join(ROOT, slug, "index.html"), page)
print(f"kwpages: wrote {len(PAGES)} pages")
