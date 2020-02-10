# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
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


class PosRepeatOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def get_lines(self, ref):
        """To get the values of the corresponding order"""
        result = []
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        if order_id:
            lines = self.env['pos.order.line'].search([('order_id', '=', order_id.id)])
            for line in lines:
                new_vals = {
                    'product_id': line.product_id.id,
                    'product': line.product_id.name,
                    'qty': 1,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'line_id': line.id,
                }
                result.append(new_vals)

        return [result]
