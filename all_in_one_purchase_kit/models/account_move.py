# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    """Inherit account.move to add fields and methods"""
    _inherit = 'account.move'

    amount_total_company_signed = fields.Float(
        string='Company Currency Total',
        compute='_compute_amount_total_company_signed',
        help="Total amount in company currency")
    number_to_words = fields.Char(
        string="Amount in Words (Total) : ",
        compute='_compute_number_to_words', help="Amount in words")

    def _compute_amount_total_company_signed(self):
        """Compute the total amount in company currency for each record."""
        for amount in self:
            amount.amount_total_company_signed = self.env[
                'res.currency']._compute(
                amount.currency_id, amount.company_id.currency_id,
                amount.amount_total)

    def _compute_number_to_words(self):
        """Compute the amount to words in Invoice for each record."""
        for rec in self:
            rec.number_to_words = rec.currency_id.amount_to_text(
                rec.amount_total)

    def action_post(self):
        """Override the default post action to merge order lines with the same
         product and price."""
        for line in self.invoice_line_ids:
            if line.id in self.invoice_line_ids.ids:
                line_ids = self.invoice_line_ids.filtered(
                    lambda m: m.product_id.id == line.product_id.id and m.
                    price_unit == line.price_unit)
                quantity = line_ids.mapped('quantity')
                line_ids.write({'quantity': sum(quantity),
                                'price_unit': line.price_unit})
                line_ids[1:].unlink()
        res = super(AccountMove, self).action_post()
        return res
