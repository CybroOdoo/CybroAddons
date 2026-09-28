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
from datetime import datetime
from odoo import models, api, _
from odoo.exceptions import ValidationError

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    def job(func):
        """Fallback decorator when queue_job is not installed."""
        return func

_logger = logging.getLogger(__name__)


class CSCartOrderSync(models.Model):
    """
    This model is responsible for synchronizing Order
    records from CS-Cart into Odoo. It fetches order data via the
    CS-Cart API
    """
    _name = "cs.cart.order.sync"
    _description = "CS-Cart Order Sync"

    @api.model
    def sync_orders(self, batch=None):
        """
                     Synchronize a single CS-Cart order into Odoo.

                     This method:
                     - Checks for existing orders using CS-Cart reference
                     - Fetches full order details from CS-Cart
                     - Creates the sales order in Odoo
                     - Adds order lines, taxes, shipping, and discounts
                     - Confirms or cancels the order based on CS-Cart status
                 """
        self = self.with_context(cs_cart_skip_stock_sync=True)
        api = self.env["cs.cart.api"]

        SaleOrder = self.env["sale.order"].sudo()
        Partner = self.env["res.partner"].sudo()
        Product = self.env["product.product"].sudo()
        Tax = self.env["account.tax"].sudo()
        Carrier = self.env["delivery.carrier"].sudo()

        partner_cache = {
            p.email: p for p in Partner.search([("email", "!=", False)])
        }

        product_cache_cs = {
            p.cs_cart_product_id: p
            for p in Product.search([("cs_cart_product_id", "!=", False)])
        }

        product_cache_code = {
            p.default_code: p
            for p in Product.search([("default_code", "!=", False)])
        }

        tax_cache = {
            (t.name, t.amount): t
            for t in Tax.search([("type_tax_use", "=", "sale")])
        }

        carrier_cache = {
            c.name: c for c in Carrier.search([])
        }

        page, per_page = 1, 50
        total_created = 0
        total_skipped = 0

        while True:
            if batch and batch.state == 'cancelled':
                break
            res = api.request("GET", "orders", {
                "page": page,
                "items_per_page": per_page,
                "include": "products,taxes,shipping",
            })

            orders = res.get("orders") or []
            if not orders:
                break

            for order in orders:
                order_id = order.get("order_id")
                origin = f"CS-{order_id}"

                try:
                    with self.env.cr.savepoint():
                        if SaleOrder.search([("origin", "=", origin)], limit=1):
                            total_skipped += 1
                            continue

                        self._sync_single_order_fast(
                            api, order,
                            partner_cache,
                            product_cache_cs,
                            product_cache_code,
                            tax_cache,
                            carrier_cache,
                        )
                        total_created += 1
                except ValidationError as e:
                    if "CS_CART_IMPORT_PRODUCTS_REQUIRED" in str(e):
                        return {
                            "success": False,
                            "reason": "missing_products",
                            "message": _("Please import products from CS-Cart first."),
                        }
                    raise
                except Exception:
                    _logger.exception("Failed to sync order %s", order_id)

            total = int(res.get("params", {}).get("total_items", 0))
            if page * per_page >= total:
                break
            page += 1

        return {"success": True, "created": total_created, "skipped": total_skipped}

    def _get_or_create_order_partner(self, details, partner_cache):
        """Resolve the order customer and create it when it is missing in Odoo."""
        Partner = self.env["res.partner"].sudo()

        user_id = details.get("user_id")
        email = details.get("email")

        firstname = details.get("firstname", "") or ""
        lastname = details.get("lastname", "") or ""
        name = f"{firstname} {lastname}".strip()
        if not name:
            name = email or f"CS-Customer-{user_id or details.get('order_id')}"
        normalized_name = " ".join(name.split()).casefold()

        partner = None
        guest_key = None
        is_registered_customer = bool(user_id and str(user_id) != "0")

        if is_registered_customer:
            if user_id:
                partner = Partner.search([("cs_cart_user_id", "=", user_id)], limit=1)
            if not partner and email:
                partner = partner_cache.get(email)
                if partner and partner.cs_cart_user_id not in (False, user_id):
                    partner = None
            if not partner and email:
                partner = Partner.search([
                    ("email", "=", email),
                    "|",
                    ("cs_cart_user_id", "=", False),
                    ("cs_cart_user_id", "=", user_id),
                ], limit=1)
        else:
            guest_key = (email or "", normalized_name)
            partner = partner_cache.get(guest_key)
            if not partner and email:
                guest_partners = Partner.search([("email", "=", email)])
                partner = next(
                    (
                        rec for rec in guest_partners
                        if " ".join((rec.name or "").split()).casefold() == normalized_name
                    ),
                    False,
                )

        vals = {
            "name": name,
            "email": email,
            "phone": details.get("phone"),
            "street": details.get("address"),
            "street2": details.get("address_2"),
            "city": details.get("city"),
            "zip": details.get("zipcode"),
            "customer_rank": 1,
        }
        if is_registered_customer:
            vals["cs_cart_user_id"] = user_id

        if partner:
            partner.write(vals)
        else:
            partner = Partner.create(vals)

        if is_registered_customer and email:
            partner_cache[email] = partner
        elif guest_key:
            partner_cache[guest_key] = partner
        return partner

    def _get_or_create_tax(self, name, rate, tax_cache):
        """Return a valid sale tax record, recreating stale cached records when needed."""
        Tax = self.env["account.tax"].sudo()
        key = (name, rate)
        tax = tax_cache.get(key)
        if tax:
            tax = tax.exists()
        if not tax:
            tax = Tax.search([
                ("name", "=", name),
                ("amount", "=", rate),
                ("type_tax_use", "=", "sale"),
                ("company_id", "=", self.env.company.id),
            ], limit=1)
        if not tax:
            tax = Tax.create({
                "name": name,
                "amount": rate,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": self.env.company.id,
            })
        tax_cache[key] = tax
        return tax

    def _get_or_create_shipping_product(self):
        """Delivery carriers require a delivery product."""
        Product = self.env["product.product"].sudo()
        product = Product.search([("default_code", "=", "CS_SHIPPING")], limit=1)
        if not product:
            product = Product.create({
                "name": "CS-Cart Shipping",
                "default_code": "CS_SHIPPING",
                "type": "service",
                "list_price": 0.0,
            })
        return product

    def _get_or_create_shipping_carrier(self, name, shipping_cost, carrier_cache):
        """Return a valid fixed-price carrier with its required delivery product."""
        Carrier = self.env["delivery.carrier"].sudo()
        carrier = carrier_cache.get(name)
        if carrier:
            carrier = carrier.exists()
        if not carrier:
            carrier = Carrier.search([("name", "=", name)], limit=1)
        if carrier:
            carrier.write({"fixed_price": shipping_cost})
        else:
            carrier = Carrier.create({
                "name": name,
                "delivery_type": "fixed",
                "fixed_price": shipping_cost,
                "product_id": self._get_or_create_shipping_product().id,
            })
        carrier_cache[name] = carrier
        return carrier

    def _sync_single_order_fast(self, api, order,partner_cache, product_cache_cs, product_cache_code,
                                tax_cache, carrier_cache,):
        """
            This method converts one CS-Cart order into an Odoo ``sale.order`` using
            preloaded in-memory caches to minimize database queries and API cal
        """

        SaleOrder = self.env["sale.order"].sudo()

        order_id = order["order_id"]
        details = api.request("GET", f"orders/{order_id}")

        partner = self._get_or_create_order_partner(details, partner_cache)

        so = SaleOrder.create({
            "partner_id": partner.id,
            "origin": f"CS-{order_id}",
            "cs_cart_order_id": int(order_id),
            "date_order": datetime.fromtimestamp(int(details["timestamp"])),
        })

        tax_ids = []
        primary_tax_rate = 0.0
        for tax in (details.get("taxes") or {}).values():
            rate = float(tax.get("rate_value") or 0)
            if rate <= 0:
                continue
            tax_record = self._get_or_create_tax(
                tax.get("description") or "VAT",
                rate,
                tax_cache,
            )
            if not primary_tax_rate:
                primary_tax_rate = tax_record.amount
            tax_ids.append(tax_record.id)

        skip = 0
        for item in (details.get("products") or {}).values():
            cs_id = int(item.get("product_id"))
            code = item.get("product_code")

            product = (
                product_cache_cs.get(cs_id)
                or product_cache_code.get(code)
            )

            if not product:
                raise ValidationError("CS_CART_IMPORT_PRODUCTS_REQUIRED")

            price_incl = float(item.get("price") or 0)
            price_excl = price_incl / (1 + primary_tax_rate / 100) if primary_tax_rate else price_incl

            self.env["sale.order.line"].sudo().create({
                "order_id": so.id,
                "product_id": product.id,
                "name": item.get("product"),
                "product_uom_qty": float(item.get("amount") or 1),
                "price_unit": price_excl,
                "tax_ids": [(6, 0, tax_ids)] if tax_ids else False,
            })

        shipping_cost = float(details.get("shipping_cost") or 0)
        if shipping_cost:
            name = "CS-Cart Shipping"
            shipping = (details.get("shipping") or [])
            if shipping:
                name = shipping[0].get("shipping") or name

            carrier = self._get_or_create_shipping_carrier(name, shipping_cost, carrier_cache)
            so.set_delivery_line(carrier, shipping_cost)

        discount = float(details.get("discount") or 0)
        if discount:
            product = self.env["product.product"].sudo().search(
                [("default_code", "=", "CS_DISCOUNT")], limit=1
            )
            if not product:
                product = self.env["product.product"].sudo().create({
                    "name": "CS-Cart Discount",
                    "default_code": "CS_DISCOUNT",
                    "type": "service",
                })
            self.env["sale.order.line"].sudo().create({
                "order_id": so.id,
                "product_id": product.id,
                "price_unit": -abs(discount),
                "product_uom_qty": 1,
            })

        if self._map_cs_cart_status(details.get("status")) == "sale":
            so.action_confirm()
        elif self._map_cs_cart_status(details.get("status")) == "cancel":
            so.action_cancel()

    def _map_cs_cart_status(self, cs_status):
        """
          Map CS-Cart order status to Odoo sales order state.
        """
        return {
            "O": "draft",
            "I": "draft",
            "P": "sale",
            "C": "sale",
            "B": "sale",
            "F": "cancel",
            "D": "cancel",
        }.get(cs_status, "draft")

    @job
    def import_orders_queue(self, batch_id):
        """Queue Job wrapper for order sync"""
        batch = self.env['cs.cart.import.batch'].browse(batch_id)
        if batch.state == 'cancelled':
            return
        batch.write({'state': 'in_progress', 'log_notes': '<p class="text-info">Order sync started...</p>'})
        try:
            res = self.sync_orders(batch)
            if batch.state == 'cancelled':
                return
            if isinstance(res, dict) and not res.get("success"):
                batch.write({
                    'state': 'failed',
                    'log_notes': (batch.log_notes or '') + f'<p class="text-warning">⚠️ Order sync stopped. Reason: {res.get("message")}</p>'
                })
            else:
                batch.write({
                    'state': 'done',
                    'log_notes': (batch.log_notes or '') + f'<p class="text-success">🎉 Orders imported successfully. Created: {res.get("created", 0)}, Skipped: {res.get("skipped", 0)}</p>'
                })
        except Exception as e:
            if batch.state == 'cancelled':
                return
            self.env.cr.rollback()
            batch.write({'state': 'failed', 'log_notes': (batch.log_notes or '') + f'<p class="text-danger">❌ Error: {str(e)}</p>'})
