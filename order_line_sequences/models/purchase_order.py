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


class PurchaseOrderLine(models.Model):
    """Inherited model purchase order line.

    Contains a field for line numbers and a method for computing them.
    """

    _inherit = 'purchase.order.line'

    sequence_number = fields.Integer(
        string='#',
        compute='_compute_sequence_number',
        help='Line Numbers',
    )

    @api.depends('sequence', 'order_id')
    def _compute_sequence_number(self):
        """Compute line numbers for purchase order lines."""
        for line in self:
            line.sequence_number = 0
        for order in self.order_id:
            sequence_number = 1
            for line in order.order_line:
                line.sequence_number = sequence_number
                if not line.display_type:
                    sequence_number += 1
