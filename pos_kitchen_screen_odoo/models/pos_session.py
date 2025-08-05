# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
############################################################################
from odoo import models


class PosSession(models.Model):
    """Inheriting the pos session"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Pos ui models to load"""
        result = super()._pos_ui_models_to_load()
        result += {
                    'pos.order', 'pos.order.line'
                }
        return result

    def _loader_params_pos_order(self):
        """Load the fields to pos order"""
        return {'search_params': {
            'domain': [],
            'fields': ['name', 'date_order', 'pos_reference',
                       'partner_id', 'lines', 'order_status', 'order_ref',
                       'is_cooking']}}

    def _get_pos_ui_pos_order(self, params):
        """Get pos ui pos order"""
        return self.env['pos.order'].search_read(
            **params['search_params'])

    def _loader_params_pos_order_line(self):
        """Load the fields to pos order line"""
        return {'search_params': {'domain': [],
                                  'fields': ['product_id', 'qty',
                                             'order_status', 'order_ref',
                                             'customer_id',
                                             'price_subtotal', 'total_cost']}}

    def _get_pos_ui_pos_order_line(self, params):
        """Get pos ui pos order line"""
        return self.env['pos.order.line'].search_read(
            **params['search_params'])
