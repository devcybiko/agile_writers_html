# AgileWriters static website conversion plan

## Goal and constraints

Produce an almost pixel-for-pixel static copy of the public AgileWriters.com site, including articles, navigation, styling, images, and the homepage carousel. The resulting site must be servable without PHP, WordPress, or a database. Preserve the production site; no deployment or production changes are included. Keep captures and logs for recovery, limit crawl traffic, and avoid spending tokens repeatedly loading the entire site.

Work one phase at a time. Review the capture audit before deciding how to handle forms, search, comments, external services, inaccessible content, or other dynamic features. Do not assume a public crawl is a complete export.

**Permissions checkpoint:** The owner authorized downloading third-party images for the migration. Before deployment or redistribution, obtain and record final permissions or applicable licenses for each third-party image, including attribution and usage restrictions. Downloading an image is not proof that redistribution rights have been granted.

## Current outstanding work

The release candidate for server testing is `site/` (entry page `site/index.html`); see `reports/release-20261029/release-notes.md`. Follow `goals/plan2.md` for the remaining standalone-site work. Search and user comments are out of scope and should not be restored. RSS feeds and their discovery links have been removed from the generated site; feed files remain in retained source captures.

Two article images could not be downloaded: their original HTTP URLs redirect to HTTPS and return 404, and no matching files were found in the capture. The full-size poster URL also returned 404. Preserve the affected articles and investigate authorized originals or suitable replacements:

1. **Night at the Museum: Secret of the Tomb poster**, used in “Storyboard: Night at the Museum 3”: `http://greg-smith.com/wp-content/uploads/2014/12/Night_at_the_Museum_Secret_of_the_Tomb_poster-202x300.jpg`.
2. **Mark Dawson photograph**, used in “Hollywood Comes Calling for Self-Published Authors”: `http://rogerpacker.com/wp-content/uploads/dawsonmark1-300x299.jpg`.

Next steps:

1. Later: obtain authorized originals or replacements for the two missing images. Record provenance in the asset manifest.
2. Continue checking for remaining WordPress/PHP server dependencies without removing ordinary outbound links. RSS removal is implemented in the build.
3. Rebuild from the retained capture and supplemental category capture, then rerun link, asset, and MIME checks. The latest sample returned 962 successful local URLs; preserve previous builds.
4. Continue desktop/mobile browser and offline testing across additional articles and states. The latest sample verified the carousel, mobile menu, and all six restored category selections; the two missing images are confirmed broken offline. Record visual differences and unresolved issues.
5. Later: confirm third-party permissions. The hosting platform and final build review are to be determined; test host routing and MIME behavior before seeking separate deployment approval.

## Current evidence

- `agilewriters_static_capture/wget_log.txt` reports a timeout waiting for response headers, followed by an SSL connection failure. No pages were captured.
- A later `curl -I` succeeded with certificate verification and HTTP 200. This does not establish that a GET or wget will work, nor explain the earlier failure.
- GNU Wget 1.25.0 with OpenSSL is installed. The existing script exits before writing an inventory when wget fails because it uses `set -e`.

All commands below run from the project root. Commands invoking planned scripts define their intended interfaces; implement the scripts before running them. Variables must be set in the same shell session, or replaced with the actual paths.

```sh
cd /Users/greg/git/agile_writers_html
```

## 1. Diagnose HTTPS and wget

**Files:** None created or modified. Preserve the existing log.

Run bounded GET tests, including the current script's user agent:

```sh
curl -v --connect-timeout 10 --max-time 30 -o /dev/null https://agilewriters.com/
wget --debug --timeout=20 --tries=1 --output-document=/dev/null https://agilewriters.com/
wget --debug --timeout=20 --tries=1 --user-agent='AgileWritersStaticArchive/1.0 (site-owner archival crawl)' --output-document=/dev/null https://agilewriters.com/
```

If TLS or certificate details are needed:

```sh
curl --version
wget --version
openssl s_client -connect agilewriters.com:443 -servername agilewriters.com -verify_return_error </dev/null
```

Run the last command with a bounded execution timeout. If redirected, also test the exact destination with bounded curl and wget requests.

**Decision:** If both GET clients work, retry a cautious capture. If curl works and wget fails, inspect its exact error and compare client, redirect, and certificate behavior before changing tools or options. If both fail, investigate connectivity, DNS, and server availability. If only the custom user agent fails, investigate server treatment of that agent. Do not disable certificate verification to bypass the problem.

**Verification and recovery:** Require successful GETs before a full crawl. Repeat bounded tests if failures are intermittent; preserve diagnostic output and avoid guessing at the cause.

## 2. Make capture reproducible and run it

**Modify:** `scripts/mirror_agilewriters.sh`.

**Create when run:** `captures/<timestamp>/`, including `wget_log.txt`, `file_inventory.txt`, `capture_metadata.txt`, and downloaded host directories.

Require an explicit new output directory and refuse to overwrite an existing one. Record the target, timestamp, wget version, options, and final status. Retain the existing recursive capture, link conversion, host restrictions, robots policy, and polite delay initially. Always produce an inventory and status summary even on failure, while returning wget's real exit status. Never delete earlier captures.

