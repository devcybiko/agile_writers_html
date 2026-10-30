# Static release candidate for server testing

- Serve the contents of `site/` as the website root; `site/index.html` is the entry page. No WordPress, PHP interpreter, or database is needed for serving the generated pages.
- This is a test release, not final publication approval. Final third-party image redistribution permissions and attribution must be confirmed before public deployment.
- Search, user comments, and RSS feeds are intentionally absent.
- The Night at the Museum poster and Mark Dawson image are still missing: their source URLs redirect to 404, and no authorized replacement has been supplied. The corresponding article pages retain the original URLs and will have broken images when offline.
- Some captured filenames contain a literal `?` character, and page links encode it as `%3F`. The local Python server serves them correctly, but hosts, upload tools, filesystems, or security rules may reject such names or encoded paths. Verify site navigation, assets, correct JavaScript/CSS MIME types, category menus, and carousel on the actual test server. Hosting is not yet selected, so behavior is not established.
- Seven unit tests passed; all 962 statically discovered local URLs returned successful HTTP responses and no script/style MIME errors with Python's local server. Browser tests of the equivalent previous build covered sampled pages and interactions; they are not comprehensive or specific to the destination server.
- The retained `wp-content`, `wp-includes`, and `wp-json` paths contain captured static files, not an operational WordPress installation. Server runtime independence and external requests should be tested on the chosen host before final deployment.
- The complete build report, static audit, and HTTP verification are in this directory.
