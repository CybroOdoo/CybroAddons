# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Viswanth K(odoo@cybrosys.com)
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
#############################################################################
from odoo import  models

class AccountPayment(models.Model):
    """Inherit Account Payment to handle payment transaction invoice matching."""
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
