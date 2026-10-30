# Outstanding Agile Writers deployment issues

These issues were found during step 5's local Apache checks. Resolve them in the site source or build process outside the deployment plan, then redeploy the corrected site to `/var/www/agilewriters.com` and verify the fixes.

## Missing sitemap

`robots.txt` advertises `https://agilewriters.com/wp-sitemap.xml`, but that file is absent and the local Apache request returns 404. Provide a valid sitemap or update `robots.txt` to remove or correct the reference.

## Deprecated domain references

Nine deployed files contain `theagilewriter.com`:

- `privacy-policy/index.html`
- `index.html?p=3.html`
- `wp-json/wp/v2/pages/3`
- `wp-json/wp/v2/pages/14`
- `wp-json/wp/v2/pages/17`
- `wp-json/wp/v2/pages/31`
- `wp-json/wp/v2/pages/1016`
- `wp-json/wp/v2/posts/1109`
- `assets/third-party-20261029/manifest.json`

Remove or replace references as appropriate. Keep asset provenance accurate in non-public records rather than inventing a new source. Re-scan the deployed copy after redeployment.

## Legacy WordPress query URLs

Old links such as `/?p=479` currently return the homepage rather than the intended article. The encoded static filename `/index.html%3Fp=479.html` works, but an ordinary query string is not part of a filename. Decide whether legacy links must be supported; if so, implement and test an explicit mapping to the correct pages.