```sh
bash -n scripts/mirror_agilewriters.sh
CAPTURE="captures/$(date +%Y%m%d-%H%M%S)"
bash scripts/mirror_agilewriters.sh "$CAPTURE"
cat "$CAPTURE/capture_metadata.txt"
tail -n 100 "$CAPTURE/wget_log.txt"
grep -Ein 'error|failed|timed out|unable|404|403|500|502|503' "$CAPTURE/wget_log.txt"
wc -l "$CAPTURE/file_inventory.txt"
```

The `grep` exit status 1 means no matching lines, not proof of completeness. A successful crawl should contain HTML and assets as well as metadata and an inventory; inspect the log even if wget exits successfully.

**Risks and recovery:** Keep partial output if timeouts, rate limits, disk usage, or server errors interrupt the crawl. Diagnose the log and use a fresh directory for another attempt. Report robots exclusions rather than bypassing them without approval. Identify specific external asset hosts before expanding crawl scope; do not crawl unrelated sites indiscriminately.

## 3. Audit the capture

**Create:** `scripts/audit_capture.py` and `reports/<capture-name>/capture_audit.{json,md}`.

Implement a read-only Python standard-library audit that counts pages and asset types; parses HTML links, images, scripts, stylesheets, forms, `srcset`, and frames; and checks CSS `url(...)` and `@import` references. Resolve local paths, query strings, fragments, URL encoding, and directory indexes. Report missing local targets, external hosts, production and WordPress endpoint references, and potentially dynamic features. Clearly distinguish uncertain or JavaScript-generated dependencies from confirmed failures.

```sh
python3 --version
python3 scripts/audit_capture.py "$CAPTURE" --json "reports/$(basename "$CAPTURE")/capture_audit.json" --markdown "reports/$(basename "$CAPTURE")/capture_audit.md"
cat "reports/$(basename "$CAPTURE")/capture_audit.md"
```

**Verification:** Compare the report and inventory with the live homepage, navigation, and representative articles. If available, compare against an authorized sitemap or export to find unlinked pages. Inspect and approve any additional asset hosts before fetching them.

**Risks and recovery:** Static parsing cannot see every dynamically constructed URL, and public crawling cannot recover private or unlinked content reliably. Record gaps for browser testing or request an authorized export. Review rights and privacy implications before bundling third-party resources.

## 4. Assemble the static site

**Create:** `scripts/build_static.py`, a fresh `builds/site-<timestamp>/`, and `reports/<capture-name>/build_report.md`. Later designate a verified build as `site/` only after inspecting any existing `site/` and agreeing how to avoid overwriting user work.

Implement a reproducible build that copies the chosen captured host into a new output directory, refuses to overwrite an existing output, leaves the capture unchanged, and records all transformations. Make targeted, evidence-based link and dependency changes; retain WordPress-generated assets that are still needed. Do not remove files merely because their paths contain `wp-`. Record unresolved external and server-dependent features.

```sh
BUILD="builds/site-$(date +%Y%m%d-%H%M%S)"
python3 scripts/build_static.py "$CAPTURE" "$BUILD" --report "reports/$(basename "$CAPTURE")/build_report.md"
python3 scripts/audit_capture.py "$BUILD" --json "reports/$(basename "$CAPTURE")/site_audit.json" --markdown "reports/$(basename "$CAPTURE")/site_audit.md"
cat "reports/$(basename "$CAPTURE")/build_report.md"
cat "reports/$(basename "$CAPTURE")/site_audit.md"
```

**Verification:** The output contains the captured pages and required assets, and the audit identifies remaining issues. Keep an unchanged capture and prior builds for recovery.

**Decision points:** Discuss forms, search, comments, login, embeds, and other server-side features before changing behavior or introducing a third-party service. An external service can be an explicit exception only if approved; otherwise the target remains independently servable. Seek authorized source material if necessary content was not captured.

## 5. Verify locally and fix defects

**Create:** `scripts/check_site.py` and `reports/<capture-name>/verification.md`. Apply narrowly scoped fixes through the build process and produce a fresh build.

Implement a local HTTP checker with timeouts that checks known internal pages and assets, reports non-success responses, redirect loops, unexpected redirects to the live site, and detectable production WordPress endpoint references. Do not follow external URLs by default. This complements, but does not replace, browser testing.

Start the following server in the background and stop that specific process after testing:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$BUILD"
```

```sh
curl -I --connect-timeout 5 --max-time 10 http://127.0.0.1:8000/
python3 scripts/check_site.py --root "$BUILD" --base-url http://127.0.0.1:8000/ --report "reports/$(basename "$CAPTURE")/verification.md"
cat "reports/$(basename "$CAPTURE")/verification.md"
open http://127.0.0.1:8000/
```

Compare the local and live sites at matching desktop and mobile viewport sizes. Test the homepage, navigation, representative articles, images, and carousel controls and transitions. Inspect browser console and network errors when tooling is available. Record results and known differences.

**Acceptance criteria:** Intended public pages and required assets serve without PHP, WordPress, or a database; internal navigation works; known missing assets and links are resolved or documented; appearance is close to the live site; the carousel and agreed interactive features work or have documented limitations; external dependencies are disclosed; and the build is reproducible from the retained capture and scripts.

**Risks and recovery:** Local server routing may differ from the eventual host; test the selected host separately before any deployment. Visual equivalence requires browser review. Preserve previous builds if fixes regress. Production deployment is a separate approval and plan.
