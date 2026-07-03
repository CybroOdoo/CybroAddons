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
import logging
import requests

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extend Contact model to support image synchronization from a URL."""
    _inherit = "res.partner"

    partner_image_url = fields.Char(
        string="Image URL",
        help="Provide a valid image URL. The image will be downloaded and "
             "stored in the contact's profile picture."
    )

    # ---------------------------------------------------------
    # Utility: Download image from URL
    # ---------------------------------------------------------
    def _download_image_from_url(self, url):
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                raise UserError("Unable to download image from URL")

            content_type = response.headers.get("Content-Type")

            if not content_type or "image" not in content_type:
                raise UserError("URL does not contain a valid image")

            return base64.b64encode(response.content)

        except requests.exceptions.RequestException as e:
            _logger.error("Image download failed: %s", e)
            raise UserError("Image download failed") from e

    # ---------------------------------------------------------
    # Onchange preview
    # ---------------------------------------------------------
    @api.onchange("partner_image_url")
    def _onchange_partner_image_url(self):
        """Preview image when URL changes"""

        if self.partner_image_url and self.partner_image_url.startswith(("http://", "https://")):
            try:
                self.image_1920 = self._download_image_from_url(self.partner_image_url)
            except UserError:
                self.image_1920 = False

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Create contacts and set image from URL."""
        records = super().create(vals_list)

        for record, vals in zip(records, vals_list):
            url = vals.get("partner_image_url")
            if url:
                try:
                    record.image_1920 = record._download_image_from_url(url)
                except UserError:
                    pass

        return records

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------
    def write(self, vals):
        """Update contact image when URL changes."""
        res = super().write(vals)

        if "partner_image_url" in vals:
            for rec in self:
                if rec.partner_image_url:
                    rec.image_1920 = rec._download_image_from_url(
                        rec.partner_image_url
                    )
                else:
                    rec.image_1920 = False

        return res
