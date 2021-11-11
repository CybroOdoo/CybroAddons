# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P (odoo@cybrosys.com)
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
from odoo import models, api, fields


class PosOrderReturn(models.Model):
    _inherit = 'pos.order'

    return_ref = fields.Char(string='Return Ref', readonly=True, copy=False)
    return_status = fields.Selection([
        ('nothing_return', 'Nothing Returned'),
        ('partialy_return', 'Partialy Returned'),
        ('fully_return', 'Fully Returned')
    ], string="Return Status", default='nothing_return',
        readonly=True, copy=False, help="Return status of Order")

    @api.model
    def get_lines(self, ref):
        result = []
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        if order_id:
            lines = self.env['pos.order.line'].search([('order_id', '=', order_id.id)])
            for line in lines:
                if line.qty - line.returned_qty > 0:
                    new_vals = {
                        'product_id': line.product_id.id,
                        'product': line.product_id.name,
                        'qty': line.qty - line.returned_qty,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'line_id': line.id,
                    }
                    result.append(new_vals)

        return [result]

    def _order_fields(self, ui_order):
        order = super(PosOrderReturn, self)._order_fields(ui_order)
        if 'return_ref' in ui_order.keys() and ui_order['return_ref']:
            order['return_ref'] = ui_order['return_ref']
            parent_order = self.search([('pos_reference', '=', ui_order['return_ref'])], limit=1)

            updated_lines = ui_order['lines']
            ret = 0
            qty = 0
            for uptd in updated_lines:
                line = self.env['pos.order.line'].search([('order_id', '=', parent_order.id),
                                                           ('id', '=', uptd[2]['line_id'])], limit=1)
                if line:
                    line.returned_qty += -(uptd[2]['qty'])
            for line in parent_order.lines:
                qty += line.qty
                ret += line.returned_qty
            if qty-ret == 0:
                if parent_order:
                    parent_order.return_status = 'fully_return'
                    print(parent_order.return_status)
            elif ret:
                if qty > ret:
                    if parent_order:
                        parent_order.return_status = 'partialy_return'

        return order


class PosOrderLineReturn(models.Model):
    _inherit = 'pos.order.line'

    returned_qty = fields.Integer(string='Returned Qty', digits=0, readonly=True)
