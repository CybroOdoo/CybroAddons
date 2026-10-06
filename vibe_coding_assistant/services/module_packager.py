# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

"""Module packager for the Vibe Coding Assistant.

Builds a ZIP archive in memory from a vibe.generated.module recordset.
No disk I/O — the bytes are built entirely in a BytesIO buffer and returned
directly to the HTTP controller (spec §12).
"""

import io
import zipfile


def build_zip(generated_module) -> bytes:
    """Build and return a ZIP of the generated module as raw bytes.

    The ZIP contains all files prefixed with the module's technical_name so
    that extracting it produces a ready-to-use Odoo addons directory:

        product_brand/
            __manifest__.py
            __init__.py
            models/
                product_brand.py
            ...

    Args:
        generated_module: A vibe.generated.module recordset (ensure_one expected
                          by the controller before calling).

    Returns:
        bytes: In-memory ZIP archive.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in generated_module.file_ids:
            # Leading directory = module's technical_name
            zip_path = f"{generated_module.technical_name}/{f.path}"
            zf.writestr(zip_path, f.content.encode("utf-8"))
    return buf.getvalue()
