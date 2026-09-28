# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
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
#############################################################################

import logging

from odoo import api, models, _

_logger = logging.getLogger(__name__)


class CsCartVendorSync(models.Model):
    """
        This model is responsible for synchronizing Vendor
        records from CS-Cart into Odoo. It fetches vendor data via the
        CS-Cart API
    """
    _name = 'cs.cart.vendor.sync'
    _description = 'CsCartVendorSync'

    @api.model
    def sync_vendors(self):
        """
            Synchronize vendor users from CS-Cart into Odoo.

            This method fetches vendor-type users (``user_type = 'V'``) from
            CS-Cart using paginated API requests and creates or updates
            corresponding vendor partner records in Odoo.
        """
        api = self.env["cs.cart.api"]
        Partner = self.env["res.partner"].sudo()

        page = 1
        items_per_page = 50
        total_created = 0

        while True:
            res = api.request(
                "GET",
                "users",
                params={
                    "user_type": "V",
                    "page": page,
                    "items_per_page": items_per_page,
                }
            )
            vendors = res.get("users") or []
            params = res.get("params") or {}

            if not vendors:
                break

            for vendor in vendors:
                try:
                    self._sync_single_vendor(vendor, Partner)
                    total_created += 1
                except Exception:
                    _logger.exception(
                        "Failed to sync vendor user_id=%s",
                        vendor.get("user_id"),
                    )

            total_items = int(params.get("total_items") or 0)
            if page * items_per_page >= total_items:
                break

            page += 1

        return {
            "success": True,
        }

    def _sync_single_vendor(self, vendor, Partner):
        """
            Create or update a single vendor in Odoo from CS-Cart data.

            This method retrieves detailed vendor information from CS-Cart
            and maps it to an Odoo partner record. Vendors are matched using
            the CS-Cart user ID.

            If a matching partner exists, it is updated. Otherwise, a new
            vendor partner is created.
        """
        api = self.env["cs.cart.api"]

        user_id = vendor.get("user_id")
        if not user_id:
            return

        details = api.request("GET", f"users/{user_id}")
        email = details.get("email")
        name = (
                details.get("company_name")
                or details.get("company")
                or f"{details.get('firstname', '')} {details.get('lastname', '')}".strip()
                or email
                or f"CS-Vendor-{user_id}"
        )

        partner = Partner.search(
            [("cs_cart_user_id", "=", user_id)],
            limit=1,
        )

        vals = {
            "name": name,
            "email": email,
            "phone": details.get("phone"),
            "street": details.get("address"),
            "street2": details.get("address_2"),
            "city": details.get("city"),
            "zip": details.get("zipcode"),
            "supplier_rank": 1,
            "company_type": "company",
            "is_company": True,
            "cs_cart_user_id": user_id,
            "active": True,
        }

        if partner:
            partner.write(vals)
        else:
            Partner.create(vals)
