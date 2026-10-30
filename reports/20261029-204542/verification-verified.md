# Local HTTP verification

- Root: `/Users/greg/git/agile_writers_html/builds/site-20261029-verified`
- Base: `http://127.0.0.1:8001/`
- HTML/CSS files inspected: 460
- Unique local URLs checked: 1424
- Successful responses: 1424
- Failed responses: 0
- Distinct absolute production URLs: 53
- Distinct WordPress endpoint references: 480

## Failed local requests
- None detected.

## Response content types
- `text/html`: 596
- `application/octet-stream`: 471
- `image/jpeg`: 186
- `image/png`: 68
- `font/woff`: 36
- `text/css`: 20
- `text/javascript`: 19
- `application/vnd.ms-fontobject`: 6
- `image/svg+xml`: 6
- `font/ttf`: 6
- `font/woff2`: 6
- `image/gif`: 4

## Limitations

GET checks cover statically discoverable HTML and CSS references only; external URLs are not requested. Search, JavaScript, carousel interactions, visual fidelity, and production host routing require separate verification. A successful HTTP response does not establish the correct content or MIME type.

## Browser checks and remaining work

- Headless Chrome: carousel initialized with six original slides, and clicking Next changed its current index from 0 to 1. No JavaScript exceptions, failed network responses, or broken image elements were observed for the homepage, one article, and mobile homepage during this check.
- Mobile viewport 390 pixels: document width was 390, mobile menu element and initialized carousel were present. Mobile screenshots are `browser-check-verified-mobile.png` and `mobile-live.png`; header and hero appear similar, though carousel entries differ. Menu interaction and full-page visual comparison were not checked.
- The article `2019/01/17/guest-post-the-importance-of-colors-to-your-brand/` loaded with the expected title. Additional articles and navigation interactions remain to be tested.
- The previously blank Muppets carousel slide explicitly references the captured theme `placeholder.jpg`; it is not a failed image load. This does not establish whether the live site's corresponding slide uses the same placeholder.
- Added `.js` aliases for captured script files and updated HTML references in the new build. Python's server now reports `text/javascript` for the tested jQuery alias. Test MIME behavior again on the intended host.
- The observed runtime requests include Google Fonts, a Bizberg-hosted background, the live site's WordPress emoji script, and a third-party article image. The site is therefore not yet verified as self-contained.
- Search remains a WordPress-backed form, with no approved static replacement. HTTP success checks alone cannot establish that search works.
- The 24 previously missing production resource URLs, carousel transitions, offline behavior, other articles, and deployment routing remain unresolved or incompletely verified.

Detailed machine-readable observations: `browser-check-verified.json`. The captures contain live third-party requests, so these tests do not establish offline operation.
