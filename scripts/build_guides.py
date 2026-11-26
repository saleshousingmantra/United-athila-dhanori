#!/usr/bin/env python3
"""Build the guides section of unitedathiladhanori.com.

Run from the repository root:   python3 scripts/build_guides.py

Reads scripts/guides_schedule.json ("order" and "published"). Only published
guides are written, and hub pages, the HTML site map and sitemap.xml list only
published guides, so the live site never links to a page that is not there yet.
To publish the next guide: add its slug to "published", run this script, commit
and push to main.
"""
import json, os, re, html, urllib.parse, glob, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://unitedathiladhanori.com"
DATE = "2026-11-26"
PHONE = "+918007616636"
RERA = "PM1260002602534"
sched = json.load(open(os.path.join(ROOT, "scripts/guides_schedule.json")))

def cap(s): return s[0].upper() + s[1:]
def slugify(t): return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", t)).lower()).strip("-")
def mins(b): return max(2, round(len(re.sub(r"<[^>]+>", " ", b).split()) / 200))

def gmaps(name, area="Dhanori Pune"):
    q = urllib.parse.quote_plus(f"{name} {area}")
    return (f'<a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">View on Google Maps</a> · '
            f'<a href="https://www.google.com/maps/dir/?api=1&amp;origin=Dhanori+Jakat+Naka+Pune&amp;destination={q}" target="_blank" rel="noopener">Directions from Dhanori Jakat Naka</a>')

def table(rows, hdr=("Place", "Type", "Map")):
    t = f'<div class="tw"><table class="compare"><thead><tr><th>{hdr[0]}</th><th>{hdr[1]}</th><th>{hdr[2]}</th></tr></thead><tbody>'
    for n, ty, area in rows:
        t += f"<tr><td>{n}</td><td>{ty}</td><td>{gmaps(n, area)}</td></tr>"
    return t + "</tbody></table></div>"

SRC = ('<p><strong>How we compiled this guide:</strong> place names come from public listings and are a starting point. '
       'Distances and travel times change with traffic and route, so use the Google Maps links to check live directions, and confirm details '
       'directly with each place before you decide.</p>')
CTA_NOTE = '<p>Project details, pricing and floor plans for United Athila are on the <a href="{h}">home page</a>.</p>'

G = {}
# ------------------------------------------------------------------ buying guides
G["2-bhk-vs-2-5-bhk-vs-3-bhk"] = dict(cat="buying-guides", catname="Buying guide", img="towers-courtyard-view", imgw=1600,
  t="2 BHK vs 2.5 BHK vs 3 BHK: Which Fits You? | United Athila",
  h="2 BHK vs 2.5 BHK vs 3 BHK: which fits you",
  d="Compare 2, 2.5 and 3 BHK homes at United Athila, Dhanori, on carpet area, price and who each suits. A plain-language guide for Pune home buyers.",
  dek="Carpet areas, starting prices and who each layout suits, with numbers from United Athila, Dhanori.",
  alt="Towers and courtyard at United Athila, Dhanori, Pune",
  tk=["United Athila offers 2 BHK (779–843 sq ft carpet), 2.5 BHK (806–899) and 3 BHK (918–1,059).",
      "All-inclusive prices start around ₹84.58 L, ₹90.22 L and ₹99.63 L respectively, as per the current cost sheet.",
      "A 2.5 BHK adds a flexible room for work, a nursery or a guest.",
      "Choose by household size in five years, a comfortable EMI and how you will use the extra room."],
  body='''<p>United Athila, by United Landmarks LLP, offers three home types at Dhanori Central in East Pune. Picking between them is mostly a question of space, budget and how long you plan to stay. Here are the numbers and a simple way to decide.</p>
<h2>The three layouts at a glance</h2>
<div class="tw"><table class="compare"><thead><tr><th></th><th>2 BHK</th><th>2.5 BHK</th><th>3 BHK</th></tr></thead><tbody>
<tr><td>Carpet area</td><td>779 – 843 sq ft</td><td>806 – 899 sq ft</td><td>918 – 1,059 sq ft</td></tr>
<tr><td>All-inclusive price from</td><td>₹84.58 L</td><td>₹90.22 L</td><td>₹99.63 L</td></tr></tbody></table></div>
<p>All-inclusive prices include stamp duty, registration and GST as per the current cost sheet, and are subject to change.</p>
<h2>Who suits a 2 BHK</h2>
<ul><li>Couples and small families who want a well-planned home without paying for unused rooms.</li><li>First-time buyers who want a lower loan amount and EMI.</li><li>Investors planning to rent the home out.</li></ul>
<h2>What the half bedroom in a 2.5 BHK is for</h2>
<p>A 2.5 BHK adds a smaller room to the two bedrooms. Families use it as a home office, a nursery, a study or a guest room. It suits buyers who want more flexibility than a 2 BHK without the budget of a full 3 BHK.</p>
<h2>Who suits a 3 BHK</h2>
<ul><li>Families with children or parents living together who need a room for each.</li><li>Professionals who work from home and need a dedicated study.</li><li>Buyers planning to stay long term, because a third bedroom grows with the family.</li></ul>
<h2>A simple way to decide</h2>
<ol><li>List how many people will live in the home five years from now.</li><li>Set a comfortable EMI, then see which price band fits.</li><li>Decide whether you need a separate room for work or guests.</li><li>Compare the floor plans of the exact unit you are considering.</li></ol>
<p>For the full cost breakdown of each unit, see our guide on <a href="../how-to-read-a-cost-sheet/">how to read a cost sheet</a>, and read how <a href="../what-is-pre-launch-and-early-bird-pricing/">pre-launch pricing</a> works before you book.</p>''')

