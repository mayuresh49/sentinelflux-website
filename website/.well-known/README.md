# .well-known — TalentDesk mobile deep-link association

Served at `https://sentinelflux.in/.well-known/` (GitHub Pages — the deploy uses
peaceiris/actions-gh-pages, which disables Jekyll, so this dotfolder IS published;
the build's `cp -r website/. _build/` copies it). App package:
`in.sentinelflux.talentdesk`. The app registers hosts **sentinelflux.in** and
**talentdesk.sentinelflux.in**.

## assetlinks.json (Android App Links) — ACTION REQUIRED
Replace `REPLACE_WITH_APK_SIGNING_SHA256` with the SHA-256 fingerprint of the
keystore that **signs the APK**:
```bash
keytool -list -v -keystore <keystore> -alias <alias> | grep SHA256
```
⚠️ The CI **debug** build uses an ephemeral debug keystore (fingerprint changes
each build), so pin a release (or fixed debug) keystore to get a stable value.
You may list multiple fingerprints in the array (e.g. debug + release).
Until this is filled, verified `https://` App Links won't auto-open — but the
custom scheme `talentdesk://clients/c1` already works with the debug APK.

## apple-app-site-association (iOS Universal Links) — ACTION REQUIRED
Replace `REPLACE_TEAMID` with your Apple Developer Team ID. iOS expects this
served as `application/json` with **no file extension** (already extensionless).
iOS isn't built yet — this is scaffolding for when it is.

## Verify once filled
```bash
curl -s https://sentinelflux.in/.well-known/assetlinks.json
# Android verifier:
# https://developers.google.com/digital-asset-links/tools/generator
```
