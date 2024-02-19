# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
import requests
from odoo import models, _
from odoo.exceptions import UserError
from odoo.http import request


class SaleOrder(models.Model):
    """Extends the functionality of sale orders by adding
       additional analytics tracking upon confirmation and cart update."""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Supering the function to send analytics data of the sale order.
        :return: Result of confirming the sale order."""
        res = super().action_confirm()
        enable_analytics = self.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics')
        measurement_id = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        if enable_analytics:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
            data = {
                "client_id": str(self.partner_id.id),
                "events": [{
                    "name": "Sales_Order",
                    "params": {
                        "Number": self.name,
                        "Customer": self.partner_id.name,
                        "Amount": self.amount_total,
                    }
                }]
            }
            requests.post(url, json=data)
        return res

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0,
                     **kwargs):
        """ Updates the cart and sends analytics data.

            :param product_id: ID of the product to be updated.
            :param line_id: ID of the order line.
            :param add_qty: Quantity to be added.
            :param set_qty: Quantity to be set.
            :param kwargs: Additional keyword arguments.
            :return: Result of updating the cart."""
        self.ensure_one()
        self = self.with_company(self.company_id)
        if self.state != 'draft':
            request.session.pop('sale_order_id', None)
            request.session.pop('website_sale_cart_quantity', None)
            raise UserError(
                _('It is forbidden to modify a sales order which is not in draft status.'))
        product = self.env['product.product'].browse(product_id).exists()
        if add_qty and (not product or not product._is_add_to_cart_allowed()):
            raise UserError(
                _("The given product does not exist therefore it cannot be added to cart."))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id,
                                                      **kwargs)[:1]
        else:
            order_line = self.env['sale.order.line']
        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            if order_line:
                quantity = order_line.product_uom_qty + (add_qty or 0)
            else:
                quantity = add_qty or 0
        if quantity > 0:
            quantity, warning = self._verify_updated_quantity(
                order_line,
                product_id,
                quantity,
                **kwargs,
            )
        else:
            # If the line will be removed anyway, there is no need to verify
            # the requested quantity update.
            warning = ''
        self._remove_delivery_line()
        order_line = self._cart_update_order_line(product_id, quantity,
                                                  order_line, **kwargs)
        if (order_line
            and order_line.price_unit == 0
            and self.website_id.prevent_zero_price_sale
            and product.detailed_type not in self.env[
            'product.template']._get_product_types_allow_zero_price()
        ):
            raise UserError(_(
                "The given product does not have a price therefore it cannot be added to cart.",
            ))
        enable_analytics = self.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics'),
        measurement_id = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        if enable_analytics:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
            data = {
                "client_id": str(self.env.user.partner_id.id),
                "events": [{
                    "name": "Add_To_Cart",
                    "params": {
                        "Product_Name": order_line.name_short,
                        'Customer': request.env.user.name,
                        "Quantity": order_line.product_qty,
                        "Amount": order_line.price_unit,
                        "Total_Price": order_line.price_total,
                        "Discount": order_line.discount,
                        "Total_Tax": order_line.price_tax,
                    }
                }]
            }
            requests.post(url, json=data)
        return {
            'line_id': order_line.id,
            'quantity': quantity,
            'option_ids': list(set(order_line.option_line_ids.filtered(
                lambda l: l.order_id == order_line.order_id).ids)),
            'warning': warning,
        }
