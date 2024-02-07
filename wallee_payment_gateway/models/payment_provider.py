# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ansil pv (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wallee', "Wallee")],
        ondelete={'wallee': 'set default'}, help='Wallee code selection')
    wallee_user_id = fields.Integer(string='User ID',
                                    help='User id of wallee portal')
    wallee_user_secret_key = fields.Char(string='User secret key',
                                         help='API secret key for wallee')
    wallee_user_space_id = fields.Integer(string='Wallee user space',
                                          help='Space ID of wallee')

    @api.model
    def _get_payment_method_information(self):
        """Override to add Wallee payment method information to the
        existing methods.
        """
        res = super()._get_payment_method_information()
        res['wallee'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res