G["what-is-pre-launch-and-early-bird-pricing"] = dict(cat="buying-guides", catname="Buying guide", img="towers-facade", imgw=1600,
  t="What Is Pre-Launch and Early-Bird Pricing? | United Athila",
  h="What is pre-launch and early-bird pricing",
  d="What a pre-launch means when buying a flat, how early-bird pricing works, and what to check first, including the MahaRERA number, with United Athila, Dhanori.",
  dek="What pre-launch means, how early-bird offers work and what to verify before you pay.",
  alt="Tower facade at United Athila, Dhanori, Pune",
  tk=["Pre-launch means a project is offered to early buyers before the formal launch.",
      "Early-bird pricing is an introductory price that can change as the project moves forward.",
      "Always verify the MahaRERA registration (United Athila: PM1260002602534) on the official website.",
      "Get the cost sheet, payment terms and possession timeline in writing."],
  body=f'''<p>When a new project is called "pre-launch", it is being offered to a limited group of buyers before the full public launch. United Athila, Dhanori, is currently in pre-launch. This guide explains what that means for you.</p>
<h2>What pre-launch means</h2>
<p>A pre-launch lets buyers register interest and choose units early. Plans, specifications and prices are indicative and can change as approvals and sales progress. That is why every pre-launch price carries a note that it is subject to change.</p>
<h2>How early-bird pricing works</h2>
<p>An early-bird price is an introductory rate offered to the first buyers. It is usually available for a limited time or for a limited number of units. Always ask what exactly is covered, how long the offer lasts and what happens to the price afterwards.</p>
<h2>Check the RERA registration first</h2>
<p>In Maharashtra, projects must be registered with MahaRERA. United Athila's registration number is <strong>{RERA}</strong>. You can verify any project on the official site, <a href="https://maharera.maharashtra.gov.in/" target="_blank" rel="noopener">maharera.maharashtra.gov.in</a>, before paying anything.</p>
<h2>Questions to ask before you book</h2>
<ul><li>What is included in the all-inclusive price, and what is extra?</li><li>What is the payment schedule?</li><li>What is the expected possession timeline?</li><li>What are the terms if you decide to cancel?</li></ul>
<h2>Next steps</h2>
<p>Compare layouts in our guide to <a href="../2-bhk-vs-2-5-bhk-vs-3-bhk/">2, 2.5 and 3 BHK homes</a>, and see how a cost sheet adds up in <a href="../how-to-read-a-cost-sheet/">how to read a cost sheet</a>.</p>''')

