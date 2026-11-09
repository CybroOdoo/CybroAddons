#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    """Add a global discount on customer invoices."""
    _inherit = 'account.move'

    discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Amount')],
        default='percent',
        help="Apply the discount as a percentage or as a fixed amount.")
    discount_rate = fields.Float(
        digits=(16, 2),
        help="Discount percentage or amount applied on the invoice total.")
    amount_discount = fields.Monetary(
        string='Discount', store=True, readonly=True,
        compute='_compute_amount_discount',
        help="Total discount amount of the invoice lines.")

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.price_unit',
                 'invoice_line_ids.discount')
    def _compute_amount_discount(self):
        """Compute the total discount given on the invoice lines."""
        for move in self:
            move.amount_discount = sum(
                line.quantity * line.price_unit * line.discount / 100
                for line in move.invoice_line_ids
                if line.display_type == 'product')

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def _onchange_discount_rate(self):
        """Apply the global discount on all the invoice lines."""
        for move in self:
            lines = move.invoice_line_ids.filtered(
                lambda line: line.display_type == 'product')
            if move.discount_type == 'percent':
                discount = move.discount_rate
            else:
                total = sum(line.quantity * line.price_unit for line in lines)
                discount = move.discount_rate / total * 100 if total else 0.0
            lines.discount = discount

    def button_dummy(self):
        """Apply the global discount on the invoice lines."""
        self._onchange_discount_rate()
        return True
