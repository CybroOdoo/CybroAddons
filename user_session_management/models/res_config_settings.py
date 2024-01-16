# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith PG (odoo@cybrosys.com)
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
#############################################################################
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration Settings"""
    _inherit = 'res.config.settings'

    model_ids = fields.Many2many('ir.model', string='Models',
                                 domain=[('model', 'not in',
                                          ['user.session.login',
                                           'user.session.activity'])],
                                 help='Add the models to track.')
    clear_log = fields.Boolean(string='Clear Logs Periodically',
                               help='Select the checkbox to clear the log '
                                    'records automatically')
    records_retain_period = fields.Integer(string='Records Retain Period',
                                           help='Number of days after a '
                                                'session ends before its logs '
                                                'will be automatically removed '
                                                'from the system.')

    def set_values(self):
        """Update the values of configuration parameters."""
        res = super().set_values()
        self.env['ir.config_parameter'].set_param(
            'user_session_management.model_ids', self.model_ids.ids)
        self.env['ir.config_parameter'].set_param(
            'user_session_management.clear_log',
            self.clear_log)
        self.env['ir.config_parameter'].set_param(
            'user_session_management.records_retain_period',
            self.records_retain_period)
        return res

    @api.model
    def get_values(self):
        """Retrieve the current values of configuration parameters."""
        res = super().get_values()
        config_param = self.env['ir.config_parameter'].sudo()
        tracked_models = config_param.get_param(
            'user_session_management.model_ids')
        clear_log = config_param.get_param(
            'user_session_management.clear_log')
        period = config_param.get_param(
            'user_session_management.records_retain_period')
        res.update(
            model_ids=[(6, 0, literal_eval(
                tracked_models))] if tracked_models else False,
            clear_log=clear_log, records_retain_period=period)
        return res