G["how-to-read-a-cost-sheet"] = dict(cat="buying-guides", catname="Buying guide", img="pool-amenity-deck", imgw=1600,
  t="How to Read a Cost Sheet: Stamp Duty, GST | United Athila",
  h="How to read a cost sheet: stamp duty, registration and GST",
  d="How a flat's all-inclusive price is built: agreement value, stamp duty, registration and GST, with a worked example from United Athila, Dhanori.",
  dek="How agreement value, stamp duty, registration and GST add up to the all-inclusive price.",
  alt="Pool and amenity deck at United Athila, Dhanori, Pune",
  tk=["The all-inclusive price is the agreement value plus stamp duty, registration and GST.",
      "United Athila's current cost sheet uses stamp duty at 7%, registration of ₹30,000 and GST at 5%.",
      "Example: an agreement value of ₹75,25,000 gives a total of ₹84,58,000.",
      "Rates and charges can change, so confirm the latest cost sheet in writing."],
  body='''<p>A cost sheet breaks the price of a flat into its parts. Reading it properly helps you compare projects fairly and plan your budget. Here is how the pieces fit together, using the current cost sheet for United Athila, Dhanori.</p>
<h2>The parts of a cost sheet</h2>
<ul><li><strong>Agreement value:</strong> the price of the flat as written in your agreement.</li><li><strong>Stamp duty:</strong> a government charge on the agreement. The current cost sheet uses 7%.</li><li><strong>Registration:</strong> a fixed registration charge. The current cost sheet shows ₹30,000.</li><li><strong>GST:</strong> shown at 5% in the current cost sheet.</li></ul>
<h2>A worked example</h2>
<div class="tw"><table class="compare"><thead><tr><th>Item</th><th>Amount</th></tr></thead><tbody>
<tr><td>Agreement value (2 BHK, 779 sq ft carpet)</td><td>₹75,25,000</td></tr><tr><td>Stamp duty (7%)</td><td>₹5,26,750</td></tr>
<tr><td>Registration</td><td>₹30,000</td></tr><tr><td>GST (5%)</td><td>₹3,76,250</td></tr><tr><td><strong>All-inclusive total</strong></td><td><strong>₹84,58,000</strong></td></tr></tbody></table></div>
<p>These figures are from the indicative cost sheet for the 779 sq ft 2 BHK. Larger units follow the same method with a higher agreement value.</p>
<h2>What to check</h2>
<ol><li>Is the price all-inclusive of stamp duty, registration and GST?</li><li>Are maintenance, parking and club charges included or extra?</li><li>Is the carpet area stated, and does it match the plan?</li><li>Is the payment schedule written in the agreement?</li></ol>
<p>Prices are indicative and subject to change as per the agreement. Read more about pricing stages in our guide to <a href="../what-is-pre-launch-and-early-bird-pricing/">pre-launch and early-bird pricing</a>.</p>''')

# ------------------------------------------------------------------ locality guides
G["living-in-dhanori-pune"] = dict(cat="locality", catname="Locality guide", img="towers-courtyard-view", imgw=1600,
  t="Living in Dhanori, Pune: Locality Overview | United Athila",
  h="Living in Dhanori, Pune: a locality overview",
  d="Where Dhanori is, what is nearby and what daily life looks like in this East Pune locality. A plain overview for home buyers, with Google Maps links.",
  dek="Where Dhanori is in East Pune, what is close by and how to check it yourself on Google Maps.",
  alt="Landscaped towers at United Athila, Dhanori, Pune",
  tk=["Dhanori is a residential locality in the north-east of Pune, near Viman Nagar, Lohegaon and Yerwada.",
      "Public listings put Pune Airport roughly 4 to 5 km away, and Ramwadi is the nearest operating metro station.",
      "Pune Railway Station is approximately 9 km from the project.",
      "Use the Google Maps links to check live distance and travel time."],
  body=f'''<p>Dhanori is a residential locality in the north-east of Pune. It sits close to Viman Nagar, Lohegaon, Yerwada, Vishrantwadi and Kalyani Nagar. United Athila, by United Landmarks LLP, is at Dhanori Central, Survey No. 6, Hissa No. 2, Dhanori, Pune 411015.</p>
<h2>Where Dhanori is</h2>
<p>The project is reached by 24 m and 30 m wide roads. Well-known landmarks nearby include Dhanori Jakat Naka, Porwal Road, Goodwill Square, Dhanori Road, Dhanori–Lohegaon Road and the Pune Airport Road.</p>
<h2>Key places at a glance</h2>
<div class="tw"><table class="compare"><thead><tr><th>Place</th><th>Approx. distance</th><th>Map</th></tr></thead><tbody>
<tr><td>Pune International Airport</td><td>about 4–5 km (listings vary)</td><td>{gmaps("Pune International Airport", "Pune")}</td></tr>
<tr><td>Ramwadi Metro Station</td><td>nearest operating metro</td><td>{gmaps("Ramwadi Metro Station", "Pune")}</td></tr>
<tr><td>Pune Railway Station</td><td>about 9 km</td><td>{gmaps("Pune Railway Station", "Pune")}</td></tr>
<tr><td>Viman Nagar</td><td>neighbouring locality</td><td>{gmaps("Viman Nagar", "Pune")}</td></tr>
<tr><td>Kharadi</td><td>IT and business hub nearby</td><td>{gmaps("Kharadi", "Pune")}</td></tr></tbody></table></div>
<h2>Everyday needs</h2>
<p>Read our guides to <a href="../schools-near-dhanori/">schools near Dhanori</a> and <a href="../hospitals-near-dhanori/">hospitals near Dhanori</a>, and to <a href="../roads-metro-and-airport-near-dhanori/">roads, metro and the airport</a>.</p>
<h2>About the project</h2>
<p>United Athila spans 4.25 acres with over 700 planned homes and shops across Towers G, H, I and J, next to the upcoming 108-acre Dhanori Central development. See the <a href="../../../#overview">project overview</a> and <a href="../../../#location">location details</a>.</p>
{SRC}''')

