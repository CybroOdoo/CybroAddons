.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

# NHS Trust Management — UK Regions Extension

**Extend your NHS Trust register to NHS Wales and HSC Northern Ireland — full UK coverage from one suite.**

`odoo_nhs_uk_regions` brings the remaining two UK health systems into the NHS Trust Management suite. After installing this module, your trust register supports all four UK nations side by side — England, Scotland, Wales and Northern Ireland — using the same workflow, audit trail, security model and reporting you already rely on.

---

## Why this module?

The NHS Trust Management suite was built England-first, with Scotland second. This extension completes the picture by adding:

- **NHS Wales** — the 7 Local Health Boards (LHBs) plus the 3 national NHS Wales Trusts (WAST, Velindre, Public Health Wales).
- **HSC Northern Ireland** — the 5 Health and Social Care (HSC) Trusts plus the Northern Ireland Ambulance Service (NIAS).

It is a clean, additive extension. Your existing England and Scotland data is untouched, and every existing feature continues to work for the new Welsh and Northern Irish organisations the moment they are created.

---

## Key features

- **Full UK coverage** — the `health_system` field expands from 2 to 4 values: NHS England, NHS Scotland, NHS Wales and HSC Northern Ireland.
- **Welsh Local Health Boards** — a dedicated master-data model for the 7 LHBs, each pre-loaded with its official ODS code, bilingual (English/Welsh) name and key details.
- **Pre-seeded organisations** — 16 organisations created on install: 7 Welsh LHBs, 3 Welsh national trusts, 5 HSC Trusts and NIAS.
- **Region-aware governance links** — Welsh trusts link to their Local Health Board; Northern Irish HSC Trusts attach directly to the NI region (correctly modelled, since NI has no intermediate commissioning body).
- **Smart form behaviour** — the trust form automatically shows and hides the right fields per health system: the Welsh LHB field appears only for Wales, English ICB/ICS fields hide for the devolved nations, and CQC fields continue to hide outside England.
- **Region-scoped security** — users can be restricted to specific Welsh LHBs or to the Northern Ireland region, extending the existing access-control pattern with no new security groups to manage.
- **Validation built in** — constraints ensure Welsh trusts carry a Local Health Board (with the correct exemption for the national Welsh trusts), and that organisations from different nations can't be mixed up.
- **Upgrade-safe seed data** — all pre-loaded records use `noupdate` so your manual edits survive future module upgrades.

---

## What's included

### New organisations seeded on install

**NHS Wales — Local Health Boards (7)**

| Local Health Board | ODS code |
|---|---|
| Aneurin Bevan University Health Board | 7A6 |
| Betsi Cadwaladr University Health Board | 7A1 |
| Cardiff and Vale University Health Board | 7A4 |
| Cwm Taf Morgannwg University Health Board | 7A5 |
| Hywel Dda University Health Board | 7A2 |
| Powys Teaching Health Board | 7A3 |
| Swansea Bay University Health Board | 7A7 |

**NHS Wales — National Trusts (3)**

- Welsh Ambulance Services NHS Trust (WAST)
- Velindre University NHS Trust
- Public Health Wales NHS Trust

**HSC Northern Ireland — Trusts (6)**

| HSC Trust | ODS code |
|---|---|
| Belfast Health and Social Care Trust | ZT001 |
| Northern Health and Social Care Trust | ZT002 |
| South Eastern Health and Social Care Trust | ZT003 |
| Southern Health and Social Care Trust | ZT004 |
| Western Health and Social Care Trust | ZT005 |
| Northern Ireland Ambulance Service (NIAS) | ZT006 |

Plus 2 new regions (Wales, Northern Ireland) and the relevant Welsh and NI trust types.

---

## Requirements

- **Odoo 19.0** (Community or Enterprise)
- **`odoo_nhs_trust_management`** — this module extends the core trust register and must be installed first.

Works alongside (but does not require) `odoo_nhs_trust_operations` and `odoo_nhs_trust_reports` — both function correctly with Welsh and Northern Irish trusts as soon as they exist.

---

## Installation

1. Place `odoo_nhs_uk_regions` in your Odoo addons path.
2. Update the Apps list (developer mode) or restart the server.
3. Search for **"NHS Trust Management — UK Regions Extension"** and click **Install**.
4. The Welsh LHBs, Welsh and NI trusts, regions and trust types are created automatically.

### After installing

- Find your new organisations under **NHS Trusts → Operations → Trusts** (16 new records).
- Welsh Local Health Boards are listed under **NHS Trusts → Configuration → Welsh Local Health Boards**.
- To scope a user to specific Welsh LHBs or to Northern Ireland, open their user record → **Preferences → NHS Access** and set **Allowed Welsh LHBs** and/or **Allowed Regions**.

---

## How it fits the suite

```
NHS Trust Management — Core   (odoo_nhs_trust_management)
        ▲
        │ extends
NHS Trust Management — UK Regions Extension   (this module)
        │
        ├─ works alongside Operations & Compliance
        └─ works alongside Reports & Documents
```

This module depends only on the Core module, so it installs cleanly with any combination of the rest of the suite.

---

## A note on the devolved nations

Wales and Northern Ireland organise health differently from England, and this module reflects that faithfully:

- **Wales** uses an integrated planner-provider model — the Local Health Board is both the regional body and the operational provider, so each LHB is recorded as both. The three national Welsh trusts (WAST, Velindre, Public Health Wales) operate Wales-wide and are not tied to a single LHB.
- **Northern Ireland** runs an integrated Health and Social Care model with no intermediate commissioning layer, so HSC Trusts attach directly to the Northern Ireland region.

The regulators differ too — Healthcare Inspectorate Wales (HIW) and the Regulation and Quality Improvement Authority (RQIA) in Northern Ireland — which is why CQC-specific features correctly remain England-only.

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

Contact: odoo@cybrosys.com

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
