# United Athila, Dhanori (by United Landmarks LLP) landing page

Static site, no build step. Upload the whole folder to any host (Netlify, Vercel, cPanel, S3).

```
index.html            landing page (SEO meta, Open Graph, Twitter, JSON-LD schema)
thank-you/index.html  page form.js redirects to after a successful enquiry (noindex)
css/style.css         mobile-first styles (768px tablet, 1024px desktop)
js/config.js          Supabase keys, project / RM details, lead-source capture (your file, adapted)
js/form.js            validation + Supabase insert + thank-you redirect (your file, adapted)
js/app.js             menu, progress bar, reveal, counters, lightbox, enquiry popup (your file, adapted)
js/extras.js          floor-plan tabs, lazy Google map, back-to-top
images/               WebP images from the PDFs, OG image, icons
robots.txt, sitemap.xml, manifest.webmanifest
```

## Before going live
1. The site URL is `https://unitedathiladhanori.com` (canonical, Open Graph, schema.org, robots.txt, sitemap.xml). If the domain changes, replace it in index.html, thank-you, robots.txt and sitemap.xml.
2. Set `DEFAULT_MANAGER_EMAIL` in `js/config.js` to the RM who should receive leads.
3. Confirm the amenity list and the map pin coordinates (18.5935, 73.9133 is approximate for Dhanori).

## 2026-11-27 upgrade
`scripts/retrofit.py` applies the Ceratec-era upgrades to the built site (keywords/geo/ICBM meta, About, Privacy and Cookie pages, footer links and consent line, noscript form fallback, hero reveal removal, accessibility and contrast fixes, honest sitemap `lastmod` in `scripts/lastmod.json`, `llms.txt`, caching and security headers). **Run `python3 scripts/retrofit.py .` after `python3 scripts/build_guides.py`** so regenerated guide pages keep the fixes. Then run `python3 scripts/audit_seo.py . https://unitedathiladhanori.com` and `python3 scripts/audit_deep.py .` (both must pass).

TODO: have the policy pages reviewed by a lawyer; add the operator's registered name and contact details; the home hero image takes about 2.9 s to paint on a simulated slow phone (Lighthouse), so consider a smaller hero image.

## 2026-11-28 keyword pages
Run `python3 scripts/build_guides.py`, then `python3 scripts/kwpages.py .`, then `python3 scripts/retrofit.py .`. `kwpages.py` writes 21 keyword pages from `scripts/kwpages.json` (prices are 'onwards' because the cost sheet lists starting units). The thin guides were lengthened through the `EXTRA` dict in `build_guides.py` (guide length now averages about 557 words, minimum 511).
