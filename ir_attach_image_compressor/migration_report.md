# Migration Report: ir_attach_image_compressor (V17 to V18)

## 1. Upgrade Scope
The module `ir_attach_image_compressor` underwent migration testing targeting **Odoo 18.0**. Leveraging the previously patched Odoo 17 module baseline, the system functionality ported successfully without deprecation faults.

## 2. API & Component Changes
- **Python Compatibility:** Discovered that Odoo 18 deprecated the object class `odoo.tools.image.ImageProcess` entirely. Refactored the internal loop within `models/image_compression_rule.py` to route the string bytes natively through the updated globally exposed `image_process(source)` handler.
- **ORM Structure:** Validation verified no deprecation of `appends`, datetime mechanisms, or mapping iterations affecting this module.
- **Data Records:** The `numbercall` field for `ir.cron` was removed in Odoo 18 and has been eliminated from `data/cron.xml`.
- **View Architectures:** Checked XML schemas for deprecated evaluation tags. V18 retains parsing structures of `widget="boolean_toggle"` and parameter tags directly utilized in `views/image_compression_rule_views.xml`.
  - **Tree View Deprecation**: Odoo 18 strictly enforces the `<list>` root structural tag instead of `<tree>`. Updated all `file_format_views.xml` and `image_compression_rule_views.xml` instances to `<list>` as well as mapping `view_mode` combinations to `list,form`.

## 3. Frontend Maintenance
- Updated metadata version specifiers and cybrosys internal app references via `sed` substitutions inside `static/description/index.html` from 17.0 over to target 18.0 documentation and marketplace links.

## 4. Final Validation Steps
- Evaluated codebase against lint constraints. Resolved previously raised PEP8 ordering alerts localized inside logic imports.
- Re-packaged payload effectively eliminating trailing compilation directories `__pycache__/*`.
