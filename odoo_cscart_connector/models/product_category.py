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

import re
import logging

from difflib import get_close_matches

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    """
    This model handles the seamless export of categories from Odoo to CS-Cart.
    Since products can only be exported if their categories already exist in CS-Cart,
    category export is a prerequisite for product export.
    """
    _inherit = "product.category"

    cs_cart_category_id = fields.Integer(
        string="CS-Cart Category ID",
        index=True,
        copy=False,
    )

    def _normalize(self, name):
        """
            Normalize a category name for reliable comparison.
            This helper converts a category name into a normalized key used
            for matching Odoo categories with CS-Cart categories.
        """
        name = (name or "").lower()
        name = re.sub(r"\bab\b", "", name)
        name = name.replace("&", "and")
        name = re.sub(r"[^a-z0-9]", " ", name)
        name = re.sub(r"\s+", " ", name)
        return name.strip()

    def _cscart_category_exists(self, api, category_id):
        """
            Check whether a CS-Cart category still exists.
            This method verifies the existence of a CS-Cart category by
            attempting to fetch it via the CS-Cart API. If the category
            is not found (404), it is treated as deleted.
        """
        try:
            api.request("GET", f"categories/{category_id}")
            return True
        except UserError as e:
            # Only treat NOT FOUND as deleted
            if "404" in str(e) or "not found" in str(e).lower():
                return False
            raise

    def _create_cscart_category(self, api, name, parent_id=0):
        """
            This method sends a category creation request to CS-Cart using
            the provided name and optional parent category ID. The created
            category is enabled by default and assigned to the root admin
            company.
        """
        storefront_id = self.env.context.get("cscart_storefront_id") or 0

        payload = {
            "category": name,
            "parent_id": parent_id,
            "status": "A",
            "company_id": storefront_id,
            "lang_code": "en",
        }
        if storefront_id:
            payload["storefront_id"] = storefront_id


        try:
            res = api.request(
                "POST",
                "categories",
                data=payload,
            )
        except UserError as e:
            # Check if storefront_id is required
            if "storefront_id" in str(e).lower() or "storefront id" in str(e).lower():
                try:
                    stores_res = api.request("GET", "stores")
                    stores = stores_res.get("stores") or []
                    if stores:
                        store_id = int(stores[0].get("company_id") or 1)
                        payload["company_id"] = store_id
                        payload["storefront_id"] = store_id
                        res = api.request("POST", "categories", data=payload)
                    else:
                        raise e
                except Exception:
                    raise e
            else:
                raise e


        if isinstance(res, dict) and res.get("category_id"):
            return int(res["category_id"])

        return False

    def _reconcile_cscart_categories(self, categories, cscart_map):
        """
            If CS-Cart does NOT have the category name,
            reset cs_cart_category_id in Odoo
        """
        for category in categories:
            if not category.cs_cart_category_id:
                continue

            odoo_key = self._normalize(category.name)

            if odoo_key not in cscart_map:
                _logger.warning(
                    "RESET CS-CART CATEGORY ID → %s (was %s)",
                    category.name,
                    category.cs_cart_category_id,
                )
                category.cs_cart_category_id = False

    def _export_single_category_to_cscart(self, api, category, cscart_map):
        """
            Export or reconcile a single Odoo category with CS-Cart.
            This method attempts to match an Odoo product category with an
            existing CS-Cart category.
        """
        odoo_key = self._normalize(category.name)

        if category.cs_cart_category_id:
            if self._cscart_category_exists(api, category.cs_cart_category_id):
                cscart_map.setdefault(
                    odoo_key,
                    category.cs_cart_category_id
                )
                return "present"
            else:
                category.cs_cart_category_id = False

        if odoo_key in cscart_map:
            category.cs_cart_category_id = cscart_map[odoo_key]
            return "present"

        close = get_close_matches(
            odoo_key,
            cscart_map.keys(),
            n=1,
            cutoff=0.80,
        )

        if close:
            category.cs_cart_category_id = cscart_map[close[0]]
            cscart_map[odoo_key] = category.cs_cart_category_id
            return "present"

        parent_id = (
            category.parent_id.cs_cart_category_id
            if category.parent_id and category.parent_id.cs_cart_category_id
            else 0
        )

        new_id = self._create_cscart_category(
            api=api,
            name=category.name,
            parent_id=parent_id,
        )

        if new_id:
            category.cs_cart_category_id = new_id
            cscart_map[odoo_key] = new_id
            return "created"

        return "failed"


    @api.model
    def export_categories_to_cscart(self):
        """
            Export and reconcile Odoo product categories with CS-Cart.
            This method synchronizes Odoo product categories with CS-Cart
        """
        api = self.env["cs.cart.api"]

        store_id = 0
        try:
            stores_res = api.request("GET", "stores")
            stores = stores_res.get("stores") or []
            if stores:
                store_id = int(stores[0].get("company_id") or 1)
        except Exception:
            pass

        res = api.request("GET", "categories", params={"items_per_page": 500})
        cscart_categories = res.get("categories", [])

        cscart_map = {
            self._normalize(cat["category"]): int(cat["category_id"])
            for cat in cscart_categories
        }

        odoo_categories = (self if self else self.env["product.category"].search([])) \
            .sorted(lambda c: c.complete_name.count("/"))

        self._reconcile_cscart_categories(odoo_categories, cscart_map)

        stats = {
            "present": 0,
            "created": 0,
            "failed": 0,
        }

        for category in odoo_categories:
            result = category.with_context(cscart_storefront_id=store_id)._export_single_category_to_cscart(
                api, category, cscart_map
            )
            stats[result] += 1

        return stats

    def _queue_job_available(self):
        """Check if queue_job addon is configured in server wide modules."""
        from odoo.tools import config
        server_wide = config.get('server_wide_modules') or ''
        modules = {m.strip() for m in server_wide.split(',')} if isinstance(server_wide, str) else set(server_wide)
        return 'queue_job' in modules

    def action_export_to_cs_cart(self):
        """
            Trigger CS-Cart category export and display the result.
            This action calls the category export routine and displays
            a user-facing notification summarizing the outcome
        """
        if self._queue_job_available():
            self.with_delay(description="Exporting categories to CS-Cart")._export_categories_job(self.ids)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("CS-Cart Category Export"),
                    "message": _("Category export job queued in the background."),
                    "type": "info",
                    "sticky": False,
                },
            }
        return self._export_categories_sync()

    @job
    def _export_categories_job(self, category_ids):
        """Background queue job handler for category export."""
        categories = self.browse(category_ids)
        categories._export_categories_sync()

    def _export_categories_sync(self):
        """Synchronous category export action and user notification runner."""
        stats = self.export_categories_to_cscart()

        if not any(stats.values()):
            message = _("No categories to export.")
            msg_type = "info"
        else:
            messages = []

            if stats["present"]:
                messages.append(
                    _("Already present in CS-Cart: %s") % stats["present"]
                )

            if stats["created"]:
                messages.append(
                    _("Newly created in CS-Cart: %s") % stats["created"]
                )

            if stats["failed"]:
                messages.append(
                    _("Failed to export: %s") % stats["failed"]
                )

            message = "\n".join(messages)
            msg_type = "danger" if stats["failed"] else "success"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CS-Cart Category Export"),
                "message": message,
                "type": msg_type,
                "sticky": False,
            },
        }
