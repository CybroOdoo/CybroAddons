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
from odoo import api, fields, models


class StockMove(models.Model):
    """Inherited model stock move.

    Contains a field for line numbers and a method for computing them.
    """

    _inherit = 'stock.move'

    sequence_number = fields.Integer(
        string='#',
        compute='_compute_sequence_number',
        help='Line Numbers',
    )

    @api.depends('picking_id', 'picking_id.move_ids')
    def _compute_sequence_number(self):
        """Compute line numbers for stock moves."""
        for move in self:
            move.sequence_number = 0

        for picking in self.picking_id:
            for sequence_number, move in enumerate(picking.move_ids, 1):
                if move in self:
                    move.sequence_number = sequence_number


class StockPicking(models.Model):
    """Inherited model stock picking.

    Contains a method for calculating line numbers on change.
    """

    _inherit = 'stock.picking'

    @api.onchange('move_ids')
    def _onchange_move_ids_without_package(self):
        """Calculate line number of operations."""
        for sequence_number, rec in enumerate(self.move_ids, 1):
            rec.sequence_number = sequence_number
