# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class ProductTemplate(models.Model):
    """Inherits the product template for adding fields and methods"""
    _inherit = 'product.template'

    stock_warehouse_id = fields.Many2one('stock.warehouse',
                                         string='Warehouse',
                                         help="Warehouse Selection",
                                         domain="[('company_id', '=', "
                                                "company_id)]")
    quantity = fields.Float(string='On Hand',
                            help=' for Quantity')
    revenue = fields.Float(string="Revenue",
                           help='Float Field for Revenue ')
    total_order = fields.Integer(string="ToTal Order",
                                 help='Float Field for Total Order')
    ordered_quantities = fields.Integer(string="Ordered Quantities",
                                        help='for Ordered Quantities')
    delivered_quantities = fields.Integer(string="Delivered Quantities",
                                          help='for Ordered Quantities')
    returned_quantities = fields.Integer(string="Returned Quantities",
                                         help='for Ordered Quantities')
    avg_price = fields.Float(string="Avg Price", help='Avg Price of Products')
    avg_qty_order = fields.Float(string="Avg Qty Per Order",
                                 help='Average Quantity Order')
    avg_stock = fields.Integer(string="Avg Stock", help='Avg Stock of Products')

    def performance_values(self, start_date, end_date, up_to_date):
        """
        For Calculate Performance Values
        :param start_date: for get records after the date .
        :param end_date: for get records before the date.
        :param up_to_date: for up_to_date records.
        """
        domain = [('product_template_id', '=', self.id)]
        if not up_to_date:
            if start_date:
                domain.append(('order_id.date_order', '>=', start_date))
            if end_date:
                domain.append(('order_id.date_order', '<=', end_date))
        sale_order = self.env['sale.order.line'].search(domain)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id)])
        stock_quant = self.env['stock.quant'].search([
            ('product_id', '=', product_variant[0].id)])
        self.quantity = self.qty_available
        self.stock_warehouse_id = stock_quant.location_id.warehouse_id
        self.delivered_quantities = sum(sale_order.mapped('qty_delivered'))
        self.ordered_quantities = sum(sale_order.mapped('product_uom_qty'))
        self.total_order = len(sale_order)
        self.avg_stock = (self.ordered_quantities / self.total_order) \
            if self.total_order != 0 else 0
        self.avg_qty_order = self.delivered_quantities / self.total_order \
            if self.total_order != 0 else 0.00
        self.avg_price = (sum(sale_order.mapped('price_unit')) /
                          self.total_order) if self.total_order != 0 else 0.00
        self.revenue = 0
        for line in sale_order:
            self.revenue += line.price_subtotal
            return_qty = self.env['stock.move'].search(
                [('sale_line_id', '=', line.id),
                 ('picking_id.sale_id', '=', line.order_id.id),
                 ('picking_type_id.code', '=', 'incoming')])
            if return_qty.quantity:
                self.returned_quantities = return_qty.quantity

    def action_sale_order(self):
        """
            action for get sale orders done with this product
            return: to sale order tree view and form view
        """
        domain = [('product_template_id', '=', self.id)]
        if not self._context['up_to_date']:
            if self._context['start_date']:
                domain.append(
                    ('order_id.date_order', '>=', self._context['start_date']))
            if self._context['end_date']:
                domain.append(
                    ('order_id.date_order', '<=', self._context['end_date']))
        sale_order = self.env['sale.order.line'].search(domain)
        orders = [order.order_id.id for order in sale_order]
        tree_view_id = request.env.ref(
            'sale.view_order_tree').id
        form_view_id = request.env.ref(
            'sale.view_order_form').id
        if orders:
            return {
                'name': _('Product Performance Report'),
                'res_model': 'sale.order',
                'views': [(tree_view_id, 'list'), (form_view_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'self',
                'domain': [('id', 'in', orders)]
            }
        else:
            raise UserError(_("No Orders with this Product!"))