G["schools-near-dhanori"] = dict(cat="locality", catname="Locality guide", img="towers-courtyard-view", imgw=1600,
  t="Schools Near Dhanori, Pune: Local Guide | United Athila",
  h="Schools near Dhanori, Pune",
  d="CBSE and ICSE schools listed in Dhanori and nearby Lohegaon, Pune, with Google Maps links and a checklist for choosing the right school.",
  dek="CBSE and ICSE schools listed in Dhanori and Lohegaon, with map links and a checklist.",
  alt="Landscaped courtyard and towers at United Athila, Dhanori",
  tk=["Public listings show CBSE and ICSE schools in Dhanori and neighbouring Lohegaon.",
      "Check board, fees, bus routes and admission dates directly with each school.",
      "Use the Directions links to see the route from Dhanori Jakat Naka.",
      "Visit in person before deciding."],
  body=f'''<p>Finding the right school is high on every family's list. Public listings show a range of CBSE and ICSE schools in Dhanori and in nearby Lohegaon. Here are the names we found, with Google Maps links so you can check each one.</p>
<h2>Schools listed in Dhanori</h2>
{table([("Pragatti English Medium School","School, Dhanori–Lohegaon Road","Dhanori Pune"),("Pragatti International School","CBSE school, Madhav Nagar","Dhanori Pune"),("Neuron Labs School","CBSE school, Dhanori–Lohegaon Road","Dhanori Pune"),("Proxima International School","ICSE co-ed school","Dhanori Pune"),("Dr. Mar Theophilus School","ICSE school","Dhanori Pune"),("Akansha School","CBSE co-ed school","Dhanori Pune")])}
<h2>Schools listed in nearby Lohegaon</h2>
{table([("Kaveri International School","School, Vadgaon Shinde Road","Lohegaon Pune"),("Mount St. Patrick Academy","ICSE school","Lohegaon Pune"),("Sanskar Public School","CBSE school","Lohegaon Pune")])}
<h2>How to choose a school</h2>
<ol><li><strong>Board and curriculum:</strong> confirm CBSE, ICSE, State or international.</li><li><strong>Distance and transport:</strong> check the Directions link and ask about school bus routes.</li><li><strong>Fees and admission dates:</strong> these change each year, so ask the school office.</li><li><strong>Visit in person:</strong> see classrooms, playgrounds and safety arrangements.</li></ol>
<h2>More about the area</h2>
<p>Read the <a href="../living-in-dhanori-pune/">Dhanori locality overview</a> for key distances.</p>
{SRC}''')

G["hospitals-near-dhanori"] = dict(cat="locality", catname="Locality guide", img="pool-amenity-deck", imgw=1600,
  t="Hospitals Near Dhanori, Pune: Local Guide | United Athila",
  h="Hospitals and clinics near Dhanori, Pune",
  d="Hospitals and clinics listed in Dhanori, Lohegaon and nearby areas of Pune, with Google Maps links and what to check before you rely on one.",
  dek="Hospitals and clinics listed around Dhanori and Lohegaon, with map links and what to check first.",
  alt="Pool and amenity deck at United Athila, Dhanori",
  tk=["Hospitals and clinics are listed in Dhanori and neighbouring Lohegaon.",
      "Larger hospitals in Kharadi and on Nagar Road are reachable by road.",
      "Specialities, emergency cover and insurance vary, so confirm by phone.",
      "Use the Directions links to check the route from Dhanori Jakat Naka."],
  body=f'''<p>Healthcare nearby gives families peace of mind. Public listings show hospitals, nursing homes and clinics around Dhanori and Lohegaon. Here is what we found, with Google Maps links for each.</p>
<h2>Hospitals and clinics listed nearby</h2>
{table([("Orchid Speciality Hospital","Hospital, Porwal Road, near Dhanori Jakat Naka","Lohegaon Pune"),("Sparsh Orthopaedic &amp; General Hospital","Hospital, Dhanori–Lohegaon Road","Lohegaon Pune"),("Sai Shraddha Health Care Center","Health centre, near Jakat Naka","Lohegaon Pune"),("Manipal Clinics Dhanori","Clinic","Dhanori Pune"),("CT Nursing Home","Nursing home, Dhanori Road","Dhanori Pune"),("Vaibhav Nursing Home","Nursing home, Dhanori Road","Dhanori Pune")])}
<h2>Larger hospitals within reach</h2>
{table([("Manipal Hospital, Kharadi","Large hospital","Kharadi Pune"),("Sahyadri Super Speciality Hospital","Super speciality hospital, Nagar Road","Nagar Road Pune")])}
<h2>What to check before you rely on a hospital</h2>
<ul><li>Is the emergency department open 24x7, and is there an ICU?</li><li>Which specialists are available, and on which days?</li><li>Does the hospital accept your health insurance and offer cashless claims?</li><li>Does it run an ambulance service?</li></ul>
<h2>More about the area</h2>
<p>See the <a href="../living-in-dhanori-pune/">Dhanori locality overview</a> and our guide to <a href="../roads-metro-and-airport-near-dhanori/">roads, metro and the airport</a>.</p>
{SRC}''')

