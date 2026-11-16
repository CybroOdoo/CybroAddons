# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging
import requests
from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extends the functionality of sale orders by adding
       additional analytics tracking upon confirmation and cart addition."""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Sends Google Analytics event when sale orders are confirmed."""
        res = super().action_confirm()
        try:
            enable_analytics = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.enable_analytics'
            )
            measurement_id = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.measurement_id_analytics'
            )
            api_secret = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.api_secret'
            )
            if enable_analytics and measurement_id and api_secret:
                url = (
                    f"https://www.google-analytics.com/mp/collect"
                    f"?measurement_id={measurement_id}&api_secret={api_secret}"
                )
                for order in self:
                    data = {
                        "client_id": str(order.partner_id.id),
                        "events": [{
                            "name": "Sales_Order",
                            "params": {
                                "Number": order.name,
                                "Customer": order.partner_id.name,
                                "Amount": order.amount_total,
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Sales_Order confirmation error: %s", e)
        return res

    def _cart_add(self, product_id: int, quantity: float = 1.0, *, uom_id: int | None = None, **kwargs) -> dict:
        """Overrides _cart_add to send Add_To_Cart event to Google Analytics in Odoo 20."""
        res = super()._cart_add(product_id=product_id, quantity=quantity, uom_id=uom_id, **kwargs)
        line_id = res.get('line_id')
        if line_id:
            order_line = self.env['sale.order.line'].browse(line_id)
            if order_line.exists():
                self._send_cart_analytics_event(order_line, quantity)
        return res

    def _send_cart_analytics_event(self, order_line, quantity=1.0):
        """Helper to send 'Add_To_Cart' event to Google Analytics."""
        try:
            enable_analytics = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.enable_analytics'
            )
            measurement_id = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.measurement_id_analytics'
            )
            api_secret = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.api_secret'
            )
            if enable_analytics and measurement_id and api_secret:
                url = (
                    f"https://www.google-analytics.com/mp/collect"
                    f"?measurement_id={measurement_id}&api_secret={api_secret}"
                )
                customer_name = self.partner_id.name or self.env.user.name
                data = {
                    "client_id": str(self.env.user.partner_id.id),
                    "events": [{
                        "name": "Add_To_Cart",
                        "params": {
                            "Product_Name": order_line.name_short or order_line.product_id.display_name,
                            "Customer": customer_name,
                            "Quantity": quantity,
                            "Amount": order_line.price_unit,
                            "Total_Price": order_line.price_total,
                            "Discount": order_line.discount,
                            "Total_Tax": order_line.price_tax,
                        }
                    }]
                }
                requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Add_To_Cart error: %s", e)

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """Legacy compatibility wrapper for older _cart_update calls."""
        quantity = add_qty if add_qty else set_qty
        return self._cart_add(product_id=product_id, quantity=quantity or 1.0, **kwargs)
