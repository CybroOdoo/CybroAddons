# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_details_ids = fields.One2many('order.history.line', 'order_id')

    @api.onchange('partner_id')
    def sale_order_domain(self):
        self.write({'order_details_ids': [(5,)]})
        new_lines = []
        lines = self.env['sale.order.line'].search(
            [('order_id.partner_id', '=', self.partner_id.id), ('order_id.state', 'in', ('sale', 'done'))])
        for rec in lines:
            new_lines.append((0, 0, {
                'name': rec.order_id.name,
                'product_id': rec.product_id,
                'product_uom_qty': rec.product_uom_qty,
                'price_unit': rec.price_unit,
                'tax_id': rec.tax_id,
                'price_subtotal': rec.price_subtotal
            }))
        self.write({'order_details_ids': new_lines})


class OrderHistoryLine(models.Model):
    _name = 'order.history.line'
    _description = 'Order History Line'

    order_id = fields.Many2one('sale.order')
    name = fields.Char('Order')
    product_id = fields.Many2one('product.product')
    product_uom_qty = fields.Integer('Quantity')
    price_unit = fields.Integer('Unit price')
    tax_id = fields.Many2many('account.tax')
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    price_subtotal = fields.Integer(string='Subtotal')

    def action_add(self):
        vals = {
            'order_id': self.order_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'tax_id': self.tax_id.id,
            'price_subtotal': self.price_subtotal,
            'company_id':self.company_id,
        }
        self.env['sale.order.line'].sudo().create(vals)
