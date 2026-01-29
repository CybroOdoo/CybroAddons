# -*- coding: utf-8 -*-
###################################################################################

#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Swapna V (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api


class POLineHistory(models.TransientModel):
    _name = "po.line.history"

    order_id = fields.Many2one('purchase.order')
    product = fields.Many2one('product.product')
    po_order = fields.Many2one('purchase.order', string="Purchase Order")
    unit_price = fields.Float(string="Unit Price")
    quantity = fields.Float(string="Quantity")

    def reorder_product(self):
        order_line_list = self.env['purchase.order'].browse(self.order_id.id)
        ol_list = order_line_list.order_line.ids
        po_line = self.env['purchase.order.line'].create({
            'order_id': self.order_id.id,
            'product_id': self.product.id,
            'name': self.product.name,
            'product_qty': self.quantity,
            'price_unit': self.unit_price,
        })
        ol_list.append(po_line.id)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_history_lines = fields.One2many('po.line.history', 'order_id', string="Purchases")

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        history = []
        for line in res:
            for record in line.order_line:
                domain = record.product_id.id
                PurchaseHistoryLines = self.env['purchase.order'].search([('order_line.product_id', '=', domain)])
                for rec in PurchaseHistoryLines:
                    for m in rec.order_line:
                        po_order_id = rec.id
                        product = m.product_id.id
                        quantity = m.product_qty
                        price_unit = m.price_unit
                        data = self.env['po.line.history'].create({
                            'unit_price': price_unit,
                            'po_order': po_order_id,
                            'product': product,
                            'quantity': quantity,
                            'order_id': res.id,
                        }).id
                        history.append(data)
            if history:
                res.write({'purchase_history_lines': history})
        return res
