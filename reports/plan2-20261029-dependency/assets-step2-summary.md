# Plan 2, step 2: asset localization

- Build: `builds/site-plan2-assets-20261029/`. The retained capture and earlier builds were not changed.
- Localized Lato stylesheet and eight font subset files, retaining the Lato SIL OFL 1.1 license in `assets/vendor/lato/OFL.txt`; manifest records URLs, types, checksums, retrieval times, and intended use. The generated stylesheet points to the local subsets.
- The Bizberg background at the third-party URL and the captured `wp-content/themes/bizberg/assets/images/breadcrum.jpg` had identical SHA-256 digests; generated references now use the captured asset.
- The Structure category's unavailable PageSpeed image now references captured `wp-content/uploads/2017/08/225x225bb.jpg`, the apparent original behind the optimized URL. Pixel equivalence to the unavailable derivative cannot be established from the 404 response.
- The remaining 23 missing production references concern theme fonts and images. None appeared in the sampled step 1 browser requests, but their use has not been ruled out. They remain unresolved; no CSS was removed on the assumption it is unused.
- The Mitchell Productions article image remains external because redistribution permission has not been established. The WordPress emoji script remains external and is scheduled for evaluation in step 3. Other unvisited pages may have further dependencies.
- Browser check of homepage, one guest article, Structure category, page 2, and About: no failed responses detected; the observed external requests were limited to the emoji script and the Mitchell Productions image plus its redirect. This is not an exhaustive or offline test.
- Local HTTP checker: 1,433 URLs returned success. This does not establish visual parity or correctness of every dynamic feature.
- Search and comments were not changed; they are outside scope and scheduled for removal in step 3.