G["roads-metro-and-airport-near-dhanori"] = dict(cat="locality", catname="Locality guide", img="towers-facade", imgw=1600,
  t="Roads, Metro and Airport Near Dhanori, Pune | United Athila",
  h="Roads, metro and airport near Dhanori, Pune",
  d="How Dhanori connects by road, metro and air: Dhanori Jakat Naka, Porwal Road, Ramwadi Metro and Pune Airport, with Google Maps links for live routes.",
  dek="How Dhanori connects by road, metro and air, with Google Maps links for live routes.",
  alt="Tower facade at United Athila, Dhanori, Pune",
  tk=["The project is reached by 24 m and 30 m wide roads.",
      "Public listings put Pune Airport roughly 4 to 5 km away.",
      "Ramwadi is the nearest operating metro station; a direct airport metro link is proposed, not operating.",
      "Pune Railway Station is approximately 9 km away."],
  body=f'''<p>Connectivity is one of the main reasons buyers look at East Pune. This guide covers the main roads, the metro and the airport around Dhanori, with Google Maps links so you can check live routes.</p>
<h2>Roads</h2>
<p>United Athila at Dhanori Central has access via 24 m and 30 m wide roads. Nearby landmarks include Dhanori Jakat Naka, Porwal Road, Dhanori Road, Dhanori–Lohegaon Road and the Pune Airport Road. Open the Directions links for live travel time from Dhanori Jakat Naka.</p>
<h2>Metro</h2>
<p>Ramwadi Metro Station is the nearest operating station. A direct metro link to the airport has been proposed, but it is a proposal, not an operating line. Confirm the current status with Pune Metro before you rely on it.</p>
<h2>Airport and railway</h2>
{table([("Pune International Airport","About 4–5 km (listings vary)","Pune"),("Ramwadi Metro Station","Nearest operating metro","Pune"),("Pune Railway Station","About 9 km","Pune")], ("Place","Distance / note","Map"))}
<h2>Plan your own route</h2>
<p>Try the <a href="https://www.google.com/maps/dir/?api=1&amp;origin=Dhanori+Jakat+Naka+Pune&amp;destination=Pune+International+Airport" target="_blank" rel="noopener">route from Dhanori Jakat Naka to Pune Airport</a> at your usual travel time. For more about the area, read the <a href="../living-in-dhanori-pune/">Dhanori locality overview</a>.</p>
{SRC}''')

# ------------------------------------------------------------------ build
ORDER = [s for s in sched["order"] if s in G]
PUB = [s for s in ORDER if s in sched["published"]]
CATS = {"buying-guides": "Buying guides", "locality": "Locality guides"}
IMG = {"towers-courtyard-view": ("towers-courtyard-view-thumb", 640, 401), "towers-facade": ("towers-facade-md", 900, 707), "pool-amenity-deck": ("pool-amenity-deck-thumb", 640, 327)}
ICON_CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'

def rel(depth): return "../" * depth

def head(title, desc, path, ld, depth, extra=""):
    p = rel(depth)
    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{URL}{path}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0d4a42">
<meta property="og:type" content="{'article' if extra=='article' else 'website'}">
<meta property="og:locale" content="en_IN">
<meta property="og:site_name" content="United Athila, Dhanori">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{URL}{path}">
<meta property="og:image" content="{URL}/images/og-image.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="United Athila, Dhanori, Pune: residential project by United Landmarks LLP">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{p}favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="{p}images/logo/favicon.svg">
<link rel="apple-touch-icon" href="{p}images/apple-touch-icon.png">
<link rel="manifest" href="{p}manifest.webmanifest">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{p}fonts/montserrat-variable.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{p}fonts/inter-variable.woff2">
<link rel="stylesheet" href="{p}css/style.css">
<link rel="stylesheet" href="{p}css/blog.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
<body class="blog">
<div id="rp" aria-hidden="true"></div>
<header class="site-header nav">
<div class="container header-inner">
<a href="{p}" class="brand" aria-label="United Athila, Dhanori home"><img class="brand-logo" src="{p}images/logo/united-athila-logo-horizontal.svg" width="390" height="120" alt="United Athila"></a>
<nav class="main-nav" id="mainNav" aria-label="Primary"><ul>
<li><a href="{p}">Home</a></li><li><a href="{p}blog/" aria-current="page">Guides</a></li><li><a href="{p}#configurations">Pricing</a></li><li><a href="{p}#floor-plans">Floor Plans</a></li><li><a href="{p}#location">Location</a></li><li><a href="{p}#contact">Contact</a></li>
</ul></nav>
<a href="tel:{PHONE}" class="call-btn" aria-label="Call now"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg><span>Call Now</span></a>
<button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mainNav"><span></span><span></span><span></span></button>
</div></header>
'''

def foot(depth):
    p = rel(depth)
    links = f'<a href="{p}">Home</a><a href="{p}blog/">Guides</a><a href="{p}sitemap/">Site map</a><a href="{p}#configurations">Pricing</a><a href="{p}#floor-plans">Floor Plans</a><a href="{p}#location">Location</a>'
    return f'''<button id="toTop" type="button" aria-label="Back to top"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button><div id="toast" role="status"></div>
