# RSS removal and additional testing

- Build: `builds/site-plan2-no-rss-20261029/`. The build process removes 29 RSS/Atom snapshots and local or remote feed-discovery links. Source captures and prior builds remain unchanged. Static scans found no RSS/Atom discovery links and no feed snapshot files in the generated build.
- Seven unit tests passed. The local HTTP checker tested 962 unique URLs successfully with no detected script or stylesheet MIME errors. Two external image references remain unresolved and are documented in `goals/plan.md` for later.
- A headless Chrome sample blocked external HTTP(S) requests. The homepage carousel initialized and advanced in both directions, the mobile homepage fit a 390-pixel viewport, all six restored category pages loaded, and sampled article pages had no broken images except the two already identified. No JavaScript exceptions were recorded in the sample.
- Separate browser interaction checks opened the mobile menu and navigated from the category selector to each of the six restored local category pages. The archive dropdown was checked in the prior build; this run did not recheck every archive option.
- These are sampled tests, not exhaustive visual or host-specific acceptance. Permissions review is deferred by the owner, hosting and final review are to be determined, and the two missing images remain unresolved.

Evidence: `no-rss-build.md`, `no-rss-audit.json`, `no-rss-http.md`, `no-rss-browser.json`, and `no-rss-interactions.json`.
