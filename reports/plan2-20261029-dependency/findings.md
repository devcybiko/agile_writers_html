# Step 1 dependency findings

## Missing production assets (24 distinct references)

Sources below are from the static audit. A runtime hit is evidence of use; no hit does not prove a CSS rule is unused.

| Reference | Source | Observed runtime | CSS context / proposed disposition |
|---|---|---|---|
| `https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.eot` | `wp-content/themes/bizberg/assets/css/main.css?ver=1.0.css` | Not observed | `font-family: 'Aclonica'; src: url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.eot` | `wp-content/themes/bizberg/assets/css/component.css?ver=1.0.css` | Not observed | `font-family: 'slick'; font-weight: normal; font-style: normal; src: url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.eot?` | `wp-content/themes/bizberg/assets/css/component.css?ver=1.0.css` | Not observed | ` normal; src: url('https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.eot'); src: url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.svg` | `wp-content/themes/bizberg/assets/css/component.css?ver=1.0.css` | Not observed | `url('https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.ttf') format('truetype'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.ttf` | `wp-content/themes/bizberg/assets/css/component.css?ver=1.0.css` | Not observed | `), url('https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.woff') format('woff'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.woff` | `wp-content/themes/bizberg/assets/css/component.css?ver=1.0.css` | Not observed | `://agilewriters.com/wp-content/themes/bizberg/assets/css/fonts/slick.eot?') format('embedded-opentype'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.svg` | `wp-content/themes/bizberg/assets/css/main.css?ver=1.0.css` | Not observed | ` url('https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.ttf') format('truetype'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.ttf` | `wp-content/themes/bizberg/assets/css/main.css?ver=1.0.css` | Not observed | `'), url('https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.woff') format('woff'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.woff` | `wp-content/themes/bizberg/assets/css/main.css?ver=1.0.css` | Not observed | `ps://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.eot') format('embedded-opentype'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.woff2` | `wp-content/themes/bizberg/assets/css/main.css?ver=1.0.css` | Not observed | `ps://agilewriters.com/wp-content/themes/bizberg/assets/fonts/Aclonica.eot') format('embedded-opentype'), url('`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/animated-number/bg.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: #132125 url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/bread-bg.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: #EDEDED url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/cta2/cta2-bg.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: #242a33 url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/skill-bg.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background:url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/team/01.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background-image: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/team/02.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background-image: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/team/03.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background-image: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/team/04.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background-image: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/testimonial/bg.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: #333333 url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/images/touch.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `color: #fff; background:#132125 url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/img/blackboard.jpg` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: #333 url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/img/line.png` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `font-weight: bold; font-size: 1.8em; padding: 0 0 0.5em; background: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/themes/bizberg/assets/img/stamp.png` | `wp-content/themes/bizberg/assets/css/style.css?ver=1.0.css` | Not observed | `background: url(`; review before removal or replacement |
| `https://agilewriters.com/wp-content/uploads/2017/08/225x225bb.jpg.pagespeed.ce.gPi9OVWGR6.jpg` | `category/structure/index.html` | Yes, blocked | `ndex.html%3Fp=486.html" class="featured_image_link"> <div class="entry-thumbnail" style="background-image:url(`; review before removal or replacement |

## External runtime resources and disposition

- Google Fonts CSS and Lato font: localize after checking the source license; captured fonts need comparison.
- Bizberg background image: check for an identical local asset or permission to store a local copy.
- WordPress emoji script: remove or replace only after testing native emoji rendering.
- Mitchell Productions article image: investigate permission and local capture; do not silently remove.
- Structure category PageSpeed image: observed browser block; investigate original image and CSS before replacing.

## Search, comments and other forms

- Search markup occurs repeatedly in header and sidebar; two search inputs were observed on each sampled extra page. Remove as out of scope in step 3.
- Comment-count wrappers occur in article markup; stylesheet matches alone do not prove active comment forms. Audit actual markup and remove out-of-scope controls without removing article text.
- Sampled pages reported three forms: two search forms and a category dropdown form using `name="cat"` with a GET action targeting the homepage. This category selector is distinct from search and requires a static navigation replacement or another owner-approved disposition; preserve category navigation.

## Coverage and unresolved questions

- Browser trace covers homepage desktop/mobile, one guest article, category/structure, page/2, about, Muppets article, and Daisy Jones article; it is not an exhaustive crawl.
- Desktop carousel Next advanced. Mobile menu click was attempted, but aria-expanded was absent before and after: menu interaction is not verified.
- Muppets article was sampled live but no explicit featured image was found by the limited HTML query. The local homepage uses the theme placeholder; live slide comparison remains unresolved.
- The audit groups HTML links by navigation, resource, metadata, and form action; CSS and script-generated dependencies require separate review. Counts include duplicated short-link pages.
- Dynamic calls may require different interactions or authenticated pages, so no-runtime-call completeness remains unproven.
