# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil M (odoo@cybrosys.com)
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
from odoo import fields, models


class MrpProduction(models.Model):
    """This class extends the 'mrp.production' model to add a new method
        and field to add the Quantity to Produce."""
    _inherit = 'mrp.production'

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line',
                                   help='ID of the Sale Order Line')
    qty_to_produce = fields.Float(string='Quantity to Produce',
                                  help='The number of products to be produced')

    def action_update_quantity(self):
        """ Method for changing the quantities of components according to
         product quantity """
        self.move_raw_ids = [(5,)]
        self.move_finished_ids = [(5,)]
        self.product_qty = self.qty_to_produce
        moves_raw_values = self._get_moves_raw_values()
        list_move_raw = []
        for move_raw_values in moves_raw_values:
            list_move_raw += [(0, 0, move_raw_values)]
        self.move_raw_ids = list_move_raw
        moves_finished_values = self._get_moves_finished_values()
        list_move_finished = []
        for move_finished_values in moves_finished_values:
            list_move_finished += [(0, 0, move_finished_values)]
        self.move_finished_ids = list_move_finished
