# Follow-up build and verification

- Build: `builds/site-plan2-next-20261029/`. Source and earlier builds remain intact.
- Both original HTTP image URLs redirect to HTTPS and return 404. The linked full-size poster URL also returns 404. The two exact original images were not found in the capture; replacements or originals remain required.
- Removed the inactive `.footer_pro` third-party background reference after scanning captured HTML and finding no matching element. Dynamic injection remains untested. Removed six newly captured category feed links that pointed to uncaptured live feeds; retained links to locally captured feed snapshots.
- The audit and HTTP checker now identify captured RSS snapshots as feed data, not HTML. Their outgoing URLs are **not audited** and require separate review; they must not be assumed to work offline.
- Seven unit tests passed. Local HTTP checker: 991 successful URLs, zero failures, zero script/style MIME mismatches. It found two external resource references in scanned HTML/CSS, the two missing image URLs. Runtime-generated requests and feed content are outside this static count.
- Chrome sample with external HTTP(S) requests blocked: homepage and carousel loaded; Next and Previous worked. One mobile navigation test changed the menu from `display:none` to `display:block`; one archive dropdown navigated locally to July 2015. Sampled categories and a guest article loaded. The two articles with missing images each produced the expected blocked-image failure. No sampled JavaScript exceptions were recorded.
- Coverage remains limited; final review, authorization for third-party redistribution, a feed decision, broader responsive/offline testing, and intended host routing/MIME checks are required before deployment.

Evidence: `next-audit-revised.json`, `next-http-revised.md`, `next-browser.json`, and `next-interactions.json`.
