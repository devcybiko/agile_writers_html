# Static build report

- Source: `/Users/greg/git/agile_writers_html/captures/20261029-204542/agilewriters.com`
- Build: `/Users/greg/git/agile_writers_html/builds/site-20261029-204542`
- Files copied: 1269
- Transformations: none. Existing wget link conversions and assets were retained.
- Wget already percent-encoded literal query characters in captured HTML links; filenames and references were not renamed.

## Unresolved items

- 24 distinct production references have no local candidate; these need review.
- 14 external resource or metadata hosts appear in HTML/CSS; review actual browser requests.
- 480 distinct WordPress endpoint references remain; some are metadata, others may support runtime features.
- Search forms remain unchanged and require WordPress or an approved static replacement to work.
- JavaScript-generated URLs, forms, carousel behavior, and browser compatibility have not been verified.
- A static server's MIME handling for wget filenames containing literal question marks needs testing.
- The site has not been visually validated or approved for deployment.

See the site audit for details. Static parsing does not prove completeness or functionality.
