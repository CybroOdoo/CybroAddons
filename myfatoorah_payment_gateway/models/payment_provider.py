# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class PaymentProvider(models.Model):
    """ Inherited class of payment provider to add myfatoorah functions"""
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('myfatoorah', "MyFatoorah")],
        ondelete={'myfatoorah': 'set default'},
        help="Select 'MyFatoorah' as the payment provider if you want to process payments through MyFatoorah."
    )
    myfatoorah_token = fields.Char(
        string='Token',
        help="Enter the authentication token required for integrating with MyFatoorah's payment gateway."
    )



    def _myfatoorah_get_api_url(self):
        """Return the API URL according to the provider state."""
        self.ensure_one()
        return 'https://api.myfatoorah.com/' if self.state == 'enabled' else 'https://apitest.myfatoorah.com/'
