# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class RegisterPayment(models.TransientModel):
    """Details for a payment for parking"""
    _name = 'register.payment.wizard'
    _description = 'Register Parking Payment'

    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 help='Name of partner to register the payment')
    parking_duration = fields.Float(string='Duration',
                                    help='Duration of the parking vehicle')
    amount = fields.Float(string='Amount',
                          help='Amount of the parking vehicle')
    ref = fields.Char(string='Reference',
                      help='Reference to the parking ticket')
    date = fields.Date(string='Date', default=fields.Date.context_today,
                       help='Date when payment was made')

    def parking_payment(self):
        """Returns the amount of the parking ticket for the customer."""
        active_id = self._context.get('active_id')
        active_record = self.env['parking.entry'].browse(active_id)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'ref': self.ref,
        })
        payment.action_post()
        active_record.paid_bool = True
        active_record.state = 'payment'
