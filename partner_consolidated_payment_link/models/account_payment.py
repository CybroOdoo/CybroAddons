# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo import models

class AccountPayment(models.Model):
    """
    Inherit account.payment to link payment transactions to invoices for
    consolidated payment references.
    """
    _inherit = 'account.payment'

    def action_post(self):
        """
        Override to link invoices with their payment transaction for
        consolidated payments.
        """
        res = super(AccountPayment, self).action_post()
        for rec in self:
            payment_reference = rec.payment_transaction_id and rec.payment_transaction_id.reference or 'consolidated payment link'
            moves = self.env['account.move'].sudo().search([('consolidated_payment_link_ref', '=', payment_reference)])
            if moves and rec.payment_transaction_id:
                rec.payment_transaction_id.invoice_ids = [(4, move.id) for move in moves]
                moves.matched_payment_ids += rec
        return res