<footer class="site-footer"><div class="container footer-inner">
<img class="footer-logo" src="{p}images/logo/united-athila-logo-gold.svg" width="600" height="420" loading="lazy" alt="United Athila logo">
<p class="footer-tag">by United Landmarks LLP</p>
<p class="footer-loc">Survey No. 6, Hissa No. 2, Dhanori, Pune 411015</p>
<span class="footer-rule" aria-hidden="true"></span>
<nav class="footer-links" aria-label="Footer">{links}</nav>
<a class="footer-rera" href="https://maharera.maharashtra.gov.in/" target="_blank" rel="noopener"><img src="{p}images/rera-qr.svg" width="56" height="56" decoding="async" alt="QR code for MahaRERA registration number {RERA}"><span><small>MahaRERA Reg. No.</small><strong>{RERA}</strong><small class="rera-site">maharera.maharashtra.gov.in</small></span></a>
<p class="disclaimer"><strong>Disclaimer:</strong> Information in these guides is indicative and for general guidance only. Plans, specifications, amenities and prices are subject to change as per approvals. Map links and distances are approximate.</p>
<p class="copy">© 2026 United Landmarks LLP. All rights reserved.</p>
</div></footer>
<script defer src="{p}js/blog.js"></script>
</body></html>'''

def bc(items): return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": URL + q} for i, (n, q) in enumerate(items)]}

def card(s, depth):
    g = G[s]; p = rel(depth); im, w, h = IMG[g["img"]]
    return (f'<a class="gcard" href="{p}blog/{g["cat"]}/{s}/" data-title="{html.escape(g["h"])}" data-cat="{g["cat"]}"><div class="im"><img src="{p}images/gallery/{im}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{g["alt"]}"></div>'
            f'<div class="tx"><small>{g["catname"]}</small><h3>{cap(g["h"])}</h3><p>{g["dek"]}</p><div class="ft"><span>{mins(g["body"])} min read</span><em>Read guide →</em></div></div></a>')

def guide_page(s):
    g = G[s]; depth = 3; p = rel(depth); path = f"/blog/{g['cat']}/{s}/"
    body = g["body"]
    for u in G:  # never link to a guide that is not published yet
        if u not in PUB: body = re.sub(r'<a href="(?:\.\./)+%s/">(.*?)</a>' % re.escape(u), r"\1", body)
    heads = re.findall(r"<h2>(.*?)</h2>", body)
    for h in heads: body = body.replace(f"<h2>{h}</h2>", f'<h2 id="{slugify(h)}">{h}</h2>', 1)
    toc = "".join(f'<li><a href="#{slugify(h)}">{h}</a></li>' for h in heads)
    m = mins(body)
    others = [o for o in PUB if o != s and G[o]["cat"] == g["cat"]] + [o for o in PUB if o != s and G[o]["cat"] != g["cat"]]
    relc = "".join(card(o, depth) for o in others[:2])
    i = PUB.index(s); prev = PUB[i - 1] if i > 0 else None; nxt = PUB[i + 1] if i < len(PUB) - 1 else None
    pn = (f'<a class="prev" href="{p}blog/{G[prev]["cat"]}/{prev}/"><small>← Previous guide</small><b>{cap(G[prev]["h"])}</b></a>' if prev else "<span></span>") + \
         (f'<a class="next" href="{p}blog/{G[nxt]["cat"]}/{nxt}/"><small>Next guide →</small><b>{cap(G[nxt]["h"])}</b></a>' if nxt else "<span></span>")
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": g["h"], "description": g["d"], "datePublished": DATE, "dateModified": DATE, "timeRequired": f"PT{m}M", "inLanguage": "en-IN",
         "articleSection": CATS[g["cat"]], "image": URL + "/images/og-image.jpg", "mainEntityOfPage": URL + path,
         "author": {"@type": "Organization", "name": "United Landmarks LLP"},
         "publisher": {"@type": "Organization", "name": "United Landmarks LLP", "logo": {"@type": "ImageObject", "url": URL + "/images/icon-512.png"}}},
        bc([("Home", "/"), ("Guides", "/blog/"), (CATS[g["cat"]], f"/blog/{g['cat']}/"), (g["h"], path)])]}
    im = g["img"]
    page = head(g["t"], g["d"], path, ld, depth, "article") + f'''<section class="bhero"><img src="{p}images/gallery/{im}-md.webp" srcset="{p}images/gallery/{im}-md.webp 960w, {p}images/gallery/{im}.webp {g["imgw"]}w" sizes="100vw" width="1600" height="900" fetchpriority="high" decoding="async" alt="{g["alt"]}">
