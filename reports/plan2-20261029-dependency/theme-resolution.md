# Resolution of 23 missing theme references

Build: `builds/site-plan2-theme-20261029/`. Source capture remains unchanged; the transformations are in `scripts/build_static.py`.

## Investigation

- The Aclonica family occurred only in its `@font-face` declaration across the generated site; no other captured CSS family declaration used it. Removed that declaration, resolving five missing URL variants.
- The Slick font occurred only in its `@font-face` declaration. Slick arrow and dot pseudo-elements use the captured Font Awesome 5 Free font. Removed the unused declaration, resolving five URL variants. In the browser, the computed arrow font was Font Awesome; Next moved the carousel from slide 0 to 1 and Previous returned it to 0.
- Of 13 unavailable theme image URLs, the associated `#about`, `#animated-number`, `#get-in-touch`, `.about-skill`, `.ch-img-*`, `.testi-inner`, `.bg-2`, and pricing selectors were not present in captured HTML markup. Dynamic injection and untested states cannot be ruled out.
- `.breadcrumb-wrapper` did occur on 14 captured homepage/archive pages, and each has an inline background-image pointing to the captured `breadcrum.jpg`. The browser's computed homepage background confirmed that local image. Replaced the 13 unavailable CSS `url(...)` values with `none`, retaining other declarations and fallback colors. This includes the overridden breadcrumb URL. No original resources were deleted.

## Verification and limitations

- The static audit reports zero production URLs without local candidates and zero missing relative references; it does not inspect every dynamically generated URL.
- The local HTTP checker returned success for 1,433 discoverable URLs.
- A headless Chrome test blocked every non-local HTTP(S) request. Homepage carousel initialized and advanced in both directions, and the local hero image was used. Structure, page 2, About, one guest article, desktop and mobile homepage were exercised. The mobile screenshot shows the menu open after its click.
- Offline testing intentionally blocked the live WordPress emoji script and the external Mitchell Productions guest-article image; the latter appeared broken. These are separate unresolved dependencies, not part of the 23 theme references. No JavaScript exceptions were recorded in the sampled test.
- Captured CSS selectors were checked against static HTML, not every possible dynamically generated state. Compare more pages and intended deployment behavior in later steps. Other PHP/WordPress calls, search, comments, external assets, and overall offline acceptance remain unfinished.

Evidence: `theme-audit.json`, `theme-http.md`, `theme-offline.json`, and `theme-offline-mobile.png` in this directory.
