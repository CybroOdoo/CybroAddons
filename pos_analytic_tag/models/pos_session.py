# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
from odoo import fields, models


class PosSession(models.Model):
    """To add analytic tags in pos session"""
    _inherit = 'pos.session'

    pos_analytic_account_id = fields.Many2one('account.analytic.account',
                                              string='Pos Analytic Tag',
                                              help="Pos Analytic account in"
                                                   " pos session",
                                              readonly=True)

    def _pos_ui_models_to_load(self):
        """To load new model to POS"""
        result = super()._pos_ui_models_to_load()
        result.append('res.config.settings')
        return result

    def _loader_params_res_config_settings(self):
        """To load fields in a config"""
        return {
            'search_params': {
                'fields': ['pos_analytic_account_id'],
            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """To get values in res config settings to pos ui"""
        res_obj = self.env['res.config.settings'].search_read(
            **params['search_params'])
        if res_obj:
            val = res_obj[-1] if res_obj[-1] else res_obj
            self.pos_analytic_account_id = False if not val[
                'pos_analytic_account_id'] else \
                val['pos_analytic_account_id'][0]
            return val
        else:
            return False

    def _prepare_analytic_lines(self):
        """Call the parent class method and convert any string value
        in account_id to integer"""
        res = super()._prepare_analytic_lines()
        self.ensure_one()
        analytic_line_vals = []
        if self.analytic_distribution:
            distribution_on_each_plan = {}
        for account_id, distribution in self.analytic_distribution.items():
            line_values = self._prepare_analytic_distribution_line(
                float(distribution), int(account_id),
                distribution_on_each_plan)
            if not self.currency_id.is_zero(line_values.get('amount')):
                analytic_line_vals.append(line_values)
        return res

    def _create_account_move(self, balancing_account=False,
                             amount_to_balance=0,
                             bank_payment_method_diffs=None):
        """Call the parent class method using super() and creates
         analytic distribution model"""
        res = super()._create_account_move(balancing_account,
                                           amount_to_balance,
                                           bank_payment_method_diffs)
        search_params = {
            'fields': ['pos_analytic_account_id'],
            'limit': 1,
        }
        analytic_account = self._get_pos_ui_res_config_settings((
            {'search_params': search_params}))
        if analytic_account == 'False':
            return True
        else:
            self.env['account.analytic.distribution.model'].create([{
                'analytic_distribution': {self.pos_analytic_account_id.id: 100}
            }])
        return res