<div class="container"><p class="crumbs"><a href="{p}">Home</a> › <a href="{p}blog/">Guides</a> › <a href="{p}blog/{g["cat"]}/">{CATS[g["cat"]]}</a></p>
<span class="tag-pill">{g["catname"]}</span><h1>{cap(g["h"])}</h1><p class="dek">{g["dek"]}</p>
<div class="metarow"><span>{ICON_CLOCK} {m} min read</span><span>Updated {DATE}</span><span>United Athila, Dhanori</span><button type="button" class="copybtn" data-copy>Copy link</button></div></div></section>
<div class="post-layout container"><article class="post-body">
<div class="takeaways"><h2>Key takeaways</h2><ul>{"".join(f"<li>{t}</li>" for t in g["tk"])}</ul></div>
{body}
<h2 class="relh">Related guides</h2><div class="gcards two">{relc}</div>
<div class="pn">{pn}</div></article>
<aside class="side"><details class="toc"><summary>On this page</summary><ol>{toc}</ol></details>
<div class="sidecta"><h3>Interested in United Athila?</h3><p>Get the early-bird price, cost sheet and floor plans from our sales team.</p>
<a class="btn btn-gold" href="{p}#contact">Get price &amp; brochure</a><a class="btn btn-outline-light" href="tel:{PHONE}">Call Now</a></div></aside></div>
''' + foot(depth)
    out = os.path.join(ROOT, f"blog/{g['cat']}/{s}/index.html"); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)

def list_page(depth, path, title, desc, h1, dek, crumbs, slugs, name, search=True, intro=""):
    p = rel(depth)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": name, "url": URL + path, "hasPart": [{"@type": "BlogPosting", "headline": G[s]["h"], "url": f"{URL}/blog/{G[s]['cat']}/{s}/"} for s in slugs]},
        bc(crumbs)]}
    chips = '<button type="button" class="on" data-cat="all">All guides</button>' + "".join(f'<button type="button" data-cat="{c}">{n}</button>' for c, n in CATS.items() if any(G[s]["cat"] == c for s in slugs)) if search else ""
    box = f'<label class="search"><span class="sr-only">Search guides</span><input id="q" type="search" placeholder="Search guides, e.g. pricing, schools, metro" autocomplete="off"></label>' if search else ""
    crumb_html = " › ".join([f'<a href="{p}{q.strip("/")+"/" if q.strip("/") else ""}">{n}</a>' for n, q in crumbs[:-1]] + [crumbs[-1][0]])
    page = head(title, desc, path, ld, depth) + f'''<section class="bhero"><img src="{p}images/gallery/towers-courtyard-view-md.webp" srcset="{p}images/gallery/towers-courtyard-view-md.webp 960w, {p}images/gallery/towers-courtyard-view.webp 1600w" sizes="100vw" width="1600" height="1001" fetchpriority="high" decoding="async" alt="Towers and courtyard at United Athila, Dhanori, Pune">
<div class="container"><p class="crumbs">{crumb_html}</p><h1>{h1}</h1><p class="dek">{dek}</p>{box}</div></section>
<main class="container listing">
{intro}{('<div class="chips2" role="group" aria-label="Filter guides">' + chips + "</div>") if search else ""}<p class="count" aria-live="polite"></p>
<div class="gcards">{"".join(card(s, depth) for s in slugs)}</div>
<div class="empty">No guides match your search. Try a different word.</div>
<div class="band"><div><h2>Interested in United Athila?</h2><p>Get the early-bird price, cost sheet and floor plans.</p></div><div class="acts"><a class="btn btn-gold" href="{p}#contact">Get price &amp; brochure</a><a class="btn btn-outline-light" href="tel:{PHONE}">Call Now</a></div></div>
</main>''' + foot(depth)
    out = os.path.join(ROOT, path.strip("/"), "index.html"); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)

def sitemap_page():
    p = rel(1)
    sec = lambda t, items: f'<section><h2>{t}</h2><ul>' + "".join(f'<li><a href="{h}">{n}</a></li>' for h, n in items) + "</ul></section>"
    main = [(p, "United Athila, Dhanori: home page"), (p + "#configurations", "2, 2.5 & 3 BHK pricing"), (p + "#floor-plans", "Floor plans"), (p + "#amenities", "Amenities"), (p + "#location", "Location: Dhanori, Pune"), (p + "#faq", "FAQs"), (p + "#contact", "Contact and site visits")]
    gl = [(p + "blog/", "All guides")]
    for c, n in CATS.items():
        ss = [s for s in PUB if G[s]["cat"] == c]
        if ss: gl.append((f"{p}blog/{c}/", n))
    bgs = [(f"{p}blog/{G[s]['cat']}/{s}/", cap(G[s]["h"])) for s in PUB]
    ld = {"@context": "https://schema.org", "@graph": [{"@type": "WebPage", "name": "Site map", "url": URL + "/sitemap/"}, bc([("Home", "/"), ("Site map", "/sitemap/")])]}
    page = head("Site Map | United Athila, Dhanori", "Site map of United Athila, Dhanori, Pune: the project page, floor plans, pricing, FAQs and every buying and locality guide in one place.", "/sitemap/", ld, 1) + f'''<section class="bhero"><img src="{p}images/gallery/towers-courtyard-view-md.webp" width="960" height="601" fetchpriority="high" decoding="async" alt="Towers and courtyard at United Athila, Dhanori, Pune">
