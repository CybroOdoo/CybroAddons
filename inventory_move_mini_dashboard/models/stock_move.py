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
#############################################################################
from datetime import timedelta
from odoo import api, fields, models


class StockMove(models.Model):
    """Class for passing values to mini dashboard.
       retrieve_inventory_dashboard function for calculating values."""
    _inherit = 'stock.move'

    @api.model
    def retrieve_inventory_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the stock move return result which includes the values of
            numbers in all stages"""
        result = {
            'draft': 0,
            'waiting': 0,
            'assigned': 0,
            'done': 0,
            'count': 0,
            'average_products': 0,
        }
        stock_move = self.env['stock.move']
        last_week = fields.Datetime.now() - timedelta(days=7)
        moves_data = stock_move._read_group(
            [('date', '>=', last_week)],
            aggregates=['product_qty:sum', '__count'],
        )
        total_qty, count = moves_data[0] if moves_data else (0, 0)
        total_qty = total_qty or 0
        result['count'] = count
        result['average_products'] = int(total_qty / count) if count else 0

        state_counts = dict(stock_move._read_group([], ['state'], ['__count']))
        result['draft'] = state_counts.get('draft', 0)
        result['waiting'] = state_counts.get('waiting', 0) + state_counts.get('confirmed', 0)
        result['assigned'] = state_counts.get('assigned', 0)
        result['done'] = state_counts.get('done', 0)
        return result
