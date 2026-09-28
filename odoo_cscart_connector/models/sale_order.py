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


class SaleOrder(models.Model):
    """
    Extends sale.order model to include capabilities for exporting orders to CS-Cart.
    """
    _inherit = "sale.order"

    cs_cart_order_id = fields.Integer(string="CS-Cart Order ID", index=True, copy=False)

    def _queue_job_available(self):
        """
        Check if queue_job is configured server-wide.

        :return: True if queue_job is enabled server-wide, else False
        :rtype: bool
        """
        server_wide = config.get("server_wide_modules") or ""
        modules = {m.strip() for m in server_wide.split(",")} if isinstance(server_wide, str) else set(server_wide)
        return "queue_job" in modules

    def action_export_to_cs_cart(self):
        """
        Export selected sales orders from Odoo to CS-Cart.

        :return: Client action web notification dictionary
        :rtype: dict
        """
        if self._queue_job_available():
            self.with_delay(description="Exporting orders to CS-Cart")._export_to_cs_cart_job(self.ids)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("CS-Cart"),
                    "message": _("Order export job queued in the background."),
                    "type": "info",
                    "sticky": False,
                },
            }
        return self._export_to_cs_cart_sync()

    @job
    def _export_to_cs_cart_job(self, order_ids):
        """
        Queue Job worker method to export orders asynchronously.

        :param order_ids: List of sale.order record IDs
        :type order_ids: list[int]
        """
        orders = self.browse(order_ids)
        orders.with_context(cs_cart_queue_job=True)._export_to_cs_cart_sync()

    def _export_to_cs_cart_sync(self):
        """
        Synchronous export of sales orders to CS-Cart.

        :return: Client action web notification dictionary
        :rtype: dict
        :raises UserError: If export fails in queue job context.
        """
        api = self.env["cs.cart.api"]
        exported = 0
        failed_orders = []

        payment_id = "1"
        shipping_id = "1"
        store_id = 1

        try:
            stores_res = api.request("GET", "stores")
            stores = stores_res.get("stores") or []
            if stores:
                store_id = str(stores[0].get("company_id") or "1")
        except Exception as e:
            _logger.warning("CS-Cart: Failed to fetch stores, defaulting store_id to 1: %s", str(e))

        for order in self:
            try:
                payload = self._prepare_cs_cart_order_payload(order, payment_id, shipping_id, store_id)

                if order.cs_cart_order_id:
                    api.request(
                        "PUT",
                        f"orders/{order.cs_cart_order_id}?company_id={store_id}",
                        data=payload,
                    )
                    cs_id = order.cs_cart_order_id
                else:
                    _logger.info("CSCArt:store id=%s",store_id)
                    _logger.info("CSCArt:creating order %s",order.name)
                    _logger.info("CSCArt:order payload =%s",payload)


                    res = api.request(
                        "POST",
                        f"stores/{store_id}/orders",
                        data=payload,
                    )

                    cs_id = res.get("order_id") if isinstance(res, dict) else None
                    if cs_id:
                        order.cs_cart_order_id = int(cs_id)
                        order.origin = f"CS-{cs_id}"
                    else:
                        raise UserError(_("CS-Cart API did not return an order_id. Response: %s") % str(res))

                exported += 1

            except Exception as e:
                err_msg = str(e)
                _logger.error("Export failed for order %s: %s", order.name, err_msg)
                failed_orders.append((order.name, err_msg))

        if failed_orders:
            if self.env.context.get("cs_cart_queue_job"):
                raise UserError(
                    _("Export failed for some orders: %s")
                    % "; ".join([f"{name}: {err}" for name, err in failed_orders])
                )

            messages = [
                _("Successfully exported: %s") % exported,
                _("Failed: %s") % len(failed_orders),
            ]
            for name, err in failed_orders:
                messages.append(f"- {name}: {err}")

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("CS-Cart Export Completed with Warnings"),
                    "message": "\n".join(messages),
                    "type": "warning",
                    "sticky": True,
                },
            }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CS-Cart Export Completed"),
                "message": _("%s order(s) exported successfully") % exported,
                "type": "success",
            },
        }

    def _prepare_cs_cart_order_payload(self, order, payment_id="1", shipping_id="1", company_id=1):
        """
        Prepare the order creation/update payload dictionary for CS-Cart REST API.
        """
        api = self.env["cs.cart.api"]
        partner = order.partner_id
        _logger.info("cascart: patt= %s |namw=%s|cscartttt userid=%s",partner.id,partner.name,partner.cs_cart_user_id,)

        # 1. Resolve User ID (with fallback to 0 for guest checkout)
        user_id = 0
        if partner:
            if not partner.cs_cart_user_id:
                try:
                    partner._export_to_cs_cart_sync()
                except Exception as e:
                    _logger.warning("Could not sync customer %s, proceeding as guest: %s", partner.name, str(e))

            # if partner.cs_cart_user_id:
            #     user_id = partner.cs_cart_user_id
            user_id = 0

        # 2. Build Products dictionary
        products = {}
        idx = 1

        for line in order.order_line:
            if line.display_type:
                continue
            if line.product_id.default_code in ("CS_SHIPPING", "CS_DISCOUNT"):
                continue

            if not line.product_id.cs_cart_product_id:
                try:
                    line.product_id._export_to_cs_cart_sync()
                except Exception as e:
                    _logger.warning("Could not sync product %s: %s", line.product_id.display_name, str(e))

            cs_prod_id = line.product_id.cs_cart_product_id
            if not cs_prod_id:
                _logger.error("Product %s has no CS-Cart Product ID.", line.product_id.display_name)
                raise UserError(_("Could not export product %s to CS-Cart.") % line.product_id.display_name)

            # Prevent "zero inventory" error in CS-Cart
            try:
                api.request(
                    "PUT",
                    f"products/{cs_prod_id}",
                    data={"amount": 9999, "tracking": "D"},
                )
            except Exception as e:
                _logger.warning("Could not update tracking for product %s: %s", cs_prod_id, str(e))

            qty = line.product_uom_qty
            products[str(idx)] = {
                "product_id": str(cs_prod_id),
                "amount": int(qty) if qty.is_integer() else float(qty),
                "price": round(line.price_unit, 2),
            }
            idx += 1

        if not products:
            _logger.error("No valid exportable products found in order %s!", order.name)
            raise UserError(_("No valid products found in order %s to export.") % order.name)

        status_map = {
            "draft": "O",
            "sent": "O",
            "sale": "P",
            "done": "C",
            "cancel": "I",
        }
        status = status_map.get(order.state, "O")

        names = (partner.name or "").strip().split(" ", 1) if partner else ["Customer"]
        firstname = names[0] if names else "Customer"
        lastname = names[1] if len(names) > 1 else ""

        ship_partner = order.partner_shipping_id or partner
        ship_names = (ship_partner.name or "").strip().split(" ", 1) if ship_partner else [firstname]
        s_firstname = ship_names[0] if ship_names else firstname
        s_lastname = ship_names[1] if len(ship_names) > 1 else lastname

        payload = {
            "company_id": str(company_id),
            "user_id": str(user_id),
            "payment_id": str(payment_id),
            "shipping_id": {
                "0": str(shipping_id)
            },
            "shipping_ids": [str(shipping_id)],
            "status": status,
            "products": products,
            "user_data": {
                "email": (partner.email if partner and partner.email else f"customer_{order.id}@domain.com"),
                "b_firstname": firstname,
                "b_lastname": lastname,
                "b_address": (partner.street or "") if partner else "",
                "b_address_2": (partner.street2 or "") if partner else "",
                "b_city": (partner.city or "") if partner else "",
                "b_zipcode": (partner.zip or "") if partner else "",
                "b_country": (partner.country_id.code if partner and partner.country_id else "US"),
                "b_state": (partner.state_id.code if partner and partner.state_id else ""),
                "b_phone": (partner.phone or partner.mobile or "") if partner else "",
                "s_firstname": s_firstname,
                "s_lastname": s_lastname,
                "s_address": (ship_partner.street or partner.street or "") if (ship_partner or partner) else "",
                "s_address_2": (ship_partner.street2 or partner.street2 or "") if (ship_partner or partner) else "",
                "s_city": (ship_partner.city or partner.city or "") if (ship_partner or partner) else "",
                "s_zipcode": (ship_partner.zip or partner.zip or "") if (ship_partner or partner) else "",
                "s_country": (
                    ship_partner.country_id.code
                    if ship_partner and ship_partner.country_id
                    else (partner.country_id.code if partner and partner.country_id else "US")
                ),
                "s_state": (
                    ship_partner.state_id.code
                    if ship_partner and ship_partner.state_id
                    else (partner.state_id.code if partner and partner.state_id else "")
                ),
                "s_phone": (
                    ship_partner.phone
                    or ship_partner.mobile
                    or (partner.phone if partner else "")
                    or ""
                ),
            },
        }
        return payload

