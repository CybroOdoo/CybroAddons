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
from odoo import api, models

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class CsCartProductSync(models.Model):
    """
    This model is responsible for synchronizing Product
    records from CS-Cart into Odoo. It fetches product data via the
    CS-Cart API
    """
    _name = 'cs.cart.product.sync'
    _description = 'CS-Cart Product Sync'

    def _update_product_stock(self, product, quantity):
        """Apply imported on-hand stock to the main warehouse stock location."""
        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not location:
            return

        StockQuant = self.env['stock.quant'].sudo().with_context(
            inventory_mode=True,
            cs_cart_skip_stock_sync=True
        )
        quant = StockQuant.search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ], limit=1)

        if quant:
            quant.write({'inventory_quantity': quantity})
        else:
            quant = StockQuant.create({
                'product_id': product.id,
                'location_id': location.id,
                'inventory_quantity': quantity,
            })
        quant.action_apply_inventory()

    @api.model
    def sync_products(self, batch=None):
        """
        Synchronize products from CS-Cart to Odoo.

        :param batch: optional import batch record tracking progress
        """
        api = self.env['cs.cart.api']

        Product = self.env['product.product'].sudo().with_context(
            tracking_disable=True,
            mail_notrack=True,
            no_recompute=True,
            cs_cart_skip_stock_sync=True,
        )

        page = 1
        items_per_page = 200
        total_created = 0
        total_updated = 0


        existing_products = Product.search([
            '|',
            ('cs_cart_product_id', '!=', False),
            ('default_code', '!=', False),
        ])

        product_by_cs_id = {
            p.cs_cart_product_id: p
            for p in existing_products
            if p.cs_cart_product_id
        }

        product_by_code = {
            p.default_code: p
            for p in existing_products
            if p.default_code
        }
        while True:
            if batch and batch.state == 'cancelled':
                break
            res = api.request(
                "GET",
                "products",
                params={
                    "page": page,
                    "items_per_page": items_per_page,
                    "fields": "product_id,product,product_code,price,full_description,amount",
                }
            )

            products = res.get("products") or []
            params = res.get("params") or {}

            if not products:
                break

            to_create = []

            for prod in products:
                product_id = prod.get("product_id")
                code = prod.get("product_code")

                if not product_id:
                    continue

                cs_product_id = int(product_id)
                product = product_by_cs_id.get(cs_product_id)

                if not product and code:
                    matching_code_product = product_by_code.get(code)
                    if matching_code_product:
                        # Only match by default_code if the Odoo product is not already linked to another CS-Cart ID
                        if not matching_code_product.cs_cart_product_id or matching_code_product.cs_cart_product_id == cs_product_id:
                            product = matching_code_product
                        else:
                            # Log a warning about duplicate codes in CS-Cart and import as separate product
                            _logger.warning(
                                f"CS-Cart Product ID {cs_product_id} (\"{prod.get('product')}\") shares the identical product code \"{code}\" with CS-Cart Product ID {matching_code_product.cs_cart_product_id}. Created a separate product in Odoo."
                            )

                vals = {
                    "name": prod.get("product") or f"CS-Product-{cs_product_id}",
                    "default_code": code,
                    "list_price": float(prod.get("price") or 0.0),
                    "description_sale": prod.get("full_description"),
                    "type": "consu",
                    "is_storable": True,
                    "cs_cart_product_id": cs_product_id,
                }

                if product:
                    product.write(vals)
                    self._update_product_stock(product, float(prod.get("amount") or 0.0))
                    total_updated += 1
                else:
                    to_create.append((vals, float(prod.get("amount") or 0.0)))
                    total_created += 1

            if to_create:
                created = Product.create([vals for vals, qty in to_create])
                for p, (_, qty) in zip(created, to_create):
                    product_by_cs_id[p.cs_cart_product_id] = p
                    if p.default_code:
                        product_by_code[p.default_code] = p
                    self._update_product_stock(p, qty)

            total_items = int(params.get("total_items") or 0)
            if page * items_per_page >= total_items:
                break

            page += 1


        return {
            "success": True,
            "created": total_created,
            "updated": total_updated,
        }

    @job
    def import_products_queue(self, batch_id):
        """Queue Job wrapper for product sync"""
        batch = self.env['cs.cart.import.batch'].browse(batch_id)
        if batch.state == 'cancelled':
            return
        batch.write({'state': 'in_progress', 'log_notes': '<p class="text-info">Product sync started...</p>'})
        try:
            res = self.sync_products(batch)
            if batch.state == 'cancelled':
                return
            batch.write({
                'state': 'done',
                'log_notes': (batch.log_notes or '') + f'<p class="text-success">🎉 Products imported successfully. Created: {res.get("created", 0)}, Updated: {res.get("updated", 0)}</p>'
            })
        except Exception as e:
            if batch.state == 'cancelled':
                return
            batch.write({'state': 'failed', 'log_notes': (batch.log_notes or '') + f'<p class="text-danger">❌ Error: {str(e)}</p>'})
