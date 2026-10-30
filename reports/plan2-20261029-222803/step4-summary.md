# Plan 2 step 4: rebuild and static checks

- Fresh build: `builds/site-plan2-20261029-222803/`; prior builds and capture retained.
- Unit tests: 3 passed. Homepage HTTP HEAD: 200, `text/html`.
- HTTP checker: 964 unique statically discovered local URLs returned success; no detected JavaScript or stylesheet MIME mismatches. HTTP status does not prove response content or dynamic behavior.
- Audit: no detected missing local references or production URLs lacking local candidates in the HTML/CSS scan. No detected search/comment indicators or direct WordPress endpoint references in HTML/CSS markup; this is a heuristic, not exhaustive runtime verification.
- The checker found 115 distinct external resource references, including numerous article image URLs at `agilewriter.files.wordpress.com` and the Mitchell Productions image. Some images also have local `srcset` candidates; this does not prove every browser can work offline. These need asset-by-asset localization and rights review. Ordinary outbound links and external metadata are listed separately in the HTTP report.
- 420 HTML files contain inline scripts matching the endpoint heuristic. Inspection of the homepage match shows WordPress-generated speculation rules containing `/wp-*.php` and `/wp-admin/*` exclusion patterns. These matches are not by themselves evidence of calls; audit remaining scripts and runtime behavior rather than treating the count as 420 calls or as proof of no calls.
- Six uncaptured category choices remain disabled, listed in `build-report.md`. Browser/offline coverage, actual server routing, and resource rights remain unresolved. The acceptance criteria are not yet met; do not deploy this build.

Evidence: `build-report.md`, `site-audit.md`, `site-audit.json`, and `http-verification.md` in this directory.
