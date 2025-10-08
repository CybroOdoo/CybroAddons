# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class PaymentProvider(models.Model):
    """    Inherit Payment Provider to add new payment into the Payment Provider
     page."""
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('avenue', 'avenue')],
                            ondelete={'avenue': 'set default'},
                            help="The technical code of this payment provider",
                            string="code")
    merchant_key = fields.Char(string='Merchant ID', groups='base.group_user',
                               help="CCAvenue Merchant id of the user")
    access_code = fields.Char(string='Access Code',
                              required_if_provider='avenue',
                              groups='base.group_user',
                              help="CCAvenue Access Code")
    working_key = fields.Char(string='Working Key',
                              required_if_provider='avenue',
                              groups='base.group_user',
                              help="CCAvenue Working key")

    @api.model
    def _get_payment_method_information(self):
        """Override to add CCAvenue payment method information to the
        existing methods.
        """
        res = super()._get_payment_method_information()
        res['avenue'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res
