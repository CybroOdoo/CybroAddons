# -*- coding: utf-8 -*-
###################################################################################

#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Swapna V(<https://www.cybrosys.com>)
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


from odoo import fields, models, api


class PurchaseOrderLineHistory(models.TransientModel):
    _name = "purchase.order.line.history"

    wizard_id = fields.Many2one('purchaseline.history.wizard')
    po_order = fields.Many2one('purchase.order', string="Purchase Order")
    unit_price = fields.Float(string="Unit Price")
    vendor = fields.Many2one('res.partner', string="Vendor")
    quantity = fields.Float(string="Quantity")
    po_date = fields.Datetime(string="Purchase Date")


class PurchaseOrderlineHistoryWizard(models.TransientModel):
    _name = "purchaseline.history.wizard"

    @api.model
    def action_get_history_lines(self):
        domain = []
        if self._context.get('active_model') == 'product.template':
            domain.append(('product_id.product_tmpl_id', 'in', self._context.get('active_ids')))
        else:
            domain.append(('product_id', 'in', self._context.get('active_ids')))
        PurchaseHistoryLines = self.env['purchase.order.line'].search(domain)
        vals = []
        for line in PurchaseHistoryLines:
            purchase_id = line.order_id
            if purchase_id.state in ['purchase', 'done']:
                po_order_id = line.order_id.id
                vendor = purchase_id.partner_id.id
                quantity = line.product_qty
                date = line.date_order
                price_unit = line.price_unit
                data = {'po_order': po_order_id,
                        'unit_price': price_unit,
                        'vendor': vendor,
                        'quantity': quantity,
                        'po_date': date,
                        }
                vals.append(data)
        return vals

    purchase_lines = fields.One2many('purchase.order.line.history', 'wizard_id', string="Purchases",
                                     default=action_get_history_lines)

    def print_report(self):
        data = {
            'model': 'purchaseline.history.wizard',
            'wizard_data': self.read()[0],

        }
        report_action = self.env.ref('products_price_history.report_price_history').report_action(self, data=data)
        return report_action


class PurchasePriceHistoryReport(models.AbstractModel):
    _name = 'report.products_price_history.report_purchase_price_history'

    @api.model
    def _get_report_values(self, docids, data=None):
        line_ids = data.get('wizard_data').get('purchase_lines')
        docs = self.env['purchase.order.line.history'].browse(line_ids)
        return {
            'doc_ids': self.ids,
            'doc_model': 'purchase.order.line.history',
            'data': data,
            'docs': docs,
        }
