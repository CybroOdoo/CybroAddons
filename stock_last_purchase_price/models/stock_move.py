# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, _, api


class StockMove(models.Model):
    """ Class to inherit stock_move to update the product price """
    _inherit = "stock.move"

    @api.depends('value')
    def _compute_remaining_value(self):
        # First run Odoo’s standard logic (fifo + standard/average)
        super()._compute_remaining_value()
        # Then apply custom override for "last"
        for move in self:
            if not move.is_in:
                continue
            if move.product_id.cost_method == 'last':
                ratio = move.remaining_qty / move.quantity if move.quantity else 0
                move.remaining_value = ratio * move.value if ratio else 0
