.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

# NHS Trust Management — ODS Sync

**Keep your NHS organisation register accurate automatically — live data straight from the NHS Digital Organisation Data Service.**

`odoo_nhs_ods_sync` connects the NHS Trust Management suite to the NHS Organisation Data Service (ODS), the canonical national register of every NHS organisation in the UK. Instead of typing hundreds of trusts, ICBs and health boards by hand — and watching the data go stale within months — you bulk-load the register in minutes and keep it current with an unattended daily sync.

---

## Why this module?

Without ODS sync, every corporate team adopting the suite has to manually transcribe NHS organisation data: 200+ trusts across four nations, plus ICBs, Local Health Boards, Scottish Health Boards and HSC Trusts. That's days of data entry, prone to typos in ODS codes, postcodes and names — and the data drifts out of date as organisations merge, rename or change leadership.

This module turns that into a one-click install-time bootstrap plus an automatic daily catch-up. Your register stays correct without ever drifting from the national source.

---

## Key features

- **One-click bulk load** — pull every active NHS Trust, ICB, Health Board, Welsh LHB and HSC Trust from ODS in a single run, instead of hours of manual entry.
- **Automatic daily sync** — a scheduled job pulls only the organisations that changed since the last run, so your register stays current with no effort.
- **Targeted sync** — refresh a single organisation by its ODS code in seconds.
- **Dry-run mode** — preview exactly what a sync *would* change before committing anything, so you're never surprised.
- **Conflict resolution** — when an ODS value differs from a field you edited manually, the sync raises a conflict for review instead of silently overwriting your work. Resolve with Accept ODS / Keep Local / Ignore.
- **Field-level provenance** — every field knows whether its value came from a person or from ODS, so the system always knows what's safe to update automatically.
- **Full audit trail** — every sync run is logged with timestamps, counts (created / updated / unchanged / conflicts / errors) and a complete per-organisation detail record. Answer "what happened last night?" in one click.
- **Connection test** — a quick probe against ODS to confirm connectivity and latency before you schedule a large run.
- **No credentials required** — the ODS directory is a public read-only service, so there's nothing to license or authenticate for standard syncing.
- **Configurable and safe** — adjustable request throttling, timeout and a polite User-Agent; scheduled jobs ship disabled so installs are safe in any environment until you switch them on.

---

## How it works

```
NHS Digital ODS  ──(public REST API)──►  Sync Engine  ──►  Your NHS Trust register
                                              │
                                              ├─ matches by ODS code (never fuzzy)
                                              ├─ updates safe fields automatically
                                              ├─ raises a conflict where you edited manually
                                              └─ logs every run for audit
```

- **Bulk sync** walks each NHS organisation role (Trust, Foundation Trust, ICB, Health Board, Welsh LHB, HSC Trust) and pulls the active organisations.
- **Daily delta sync** asks ODS only for organisations changed since the last successful run — fast and lightweight.
- **Matching** is always on the authoritative ODS code, so an organisation is never mis-matched by name.
- **Your manual edits are protected.** If you've corrected a field by hand and ODS later disagrees, the sync flags a conflict rather than overwriting you.

---

## What gets synced

For each organisation, the sync maps the authoritative ODS data onto your register:

- Official name and ODS code
- Operational status (active / inactive)
- Establishment / operational dates
- Address and postcode
- Main telephone
- Foundation Trust status (derived from ODS roles)
- Governance link — matched to the correct ICB, Health Board or Welsh LHB where ODS records the relationship

Organisations marked inactive in ODS are reflected in your register's status, with the change logged and attributed to the sync run.

---

## Requirements

- **Odoo 19.0** (Community or Enterprise)
- **`odoo_nhs_trust_management`** — this module syncs into the core trust register and must be installed first.
- **Recommended:** `odoo_nhs_uk_regions` — install it too so Welsh Local Health Boards and HSC Northern Ireland organisations are fully supported by the sync.
- **Internet access** to the public NHS ODS directory (`directory.spineservices.nhs.uk`). No API key needed.

---

## Installation

1. Place `odoo_nhs_ods_sync` in your Odoo addons path.
2. Update the Apps list (developer mode) or restart the server.
3. Search for **"NHS Trust Management — ODS Sync"** and click **Install**.

### First run

1. Go to **Settings → NHS Settings → ODS Sync** and enter a contact email (sent in the request header so NHS Digital can identify the client). Review the timeout and throttle defaults.
2. Click **Test ODS Connection** — you should see a green result with low latency.
3. Open **NHS Trusts → Configuration → ODS Sync → Run Sync Now**, choose **Dry run** + **All roles**, and review what the sync would change.
4. Happy with the preview? Run it again as a **Live** sync. The initial full pull typically takes a little while as it fetches a few thousand organisations.
5. Optionally enable the **daily delta** and **monthly full** scheduled jobs (off by default) under **Settings → Technical → Scheduled Actions**, or just run manual syncs on demand.

---

## Conflict resolution

When ODS data differs from a value you edited by hand, the sync doesn't overwrite it — it creates a conflict for review:

- **Accept ODS** — take the national value.
- **Keep Local** — keep your edit; ODS won't overwrite it.
- **Ignore** — suppress this conflict in future syncs (with a recorded reason).

Conflicts appear in a dedicated review board, and resolutions are logged against the affected organisation.

---

## How it fits the suite

```
NHS Trust Management — Core   (odoo_nhs_trust_management)
        ▲
        │ syncs into
NHS Trust Management — ODS Sync   (this module)
        │
        ├─ recommended:  UK Regions Extension  (Wales & NI coverage)
        ├─ works alongside  Operations & Compliance
        └─ works alongside  Reports & Documents
```

This module depends only on the Core module, so it installs cleanly with any combination of the rest of the suite.

---

## Good to know

- **Read-only, one-way.** The ODS directory is read-only for external organisations, so this module only ever *pulls* data — it never writes back to NHS Digital.
- **Audit-friendly.** Every sync run, and every organisation processed within it, is recorded — created, updated, unchanged, conflicted or skipped — so you have a complete history.
- **Polite by default.** Requests are throttled and carry an identifying User-Agent, in line with ODS usage guidance.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
=======
Developer: (V19) Nubla Sherin K ,

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

---

*Part of the **Odoo for NHS Back-Office Operations** suite by Cybrosys Techno Solutions — purpose-built NHS Aligned modules for Odoo 19.*
