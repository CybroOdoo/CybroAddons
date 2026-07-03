# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import base64
import csv
import io
import requests

from odoo import models, fields
from odoo.exceptions import UserError


class BulkPartnerImageImport(models.TransientModel):
    """Wizard to import partner images from a CSV file."""
    _name = "bulk.partner.image.import"
    _description = "Bulk Partner Image Import"

    file = fields.Binary(
        "CSV File", required=True,
        help="Upload a UTF-8 encoded CSV file containing partner names and image URLs."
    )
    filename = fields.Char("File Name", help="Name of the uploaded CSV file.")

    def action_import_images(self):
        """Import partner images from the uploaded CSV file."""
        if not self.file:
            raise UserError("Please upload a CSV file")

        file_data = base64.b64decode(self.file)

        try:
            text = file_data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UserError(
                "Invalid file format. Please upload a valid CSV file (UTF-8 encoded)."
            ) from exc

        data = io.StringIO(text)
        reader = csv.DictReader(data)

        Partner = self.env["res.partner"]

        seen_names = set()
        errors = []

        for line_no, row in enumerate(reader, start=2):  # header = line 1

            name = (row.get("name") or "").strip()
            image_url = (row.get("partner_image_url") or "").strip()

            if not name or not image_url:
                errors.append(f"Line {line_no}: Missing name or image URL")
                continue

            # ✅ Check duplicate in CSV
            if name in seen_names:
                errors.append(f"Line {line_no}: Duplicate partner '{name}' in CSV")
                continue
            seen_names.add(name)

            partners = Partner.search([("name", "=", name)])

            # ❌ No partner found
            if not partners:
                errors.append(f"Line {line_no}: Partner '{name}' not found")
                continue

            # ❌ Multiple partners found
            if len(partners) > 1:
                errors.append(f"Line {line_no}: Multiple partners found with name '{name}'")
                continue

            partner = partners[0]

            try:
                response = requests.get(image_url, timeout=10)

                if response.status_code == 200:
                    partner.image_1920 = base64.b64encode(response.content)
                else:
                    errors.append(f"Line {line_no}: Failed to fetch image for '{name}'")

            except requests.exceptions.RequestException as e:
                errors.append(f"Line {line_no}: Error fetching image for '{name}' - {str(e)}")

        # 🚨 Raise all errors together
        if errors:
            raise UserError("\n".join(errors))