# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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


class VehicleRegisterPayment(models.TransientModel):
    """Details for a payment for vehicle rental"""
    _name = 'vehicle.register.payment.wizard'
    _description = 'Register Payment'

    farmer_id = fields.Many2one('farmer.detail', string='Partner',
                                 help='Name of partner to register the payment')
    rental_duration = fields.Float(string='Duration',
                                   help='Duration of the parking vehicle')
    amount = fields.Float(string='Amount', help='Amount of the parking vehicle')
    ref = fields.Char(string='Reference',
                      help='Reference to the parking ticket')
    date = fields.Date(string='Date', default=fields.Date.context_today,
                       help='Date when payment was made')

    def vehicle_rent_payment(self):
        """Returns the amount of the rental of vehicle for the customer."""
        active_id = self._context.get('active_id')
        active_record = self.env['vehicle.rental'].browse(active_id)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_id': self.farmer_id.id,
            'amount': self.amount,
            'ref': self.ref,
        })
        payment.action_post()
        active_record.vehicle_paid_bool = True
        active_record.state = 'paid'
