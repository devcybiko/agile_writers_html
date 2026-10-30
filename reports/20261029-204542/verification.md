# Local HTTP verification

- Root: `/Users/greg/git/agile_writers_html/builds/site-20261029-204542`
- Base: `http://127.0.0.1:8000/`
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
- `application/octet-stream`: 490
- `image/jpeg`: 186
- `image/png`: 68
- `font/woff`: 36
- `text/css`: 20
- `application/vnd.ms-fontobject`: 6
- `image/svg+xml`: 6
- `font/ttf`: 6
- `font/woff2`: 6
- `image/gif`: 4

## Limitations

GET checks cover statically discoverable HTML and CSS references only; external URLs are not requested. Search, JavaScript, carousel interactions, visual fidelity, and production host routing require separate verification. A successful HTTP response does not establish the correct content or MIME type.

## Browser and visual observations

- Headless Chrome initialized the homepage Slick carousel, as shown by `slick-initialized` and generated controls in the rendered DOM. This does not establish that controls, transitions, or all slides work.
- Desktop screenshots: `local-home.png` and `live-home.png` (1280 x 900). The header, hero, and carousel layout appear similar; the carousel contains different articles, and some local slides show no image. The snapshots alone do not establish why or prove a regression.
- The local Python server returned `application/octet-stream` for the captured jQuery filename containing a literal question mark. Chrome initialized the carousel in this test, but other browsers or stricter deployment servers may reject or misidentify scripts. Deployment MIME behavior needs investigation.
- Mobile layout, representative article pages, carousel interactions, runtime network requests, and offline operation remain unverified. Search still requires a separately agreed replacement.
