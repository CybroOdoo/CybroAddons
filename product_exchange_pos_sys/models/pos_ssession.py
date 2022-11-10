# -*- coding: utf-8 -*-
################################################################################
#    POS Product Exchange
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result += {
            'pos.order', 'pos.order.line'
        }
        return result

    def _loader_params_pos_order(self):
        return {'search_params': {
            'domain': [],
            'fields': ['name', 'date_order', 'pos_reference',
                       'partner_id', 'lines', 'exchange']}}

    def _get_pos_ui_pos_order(self, params):
        return self.env['pos.order'].search_read(
            **params['search_params'])

    def _loader_params_pos_order_line(self):
        return {'search_params': {'domain': [],
                                  'fields': ['product_id', 'qty',
                                             'price_subtotal', 'total_cost']}}

    def _get_pos_ui_pos_order_line(self, params):
        return self.env['pos.order.line'].search_read(
            **params['search_params'])


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def get_product_details(self, ids):
        """to get the product details"""
        lines = self.env['pos.order.line'].browse(ids)
        res = []
        for rec in lines:
            res.append({
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'qty': rec.qty
            })
        return res


class PosOrder(models.Model):
    _inherit = 'pos.order'

    exchange = fields.Boolean()

    def pos_exchange_order(self):
        """mark order a exchanged"""
        self.exchange = True
        return
