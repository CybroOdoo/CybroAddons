# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from odoo import models


class PosSession(models.Model):
    """Class to load models in to pos session"""
    _inherit = "pos.session"

    def _pos_ui_models_to_load(self):
        """Load models to pos session"""
        result = super()._pos_ui_models_to_load()
        result += ['account.journal', 'res.partner', 'pos.payment.method']
        return result

    def _loader_params_account_journal(self):
        """Load account journal parameters"""
        return {
            'search_params': {
                'fields': [
                    'name', 'type', 'code', 'default_account_id',
                    'wallet_journal'
                ]
            }
        }

    def _get_pos_ui_account_journal(self, params):
        """Get account journal parameter"""
        return self.env['account.journal'].search_read(
            **params['search_params'])

    def _loader_params_res_partner(self):
        """Load res.partner parameters"""
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['wallet_balance'])
        return result

    def _loader_params_pos_payment_method(self):
        """Load payment method parameters"""
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].extend(['wallet_journal'])
        return result
