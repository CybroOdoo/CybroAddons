# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
from datetime import date


class CreditPayment(models.TransientModel):
    """
        Transient Model for managing credit payments in the payment journal.
    """
    _name = "credit.payment"
    _description = "Credit Payment"

    payment_journal = fields.Many2one('account.journal',
                                      string='Payment Journal', readonly=1,
                                      help='Represents the payment journal '
                                           'associated with the record.')
    credit_amount = fields.Float('Credit Amount',
                                 help='Credit amount to update the journal')
    partner_id = fields.Many2one('res.partner', )
    credit_detail_id = fields.Many2one('credit.details')

    def action_submit(self):
        """
            Create and submit an inbound payment for the current record.
            Returns: account.payment: The newly created payment record.
        """
        payment_id = self.env['account.payment'].sudo().create({
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_method_line_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.credit_amount,
            'date': date.today(),
            'journal_id': self.payment_journal.id,
        })
        payment_id.action_post()
