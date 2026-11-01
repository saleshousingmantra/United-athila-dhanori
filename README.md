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
1. Replace every `https://www.example.com` with your real domain (index.html, thank-you, robots.txt, sitemap.xml).
2. Set `DEFAULT_MANAGER_EMAIL` in `js/config.js` to the RM who should receive leads.
3. Confirm the amenity list and the map pin coordinates (18.5935, 73.9133 is approximate for Dhanori).
