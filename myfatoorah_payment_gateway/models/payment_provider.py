# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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
from odoo import fields, models, api


class PaymentProvider(models.Model):
    """ Inherited class of payment provider to add myfatoorah functions"""
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('myfatoorah', "MyFatoorah")],
        ondelete={'myfatoorah': 'set default'}
    )
    myfatoorah_token = fields.Char(string='Token')

    @api.model
    def _get_payment_method_information(self):
        """ Override method to add MyFatoorah payment method information."""
        res = super()._get_payment_method_information()
        res['mfatoorah'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    def _myfatoorah_get_api_url(self):
        """ Return the API URL according to the provider state.
        Note: self.ensure_one()
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://api.myfatoorah.com/'
        else:
            return 'https://apitest.myfatoorah.com/'
