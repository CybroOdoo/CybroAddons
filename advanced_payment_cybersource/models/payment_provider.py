# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PaymentProvider(models.Model):
    """Adding payment provider"""
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cybersource', 'Cybersource')],
                                ondelete={'cybersource': 'set default'},
                                string='Provider',
                                help='Identifying the payment method in payment'
                                     ' methods')
    cyber_merchant = fields.Char(string='Merchant ID',
                                 help='Cybersource merchant id')
    cyber_secret_key = fields.Char(string='Secret Key',
                                   help='Cybersource secret key for the payment')
    cyber_key = fields.Char(string='Secret Key',
                            help='Cyber key for the payment')
