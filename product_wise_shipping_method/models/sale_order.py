# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from collections import defaultdict
from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """ Inherit sale,so we are getting shipping method corresponding to
    product."""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Create delivery method value for sale order lines with a
         shipping method."""
        if self.website_id:
            return super().action_confirm()
        order_lines_with_shipping = self.order_line.filtered(lambda line: line.product_template_id.shipping_method_id)
        vals_list = [{
                'product_id': line.product_template_id.shipping_method_id.product_id.id,
                'name': line.product_template_id.shipping_method_id.name,
                'product_uom': line.product_template_id.shipping_method_id.product_id.uom_id.id,
                'price_unit': line.product_template_id.shipping_method_id.product_id.list_price,
                'order_id': self.id,
            } for line in order_lines_with_shipping]
        self.env['sale.order.line'].create(vals_list)
        return super().action_confirm()

    def merge_similar_products(self):
        """ merge similar products on order line by adding their quantity."""
        similar_products = defaultdict(
            lambda: {'qty': 0, 'lines_to_remove': []})
        order_line = self.env['sale.order.line']
        for line in self.order_line.sorted():
            key = (line.product_id.id, line.price_unit, line.tax_id)
            similar_products[key]['qty'] += line.product_uom_qty
            similar_products[key]['lines_to_remove'].append(line.id)
        for key,product_info in similar_products.items():
            order_line.browse(product_info['lines_to_remove'][0]).write(
                {'product_uom_qty': product_info['qty']})
            order_line.browse(product_info['lines_to_remove'][1:]).unlink()

    @api.model
    def create(self, vals):
        """ When the products are newly selected in sale order line then they
        are Create on sale order """
        res = super(SaleOrder, self).create(vals)
        res.merge_similar_products()
        return res

    def write(self, vals):
        """ When the products are previously selected then Write similar
         products on sale order """
        res = super(SaleOrder, self).write(vals)
        self.merge_similar_products()
        return res

    def action_open_delivery_wizard(self):
        """Restrict adding a shipping method or open the delivery carrier selection form.
        if product have shipping method then get error message
        if product hasn't shipping method then can open wizard"""
        if any(line.product_template_id.shipping_method_id for line in self.order_line):
            raise UserError('Shipping method is already applied...!!')
        else:
            view_id = self.env.ref('delivery.choose_delivery_carrier_view_form').id
            name = _('Add a shipping method')
            carrier = (
                    self.with_company(self.company_id).partner_shipping_id.property_delivery_carrier_id
                    or self.with_company(
                self.company_id).partner_shipping_id.commercial_partner_id.property_delivery_carrier_id
            )
            return {
                'name': name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'choose.delivery.carrier',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': {
                    'default_order_id': self.id,
                    'default_carrier_id': carrier.id,
                }
            }
