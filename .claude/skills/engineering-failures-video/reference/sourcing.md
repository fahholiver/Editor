# U.S. engineering evidence and reuse

## Where to get footage without an account (use in this order)

1. **Wikimedia Commons**: `python scripts/commons.py "<search>" --video` (or `--image`). No key or login. Filters to public domain, CC0, CC BY and CC BY-SA. Searching the agency's own clip title or ID (for example `240404-G-G0105`) finds DVIDS uploads that were mirrored to Commons. `--add PROJECT` writes the hits into `assets.json`.
2. **Direct agency downloads**: NTSB and CSB report PDFs, docket figures and animations, USGS videos, NASA (images-api.nasa.gov), NOAA. These are plain file links.
3. **Internet Archive** public-domain collections (`archive.org/advancedsearch.php`, no key) for period films.
4. **DVIDS** only as a last resort: high-resolution files need a free login, so prefer the Commons copy of the same clip. If a DVIDS item is essential and has no mirror, mark it `manual: true` and tell the creator it is optional.

Never use TV news, wire photos, social-media videos or anything without a clear free license.


Search [NTSB investigations](https://www.ntsb.gov/investigations/Pages/default.aspx), [CSB completed investigations](https://www.csb.gov/investigations/completed-investigations/), [NHTSA crash-test media](https://www.nhtsa.gov/ratings/government-5-star-safety-ratings-motor-vehicles-advertising-and-communication-usage), and [DVIDS Coast Guard media](https://www.dvidshub.net/). Search the case name, then its date, agency, vessel, route, or docket number. For an episode candidate, open at least one clip page, still page, and report. Verify whether a second moving sequence exists and whether the footage actually depicts the episode subject.

## Asset list for fetch.py

Write `PROJECT/assets.json` as a list of objects with `file` (where it goes in the project, such as `real/salvage_drone.mp4` or `media/ntsb_fig12.png`), `url` (a direct file link when one exists), `page` (the item page), `kind`, `depicts`, `credit`, `rights`, and `manual: true` for items that need a login or a click-through download. `scripts/fetch.py PROJECT` downloads, logs and inventories them.

## Keep a ledger in CREDITS.md

| Local file or figure | Exact source URL and item ID | Author and year | What it depicts | Reuse evidence and credit | File or source timecodes |
|---|---|---|---|---|---|

Record the report page or figure number beside each claim. Save the item's credit and rights statement. A draft may list unverified leads, but only verified assets belong in the render. Prefer explicit public-domain or CC0 items, documented official-duty U.S. federal work, or a clear commercial-use license if the creator accepts its terms. DVIDS may require a free account for source downloads. When access requires an account, ask the creator to download the item and place it in the project. Use exact source files when possible.

A U.S. agency website may host privately authored photographs, vendor video, news footage, contractor animation, music, or exhibits. Verify authorship and reuse at the item and track level. Government records and FOIA access are separate from copyright permission. Treat state and local footage, private surveillance, TV news, wire photographs, third-party dockets and agency marks as separate checks. Use an official report or statement for the news beat, or make an original diagram from the documented facts. Public-domain material can still receive an automated YouTube claim. [Federal copyright guidance](https://www.usa.gov/government-copyright) · [NARA audiovisual permissions](https://www.archives.gov/research/motion-pictures/permissions) · [DVIDS FAQ](https://www.dvidshub.net/about/faq) · [YouTube copyright guidance](https://support.google.com/youtube/answer/2797466)

Watch every downloaded clip and inspect stills at editing size. Record exact in/out points. Preserve the original and transcode selected footage if needed. Avoid looping archival evidence or using stock footage to imply a real event. The assembly tool loops stock clips for technical convenience, so keep the stock selection long enough for its planned placement and label it if the viewer might mistake it for case footage.
