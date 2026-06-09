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


class PurchaseOrder(models.Model):
    """
        Inherits Purchase Order to support dimension-based pricing in tax totals.

        Key Features:
        --------------
        - Overrides `_compute_tax_totals` to include dimension-based products.
        - Ensures subtotal, untaxed amount, tax amount, and total amount are calculated
          correctly when products are priced based on dimensions.
        - Integrates with Odoo’s tax computation engine for accuracy.
    """
    _inherit = "purchase.order"

    @api.depends(
        'order_line.taxes_id',
        'order_line.price_unit',
        'order_line.dimension_qty',
        'order_line.discount',
        'order_line.product_id',
        'order_line.product_id.price_calculation_based_on',
        'amount_total',
        'amount_untaxed',
        'currency_id',
    )
    def _compute_tax_totals(self):
        """
        Compute tax totals for purchase orders, ensuring dimension-based products are included correctly.
        """
        for order in self:
            order = order.with_company(order.company_id)
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            # Initialize amounts
            custom_amount_untaxed = 0.0
            custom_tax_amount = 0.0

            tax_base_lines = []

            for line in order_lines:
                if line.product_id.price_calculation_based_on == 'based_on_dimension':
                    base_price = line.dimension_qty * line.price_unit
                else:
                    base_price = line.price_unit
                discounted_price = base_price * (1 - line.discount / 100.0)

                custom_amount_untaxed += line.price_subtotal
                tax_base_line_dict = line._convert_to_tax_base_line_dict()
                tax_base_line_dict.update({
                    'price_unit': discounted_price,
                    'quantity': line.product_qty,
                })
                tax_base_lines.append(tax_base_line_dict)
            tax_results = self.env['account.tax']._compute_taxes(tax_base_lines)
            for tax_total in tax_results['totals'].values():
                custom_tax_amount += tax_total['amount_tax']
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                tax_base_lines,
                order.currency_id or order.company_id.currency_id,
            )
            if order.tax_totals:
                order.tax_totals['amount_untaxed'] = custom_amount_untaxed
                order.tax_totals['amount_tax'] = custom_tax_amount
                order.tax_totals['amount_total'] = custom_amount_untaxed + custom_tax_amount

                if 'formatted_amount_untaxed' in order.tax_totals:
                    order.tax_totals['formatted_amount_untaxed'] = order.currency_id.format(custom_amount_untaxed)
                if 'formatted_amount_tax' in order.tax_totals:
                    order.tax_totals['formatted_amount_tax'] = order.currency_id.format(custom_tax_amount)
                if 'formatted_amount_total' in order.tax_totals:
                    order.tax_totals['formatted_amount_total'] = order.currency_id.format(
                        custom_amount_untaxed + custom_tax_amount)
