# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PickingMiniDashboard(models.Model):
    """Class for mini passing values to mini dashboard
        stock_picking_dashboard function for calculating values
    """
    _inherit = 'stock.picking'

    @api.model
    def stock_picking_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the stock picking return result which includes the values of
            numbers in all stages """
        result = {
            'draft': 0,
            'waiting': 0,
            'assigned': 0,
            'done': 0,
            'receipts': 0,
            'outgoing': 0,
            'internal': 0,
            'cancel': 0
        }
        current_date = fields.datetime.now().date()
        start_date = current_date.replace(day=1)
        domain = [('state', '=', 'done'),
                  ('picking_type_id.code', '=', 'incoming'),
                  ('date_done', '>=', start_date)
                  ]
        stock_picking = self.env['stock.picking']
        receipts = stock_picking.search_count(domain)
        outgoing = stock_picking.search_count(
            [('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing'),
             ('date_done', '>=', start_date)])
        internal = stock_picking.search_count(
            [('state', '=', 'done'), ('picking_type_id.code', '=', 'internal'),
             ('date_done', '>=', start_date)])
        cancel = stock_picking.search_count(
            [('state', '=', 'cancel'), ('date', '>=', start_date)])
        result['cancel'] = cancel
        result['internal'] = internal
        result['outgoing'] = outgoing
        result['receipts'] = receipts
        result['draft'] = stock_picking.search_count([('state', '=', 'draft')])
        result['waiting'] = stock_picking.search_count(
            [('state', 'in', ('waiting', 'confirmed'))])
        result['done'] = stock_picking.search_count([('state', '=', 'done')])
        result['assigned'] = stock_picking.search_count(
            [('state', '=', 'assigned')])
        return result
