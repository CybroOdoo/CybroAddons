# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class LeadProduct(models.Model):
    _inherit = 'crm.lead'

    pdt_line = fields.One2many('crm.product_line', 'pdt_crm', string="Product")

    def sale_action_quotations_new(self):
        vals = {'partner_id': self.partner_id.id,
                'user_id': self.user_id.id,
                }
        sale_order = self.env['sale.order'].create(vals)
        order_line = self.env['sale.order.line']
        for data in self.pdt_line:
            pdt_value = {
                        'order_id': sale_order.id,
                        'product_id': data.product_id.id,
                        'name': data.name,
                        'product_uom_qty': data.product_uom_qty,
                        'uom_id': data.uom_id.id
                }
            order_line.create(pdt_value)
        view_id = self.env.ref('sale.view_order_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': sale_order.id,
            'view_id': view_id.id,
        }


class LeadProductLine(models.Model):
    _name = 'crm.product_line'

    product_id = fields.Many2one('product.product', string="Product",
                                 change_default=True, ondelete='restrict', required=True)

    name = fields.Text(string='Description')
    pdt_crm = fields.Many2one('crm.lead')
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Cost Price')
    market_price = fields.Float(string='Sale Price')
    qty_hand = fields.Integer(string='Quantity On Hand')
    uom_id = fields.Many2one('product.uom', 'Unit of Measure')

    @api.onchange('product_id')
    def product_data(self):
        data = self.env['product.template'].search([('name', '=', self.product_id.name)])
        self.name = data.name
        self.price_unit = data.list_price
        self.uom_id = data.uom_id
        self.market_price = data.standard_price
        self.qty_hand = data.qty_available
