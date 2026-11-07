# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models
from odoo.tools import format_amount


class SaleOrder(models.Model):
    """Inherited the model for adding the dashboard values"""
    _inherit = 'sale.order'

    @api.model
    def get_dashboard_values(self):
        """This method returns values to the dashboard in sale order views."""
        result = {
            'total_orders': 0,
            'draft_orders': 0,
            'sale_orders': 0,
            'my_orders': 0,
            'my_draft_orders': 0,
            'my_sale_orders': 0,
            'total_sale_amount': 0,
            'total_draft_amount': 0,
        }
        sale_order = self.env['sale.order']
        user = self.env.user
        result['total_orders'] = sale_order.search_count([])
        result['draft_orders'] = sale_order.search_count(
            [('state', 'in', ['draft', 'sent'])])
        result['sale_orders'] = sale_order.search_count(
            [('state', 'in', ['sale'])])
        result['my_orders'] = sale_order.search_count(
            [('user_id', '=', user.id)])
        result['my_draft_orders'] = sale_order.search_count(
            [('user_id', '=', user.id), ('state', 'in', ['draft', 'sent'])])
        result['my_sale_orders'] = sale_order.search_count(
            [('user_id', '=', user.id), ('state', 'in', ['sale'])])
        currency = self.env.company.currency_id
        for key, states in (('total_sale_amount', ['sale']),
                            ('total_draft_amount', ['draft', 'sent'])):
            total = sale_order._read_group(
                [('state', 'in', states)],
                aggregates=['amount_total:sum'])[0][0]
            result[key] = format_amount(self.env, total or 0, currency)
        return result
