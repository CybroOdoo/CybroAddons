# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
import re

from odoo import Command, models


class AccountPayment(models.Model):
    """Inherit Account Payment to handle payment transaction invoice matching."""
    _inherit = 'account.payment'

    def action_post(self):
        """
        Override to link invoices with their payment transaction for
        consolidated payments.
        """
        res = super().action_post()
        for payment in self.filtered('payment_transaction_id'):
            transaction = payment.payment_transaction_id
            # A reused consolidated reference gets a numeric suffix (e.g. "-1")
            # on the transaction, so match the invoices on the base reference too.
            references = {transaction.reference, re.sub(r'-\d+$', '', transaction.reference)}
            moves = self.env['account.move'].sudo().search([
                ('consolidated_payment_link_ref', 'in', list(references)),
            ])
            if moves:
                transaction.invoice_ids = [Command.link(move.id) for move in moves]
                moves.matched_payment_ids = [Command.link(payment.id)]
        return res
