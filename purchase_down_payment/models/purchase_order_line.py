# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
#    (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#
################################################################################
"""Inherit purchase order line to support down payment tracking."""
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    """Extend purchase.order.line with down payment flag and invoice helper."""

    # pylint: disable=too-few-public-methods
    _inherit = 'purchase.order.line'

    is_downpayment = fields.Boolean(
        string="Is a down payment",
        help="Down payments are made when creating Bills "
             "from a purchase order.",
    )

    def _prepare_invoice_line(self, **optional_values):
        """Prepare invoice line values for purchase order line."""
        self.ensure_one()

        quantity = self.product_qty
        if self.is_downpayment:
            quantity = -1

        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.uom_id.id,
            'quantity': quantity,
            'price_unit': self.price_unit,
            'tax_ids': [fields.Command.set(self.tax_ids.ids)],
            'analytic_distribution': self.analytic_distribution,
            'purchase_line_id': self.id,
            'is_downpayment': self.is_downpayment,
        }

        if optional_values:
            res.update(optional_values)

        if self.display_type:
            res['account_id'] = False

        return res

    def _get_invoice_line_sequence(self, new=0, old=0):
        """Provide a hook to preserve or compute line sequence when grouping."""
        return new or old
