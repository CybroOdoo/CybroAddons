# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Subina P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class PaymentAcquirer(models.Model):
    """New fields are added in payment_acquirer model and compute payment
    information."""
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        string="Provider",
        selection_add=[('myfatoorah', "MyFatoorah")],
        ondelete={'myfatoorah': 'set default'},
        help="Selection value myfatoorah is added to specify the payment "
             "provider")
    myfatoorah_token = fields.Char(string='Token',
                                   help="Token of Myfatoorah payment gateway")

    def _myfatoorah_get_api_url(self):
        """ Return the API URL according to the provider state.
        Note: self.ensure_one()
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == 'enabled':
            raise ValidationError(
                "API URL cannot be retrieved when state is 'enabled'.")
        return 'https://apitest.myfatoorah.com/'

    def _get_default_payment_method_id(self):
        """ To get default payment method"""
        self.ensure_one()
        if self.provider != 'myfatoorah':
            return super()._get_default_payment_method_id()
        return (self.env.ref
                ('myfatoorah_payment_gateway.payment_method_fatoorah').id)
