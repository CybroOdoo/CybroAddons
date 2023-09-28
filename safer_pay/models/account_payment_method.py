# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class AccountPaymentMethod(models.Model):
    """ For get details of payment method """
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        """ Record for safer pay in payment acquirer is
        created while installing the module. this function is
        used for  to get default payment method details """
        res = super()._get_payment_method_information()
        res['saferpay'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res
