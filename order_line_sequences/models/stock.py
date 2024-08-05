# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    """ Class for inherited model stock move. Contains a field for line
            numbers and a function for computing line numbers."""

    _inherit = 'stock.move'
    sequence_number = fields.Integer(string='#',
                                     compute='_compute_sequence_number',
                                     help='Line Numbers')

    @api.depends('picking_id')
    def _compute_sequence_number(self):
        """Function to compute line numbers"""
        self.sequence_number = 1
        for picking in self.mapped('picking_id'):
            sequence_number = 1
            if picking.move_ids_without_package:
                for lines in picking.move_ids_without_package:
                    lines.sequence_number = sequence_number
                    sequence_number += 1
            else:
                picking.sequence()


class StockPicking(models.Model):
    """ Class for inherited model stock picking. Contains
        a function for computing line numbers."""
    _inherit = 'stock.picking'

    @api.onchange('move_ids_without_package')
    def _onchange_move_ids_without_package(self):
        """For calculating line number of operations"""
        sequence_number = 1
        for rec in self.move_ids_without_package:
            rec.sequence_number = sequence_number
            sequence_number += 1
