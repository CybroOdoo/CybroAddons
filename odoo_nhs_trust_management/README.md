.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3


# NHS Trust Management

The foundation module for managing UK NHS organisations inside Odoo. A complete
master register of every NHS Trust in England and Health Board in Scotland —
with governance, board members, approval workflow and tamper-proof audit
built in from day one.

## Why this module

NHS Trusts and their corporate teams currently juggle Trust master data across
spreadsheets, SharePoint, Excel directories and ad-hoc Access databases.
NHS Trust Management — Core replaces that with a single, structured,
permission-controlled register that becomes the source of truth for every
other NHS module in your Odoo deployment.

## Key features

**UK-wide trust register** — every NHS Trust in England and Health Board in
  Scotland modelled with ODS code, foundation status, establishment date, CQC
  registration and full HQ details.
**Pre-loaded master data** — ships with 42 statutory ICBs, 21 Scottish
  Health Boards (14 Territorial + 7 National), 10 NHS regions and 9 trust
  types ready on install.
**Multi-tier hierarchy** — Region → ICB → ICS → Trust for England, plus
  Region → Health Board → Trust for Scotland, side by side.
**Governance contacts** — Chair, CEO, Medical Director, Director of Nursing,
  Finance Director plus a full board member registry with NHS roles, term
  dates, voting rights and appointing authority.
**Approval-gated workflow** — six-state Trust lifecycle (Draft → Under
  Review → Active → Special Measures → Merging → Dissolved) with manager
  approval, mandatory reason capture and chatter notifications on every move.
**Immutable audit trail** — every status change logged with timestamp, user,
  approver, from/to states and justification. Log entries cannot be edited —
  ever — ensuring tamper-proof compliance records.
**Role-based security** — three-tier permission model (User / Manager /
  Administrator) with record-level rules scoping users to their assigned
  ICBs or Health Boards.
**Hybrid multi-company** — link any Trust to a dedicated Odoo company for
  separated accounting, or share a single company across multiple Trusts.
**CSV bulk import** — rapid onboarding from existing spreadsheets via
  standard Odoo import.

## What ships in this module

| Models | 9 |
| Pre-seeded records | 82 (42 ICBs, 21 Health Boards, 10 regions, 9 trust types) |
| Security groups | 3 (User, Manager, Administrator) |
| Record rules | 3 (scoped to ICB / Health Board) |
| Workflows | Trust state machine with mandatory approval wizard |

## Designed to grow

This module is the foundation of the NHS Trust Management suite. Add
**Operations & Compliance** to extend it with sites, departments, CQC
inspections and financials. Add **Reports & Documents** for branded Trust
Profile PDFs and Excel directory exports.

## Compatibility

Odoo 19.0 Community Edition
English and Scottish NHS structures supported out of the box
Extensible to NHS Wales and NHS Northern Ireland via add-on modules

Configuration
=============
No configuration

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

Further information
===================
HTML Description: `<static/description/index.html>`__
