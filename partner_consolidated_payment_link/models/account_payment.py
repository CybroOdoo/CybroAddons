# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import Command, models


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
        res = super().action_post()
        for rec in self:
            if rec.payment_transaction_id and rec.payment_transaction_id.reference:
                moves = self.env['account.move'].sudo().search([
                    ('consolidated_payment_link_ref', '=', rec.payment_transaction_id.reference)
                ])
                if moves:
                    rec.payment_transaction_id.invoice_ids = [
                        Command.link(move.id) for move in moves
                    ]
                    moves.matched_payment_ids += rec
        return res
