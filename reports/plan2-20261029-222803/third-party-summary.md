# Third-party image download and verification

The owner authorized downloading identified third-party images for this migration. Final redistribution permissions or licenses must still be obtained and recorded before deployment; authorization to download is not evidence that those rights are secured. The checkpoint is recorded in `goals/plan.md`.

- Downloaded 21 image source URLs into `assets/third-party-20261029/`, with source URL, final URL, checksum, MIME type, timestamp, affected pages, and pending rights status in `manifest.json`.
- Two sources returned HTTP 404 when accessed over HTTPS, and no matching originals were found in the capture: `http://greg-smith.com/wp-content/uploads/2014/12/Night_at_the_Museum_Secret_of_the_Tomb_poster-202x300.jpg` and `http://rogerpacker.com/wp-content/uploads/dawsonmark1-300x299.jpg`. Their HTTPS errors do not establish whether their original HTTP URLs still work; suitable originals or authorized replacements are needed.
- `scripts/build_static.py` copies verified downloaded files and rewrites the affected image sources in a new build. `builds/site-plan2-third-party-20261029/` uses the original capture, the category supplement, matched captured images, and this downloaded collection. Earlier captures and builds remain intact.
- Five automated tests passed. The local HTTP check found 991 successful URLs and no script/style MIME errors. Its 32 external-resource references include the two unresolved images and feed/metadata references, not necessarily 32 active image downloads.
- Chrome with external requests blocked loaded the homepage, guest article containing the Mitchell Productions image, and three additional guest/article pages. No failed network requests, broken image elements, or JavaScript exceptions were recorded in this sample. Carousel next and previous advanced successfully. This is not whole-site or deployment-host verification.

Evidence: `third-party-build.md`, `third-party-audit.json`, `third-party-http.md`, and `third-party-browser.json` in this directory.
