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
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
################################################################################
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_downpayment = fields.Boolean(
        string="Is a down payment",
        help="Down payments are made when creating Bills "
             "from a purchase order."
    )

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare invoice line values
        """
        self.ensure_one()

        # IMPORTANT FIX
        # Use product_qty instead of qty_to_invoice
        # for normal product lines

        quantity = self.product_qty

        # Down payment line should remain negative
        if self.is_downpayment:
            quantity = -1

        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': quantity,
            'price_unit': self.price_unit,
            'tax_ids': [fields.Command.set(self.tax_ids.ids)],
            'analytic_distribution': self.analytic_distribution,
            'purchase_line_id': self.id,
            'is_downpayment': self.is_downpayment,
        }

        if optional_values:
            res.update(optional_values)

        # For section/note lines
        if self.display_type:
            res['account_id'] = False

        return res