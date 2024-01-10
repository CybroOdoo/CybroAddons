"""Cyber source payment gateway"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<odoo@cybrosys.com>)
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
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('cybersource', 'Cybersource')],
                            ondelete={'cybersource': 'set default'},
                            string='Code',
                            help='Identifying the payment method')
    cyber_merchant = fields.Char(string='Merchant ID',
                                 help='Cybersource merchant id')
    cyber_secret_key = fields.Char(string='Secret Key',
                                   help='Cybersource secret key')
    cyber_key = fields.Char(string='Secret Key', help='Cyber key')
