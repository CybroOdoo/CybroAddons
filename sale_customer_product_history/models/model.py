# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def get_product_history_data(self):
        values = []
        customer_id = self.order_id.partner_id
        customer_order = self.env['sale.order'].search(
            [('partner_id', '=', customer_id.id), ('state', 'in', ('sale', 'done'))])
        for order in customer_order:
            for line in order.order_line:
                if line.product_id == self.product_id:
                    values.append((0, 0, {'sale_order_id': order.id,
                                          'history_price': line.price_unit,
                                          'history_qty': line.product_uom_qty,
                                          'history_total': order.amount_total
                                          }))
        history_id = self.env['product.sale.order.history'].create({
            'product_id': self.product_id.id,
            'product_sale_history': values
        })

        return {
            'name': 'Customer Product Sales History',
            'view_mode': 'form',
            'res_model': 'product.sale.order.history',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': history_id.id
        }