<div class="container"><p class="crumbs"><a href="{p}">Home</a> › Site map</p><h1>Site map</h1><p class="dek">Every page of United Athila, Dhanori in one place.</p></div></section>
<main class="container listing"><div class="smap">{sec("United Athila, Dhanori", main)}{sec("Guides", gl)}{sec("All guide pages", bgs)}</div></main>''' + foot(1)
    os.makedirs(os.path.join(ROOT, "sitemap"), exist_ok=True)
    open(os.path.join(ROOT, "sitemap/index.html"), "w", encoding="utf-8").write(page)

# clean old generated guide pages that are not published
for d in glob.glob(os.path.join(ROOT, "blog/*/*/")):
    if os.path.basename(d.rstrip("/")) not in PUB: shutil.rmtree(d)
for c in CATS:
    d = os.path.join(ROOT, "blog", c)
    if os.path.isdir(d) and not any(G[s]["cat"] == c for s in PUB):
        shutil.rmtree(d)
for s in PUB: guide_page(s)
list_page(1, "/blog/", "Guides for Dhanori Home Buyers | United Athila", "Guides for Dhanori, Pune home buyers from United Athila: 2, 2.5 and 3 BHK layouts, pre-launch pricing, cost sheets and Dhanori locality guides.",
          "Guides for Dhanori home buyers", "Plain-language guides on buying a home in Dhanori, Pune. Search or filter by topic.", [("Home", "/"), ("Guides", "/blog/")], PUB, "United Athila guides")
for c, n in CATS.items():
    ss = [s for s in PUB if G[s]["cat"] == c]
    if not ss: continue
    intros = {"buying-guides": "Buying a home is a big decision, and terms like pre-launch, early-bird pricing and cost sheets can be confusing. These guides explain the basics in plain language, with examples from United Athila in Dhanori, so you can compare options before you book a site visit.",
              "locality": "Choosing a home is about more than the flat itself. These guides cover the neighbourhood around United Athila in Dhanori: schools, hospitals, roads, the metro and the airport. Every place links to Google Maps so you can check live distance and travel time before you decide."}
    list_page(2, f"/blog/{c}/", f"{n} for Dhanori Home Buyers | United Athila" if c == "buying-guides" else "Dhanori Locality Guides | United Athila",
              ("Buying guides for Dhanori, Pune: compare 2, 2.5 and 3 BHK homes, understand pre-launch pricing and learn how a cost sheet adds up." if c == "buying-guides" else "Locality guides for Dhanori, Pune: schools, hospitals, roads, metro and the airport near United Athila, with Google Maps links for live distances."),
              n, "Clear answers before you buy a new home in Dhanori." if c == "buying-guides" else "Schools, hospitals, roads and transport around Dhanori, with Google Maps links.",
              [("Home", "/"), ("Guides", "/blog/"), (n, f"/blog/{c}/")], ss, n, search=False, intro=f'<p class="catintro">{intros[c]}</p>')
sitemap_page()

# sitemap.xml
urls = ["/", "/blog/", "/sitemap/"] + [f"/blog/{c}/" for c in CATS if any(G[s]["cat"] == c for s in PUB)] + [f"/blog/{G[s]['cat']}/{s}/" for s in PUB]
old = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
home_block = re.search(r"<url>\s*<loc>https://unitedathiladhanori\.com/</loc>.*?</url>", old, re.S).group(0)
xml = old[:old.index("<url>")] + home_block + "\n" + "".join(f"  <url><loc>{URL}{u}</loc><lastmod>{DATE}</lastmod></url>\n" for u in urls[1:]) + "</urlset>\n"
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)
print("published:", PUB, "| held back:", [s for s in ORDER if s not in PUB], "| sitemap urls:", len(urls))
