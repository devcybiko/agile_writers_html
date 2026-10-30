# Local HTTP verification

- Root: `/Users/greg/git/agile_writers_html/builds/site-plan2-step3-20261029`
- Base: `http://127.0.0.1:8014/`
- HTML/CSS files inspected: 461
- Unique local URLs checked: 964
- Successful responses: 964
- Failed responses: 0
- Distinct absolute production URLs: 29
- Distinct WordPress endpoint references: 0

## Failed local requests
- None detected.

## Response content types
- `text/html`: 596
- `image/jpeg`: 186
- `image/png`: 68
- `font/woff`: 36
- `text/css`: 21
- `text/javascript`: 17
- `font/woff2`: 14
- `application/vnd.ms-fontobject`: 6
- `image/svg+xml`: 6
- `font/ttf`: 6
- `application/octet-stream`: 4
- `image/gif`: 4

## Limitations

GET checks cover statically discoverable HTML and CSS references only; external URLs are not requested. Search, JavaScript, carousel interactions, visual fidelity, and production host routing require separate verification. A successful HTTP response does not establish the correct content or MIME type.
