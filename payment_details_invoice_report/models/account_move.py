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
from odoo import fields, models


class AccountMove(models.Model):
    """Inherit the account.move for adding the field
        for enabling payment details"""
    _inherit = 'account.move'

    is_payment_details = fields.Boolean(string="Payment Details in Report",
                                        help="Enables the payment details in "
                                             "invoice report")

    def get_payment_details(self):
        """
        Method to get the payment details of the invoice
        :return: list of dictionary containing payment details
        """
        payment_vals = []
        if self.payment_state != 'not_paid':
            reconciled_partials = self._get_reconciled_invoices_partials()
            for _partial, amount, counterpart_line in (
                    reconciled_partials[0] if reconciled_partials else []):
                payment_vals.append({
                    'ref': counterpart_line.move_id.name,
                    'date': counterpart_line.date,
                    'journal_name': counterpart_line.journal_id.name,
                    'amount_company_currency': amount,
                })
        return payment_vals
