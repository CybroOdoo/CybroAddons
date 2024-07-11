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
from datetime import datetime
from odoo import fields, models


class CreditAmount(models.Model):
    """
        Model for managing credit amounts associated with customers.
    """
    _name = "credit.amount"
    _description = "Credit Amount"
    _rec_name = 'customer_id'

    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=1,
        help='Reference to the associated customer/partner.')
    amount = fields.Float(string="Amount",
                          help='The monetary amount associated with this '
                               'record.')
    approve_date = fields.Datetime(
        'Approve Date', default=datetime.today(),
        help='Date and time when the record was approved.')
    state = fields.Selection(
        [('to_approve', 'Waiting for approve'), ('approved', 'Approved'), ],
        string='Stage', readonly=True, copy=False,
        index=True, tracking=3, default='to_approve',
        help='Current stage of the record, indicating whether it is waiting '
             'for approval or already approved.')
    hide_approve = fields.Boolean(
        'Approve', default=False, invisible="1",
        help='Boolean field indicating whether the approval action should be '
             'hidden or visible.')

    def action_approve(self):
        """
            Approves the credit amount and updates associated credit details.

            :return: None
            """
        self.state = 'approved'
        self.hide_approve = True
        credit_details = self.env['credit.details'].search(
            [('customer_id', '=', self.customer_id.id)])
        if credit_details:
            previous_amt = credit_details.credit_amount
            credit_details.write({
                'updated_amount':self.amount,
                '_is_amount_updated': False,
                'credit_details_ids': [(0, 0, {
                    'amount': self.amount,
                    'customer_id': credit_details.customer_id.id,
                    'previous_credit_amount': previous_amt,
                    'approve_date': self.approve_date,
                    'updated_amount': self.amount + previous_amt,
                    'credit_id': credit_details.id,

                })]
            })
        else:
            self.env['credit.details'].create({
                'customer_id': self.customer_id.id,
                'updated_amount': self.amount,
                'credit_details_ids': [(0, 0, {
                    'customer_id': self.customer_id.id,
                    'amount': self.amount,
                    'previous_credit_amount': 0.0,
                    'approve_date': self.approve_date,
                    'updated_amount': self.amount, })]
            })
