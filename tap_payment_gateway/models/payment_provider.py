# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PaymentProvider(models.Model):
    """ Payment Provider Model for Tap """
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('tap', "Tap")],
                            ondelete={'tap': 'set default'},
                            string="Provider Code",
                            help="The code that represents the Tap payment"
                                 " provider.")
    tap_secret_key = fields.Char(string="Tap Secret Key", required=True,
                                 default="sk_test_XKokBfNWv6FIYuTMg5sLPjhJ",
                                 help="The secret key provided by Tap for API"
                                      " authentication.")
    tap_publishable_key = fields.Char(string="Tap Publishable Key",
                                      required=True,
                                      default="pk_test_EtHFV4BuPQokJT6jiROls87Y",
                                      help="The publishable key provided by"
                                           " Tap for API authentication.")

    @api.model
    def _get_payment_method_information(self):
        """ Get Payment Method Information for Tap """
        res = super()._get_payment_method_information()
        res['tap'] = {'mode': 'unique',
                      'domain': [('type', '=', 'bank')]}
        return res
