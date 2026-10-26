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
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """ Inheriting sale.order.line to flag lines that come from a duplicated
    sale order, so no shipping line is added for them again. """
    _inherit = "sale.order.line"

    is_duplicated = fields.Boolean(default=False, copy=False)


class SaleOrder(models.Model):
    """ Inheriting sale.order, so we are getting shipping method corresponding
    to the product. """
    _inherit = 'sale.order'

    def action_confirm(self):
        """ Create delivery lines from the product shipping methods.
        Website orders skip this logic. """
        orders = self.filtered(
            lambda order: order.state in ('draft', 'sent')
            and not order.website_id)
        vals_list = []
        for order in orders:
            vals_list += order._prepare_shipping_line_vals_list()
        if vals_list:
            self.env['sale.order.line'].create(vals_list)
        orders.merge_similar_products()
        return super().action_confirm()

    def _prepare_shipping_line_vals_list(self):
        """ Prepare the delivery line values of the order. A line gets a
        delivery line only if its product has a shipping method and the
        line is not a duplicated one. """
        self.ensure_one()
        order_lines_with_shipping = self.order_line.filtered(
            lambda line: line.product_template_id.shipping_method_id
            and not line.is_duplicated)
        vals_list = []
        for line in order_lines_with_shipping:
            carrier = line.product_template_id.shipping_method_id
            vals_list.append({
                'product_id': carrier.product_id.id,
                'name': carrier.name,
                'product_uom_id': carrier.product_id.uom_id.id,
                'price_unit': carrier.product_id.list_price,
                'order_id': self.id,
            })
        return vals_list

    def merge_similar_products(self):
        """ Merge similar products on the order lines by adding their
        quantities. Only draft and sent orders are merged, and section,
        note and product-less lines are never touched. Lines are similar
        when product, unit, price, taxes, discount and description match. """
        for order in self.filtered(lambda o: o.state in ('draft', 'sent')):
            similar_lines = defaultdict(lambda: order.order_line.browse())
            for line in order.order_line.sorted():
                if line.display_type or not line.product_id:
                    continue
                key = (line.product_id.id, line.product_uom_id.id,
                       line.price_unit, line.tax_ids, line.discount,
                       line.name)
                similar_lines[key] |= line
            for lines in similar_lines.values():
                if len(lines) < 2:
                    continue
                lines[0].product_uom_qty = sum(lines.mapped('product_uom_qty'))
                lines[1:].unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """ When products are newly selected in the sale order lines, they
        are created on the sale order and similar lines are merged. """
        orders = super().create(vals_list)
        orders.merge_similar_products()
        return orders

    def write(self, vals):
        """ When order lines are changed, merge the similar products on the
        sale order. """
        res = super().write(vals)
        if 'order_line' in vals:
            self.merge_similar_products()
        return res

    def copy(self, default=None):
        """ Duplicate the sale order and mark its lines as duplicated, so no
        new shipping line is added when the copy is confirmed. """
        new_order = super().copy(default)
        new_order.order_line.write({'is_duplicated': True})
        return new_order

    def action_open_delivery_wizard(self):
        """ Restrict adding a shipping method, or open the delivery carrier
        selection form.
        If a product has a shipping method, an error message is shown.
        If no product has a shipping method, the core wizard is opened. """
        if any(line.product_template_id.shipping_method_id
               for line in self.order_line):
            raise UserError(
                self.env._('A shipping method is already applied.'))
        return super().action_open_delivery_wizard()
