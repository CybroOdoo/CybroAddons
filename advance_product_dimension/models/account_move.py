# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models


class AccountMove(models.Model):
    """Inherits the `account.move` model to extend tax and amount computation logic
    for invoices, especially for products whose prices are calculated based on
    dimensions (e.g., area, length, width, etc.)."""
    _inherit = 'account.move'

    @api.depends(
        'invoice_line_ids.tax_ids',
        'invoice_line_ids.price_unit',
        'invoice_line_ids.dimension_qty',
        'invoice_line_ids.discount',
        'invoice_line_ids.product_id',
        'invoice_line_ids.product_id.price_calculation_based_on',
        'amount_total',
        'amount_untaxed',
        'currency_id',
    )
    def _compute_tax_totals(self):
        """
        Compute tax totals for invoices, ensuring dimension-based products are included correctly.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                move = move.with_company(move.company_id)
                invoice_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')

                # Initialize amounts
                custom_amount_untaxed = 0.0
                custom_tax_amount = 0.0

                tax_base_lines = []

                for line in invoice_lines:
                    if line.product_id.price_calculation_based_on == 'based_on_dimension':
                        base_price = line.dimension_qty * line.price_unit
                    else:
                        base_price = line.price_unit
                    discount_price = base_price * (1 - (line.discount / 100.0))
                    line_subtotal = discount_price * line.quantity

                    custom_amount_untaxed += line_subtotal
                    tax_base_line_dict = line._convert_to_tax_base_line_dict()
                    tax_base_line_dict.update({
                        'price_unit': discount_price,
                        'quantity': line.quantity,
                    })
                    tax_base_lines.append(tax_base_line_dict)

                if tax_base_lines:
                    tax_results = self.env['account.tax']._compute_taxes(tax_base_lines)
                    for tax_total in tax_results['totals'].values():
                        custom_tax_amount += tax_total['amount_tax']

                    move.tax_totals = self.env['account.tax']._prepare_tax_totals(
                        tax_base_lines,
                        move.currency_id or move.company_id.currency_id,
                    )

                    if move.tax_totals:
                        move.tax_totals['amount_untaxed'] = custom_amount_untaxed
                        move.tax_totals['amount_tax'] = custom_tax_amount
                        move.tax_totals['amount_total'] = custom_amount_untaxed + custom_tax_amount

                        if 'formatted_amount_untaxed' in move.tax_totals:
                            move.tax_totals['formatted_amount_untaxed'] = move.currency_id.format(custom_amount_untaxed)
                        if 'formatted_amount_tax' in move.tax_totals:
                            move.tax_totals['formatted_amount_tax'] = move.currency_id.format(custom_tax_amount)
                        if 'formatted_amount_total' in move.tax_totals:
                            move.tax_totals['formatted_amount_total'] = move.currency_id.format(
                                custom_amount_untaxed + custom_tax_amount)
                else:
                    super(AccountMove, self)._compute_tax_totals()
            else:
                super(AccountMove, self)._compute_tax_totals()

    @api.depends('line_ids.price_subtotal', 'line_ids.price_total')
    def _compute_amounts(self):
        """Compute the total amounts of the invoice."""
        for move in self:
            if move.is_invoice(include_receipts=True):
                move = move.with_company(move.company_id)
                invoice_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                move.amount_untaxed = sum(
                    (line.dimension_qty * line.price_unit if line.product_id.price_calculation_based_on == 'based_on_dimension' else line.price_unit)
                    * (1 - (line.discount / 100.0))
                    * line.quantity
                    for line in invoice_lines
                )
                move.amount_tax = sum(line.price_total - line.price_subtotal for line in invoice_lines)
                move.amount_total = move.amount_untaxed + move.amount_tax
            else:
                super(AccountMove, self)._compute_amounts()
