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
import sys
import time

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func


_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """
    Extends product.product to provide export and stock sync capabilities to CS-Cart.
    """
    _inherit = "product.product"

    cs_cart_product_id = fields.Integer(string="CS-Cart Product ID", index=True)

    def _queue_job_available(self):
        """
        Check if queue_job is configured server-wide.

        :return: True if queue_job is enabled server-wide, else False
        :rtype: bool
        """
        server_wide = config.get('server_wide_modules') or ''
        modules = {m.strip() for m in server_wide.split(',')} if isinstance(server_wide, str) else set(server_wide)
        return 'queue_job' in modules

    def action_export_to_cs_cart(self):
        """
        Export selected products from Odoo to CS-Cart.

        :return: Client action notification dictionary
        :rtype: dict
        """
        if self._queue_job_available():
            self.with_delay(description="Exporting products to CS-Cart")._export_to_cs_cart_job(self.ids)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("CS-Cart"),
                    "message": _("Product export job queued in the background."),
                    "type": "info",
                    "sticky": False,
                },
            }
        return self._export_to_cs_cart_sync()

    @job
    def _export_to_cs_cart_job(self, product_ids):
        """
        Queue Job wrapper for exporting product variants asynchronously.

        :param product_ids: List of product record IDs
        :type product_ids: list[int]
        """
        products = self.browse(product_ids)
        products._export_to_cs_cart_sync()

    def _export_to_cs_cart_sync(self):
        """
        Synchronous export of products from Odoo to CS-Cart.

        :return: Client action notification dictionary
        :rtype: dict
        :raises UserError: If product name or CS-Cart category mapping is missing.
        """
        start_total = time.time()

        api = self.env["cs.cart.api"]

        for idx, product in enumerate(self, 1):
            start_prod = time.time()

            if not product.name:
                raise UserError(_("Product name is required."))
            categ = product.product_tmpl_id.categ_id
            if categ and not categ.cs_cart_category_id:
                cats_to_export = self.env['product.category']
                c = categ
                while c:
                    cats_to_export |= c
                    c = c.parent_id
                cats_to_export.export_categories_to_cscart()

            categ = product.product_tmpl_id.categ_id
            while categ and not categ.cs_cart_category_id:
                categ = categ.parent_id
            if not categ:
                raise UserError(
                    _("No CS-Cart category mapped for product '%s'.")
                    % product.display_name
                )

            category_id = int(categ.cs_cart_category_id)
            payload = {
                "product": product.name,
                "price": float(product.list_price),
                "status": "A",
                "category_ids": [category_id],
            }
            if not product.is_storable:
                payload["tracking"] = "D"
                payload["amount"] = 9999
            else:
                payload["tracking"] = "B"
                payload["amount"] = int(product.qty_available)

            if product.default_code:
                payload["product_code"] = product.default_code

            if product.image_1920:
                base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                image_url = f"{base_url}/web/image/product.product/{product.id}/image_1920"
                payload["main_pair"] = {
                    "detailed": {
                        "image_path": image_url
                    }
                }

            t0 = time.time()
            if product.cs_cart_product_id:
                res = api.request(
                    "PUT",
                    f"products/{product.cs_cart_product_id}",
                    data=payload
                )
            else:
                res = api.request(
                    "POST",
                    "products",
                    data=payload
                )
                cs_id = res.get("product_id")
                if not cs_id:
                    raise UserError(_("CS-Cart did not return product_id"))

                product.cs_cart_product_id = cs_id


        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CS-Cart"),
                "message": _("Products exported successfully"),
                "type": "success",
                "sticky": False,
            },
        }

    def _trigger_cs_cart_stock_sync_from_products(self):
        """
        Identifies affected products and schedules their stock sync to CS-Cart.
        """
        configs = self.env['cs.cart.config'].sudo().search([
            ('connected_status', '=', 'connected'),
            ('realtime_stock_sync', '=', True)
        ])
        if not configs:
            return

        products = self.filtered(lambda p: p.cs_cart_product_id and p.is_storable)
        if not products:
            return

        for config_rec in configs:
            for product in products:
                sync_field = config_rec.stock_sync_type or 'qty_available'
                if 'odoo.addons.queue_job' in sys.modules:
                    identity_key = f"sync_stock_product_{product.id}_config_{config_rec.id}"
                    product.with_delay(
                        description=f"Sync stock for product {product.display_name} to CS-Cart",
                        identity_key=identity_key
                    )._sync_stock_to_cs_cart(config_rec.id, sync_field)
                else:
                    product._sync_stock_to_cs_cart(config_rec.id, sync_field)

    @job
    def _sync_stock_to_cs_cart(self, config_id, sync_field):
        """
        Background job to sync stock of a product to CS-Cart.

        :param config_id: CS-Cart configuration instance ID
        :type config_id: int
        :param sync_field: Field name to fetch stock quantity from ('qty_available' or 'virtual_available')
        :type sync_field: str
        """
        self.ensure_one()
        if not self.cs_cart_product_id:
            return

        qty = int(getattr(self, sync_field, 0.0))
        api = self.env['cs.cart.api'].with_context(cs_cart_config_id=config_id)
        try:
            res = api.request(
                "PUT",
                f"products/{self.cs_cart_product_id}",
                data={"amount": qty}
            )
        except Exception as e:
            if 'odoo.addons.queue_job' in sys.modules:
                raise
            _logger.error("Failed to sync stock for product %s to CS-Cart: %s", self.display_name, str(e))
