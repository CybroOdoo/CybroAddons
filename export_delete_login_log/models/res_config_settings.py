# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models, api, _
from ast import literal_eval
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """Inherits ResConfigSettings to add fields to support DeleteLog,
    LoginLog"""
    _inherit = 'res.config.settings'

    delete_log_models_ids = fields.Many2many('ir.model',
                                             string="Delete log models",
                                             domain=[
                                                 ('model', '!=', 'delete.log')
                                             ])
    have_api_key = fields.Boolean(string='Have API Key',
                                  config_parameter='export_delete_login_log'
                                                   '.have_api_key')
    ipapi_key = fields.Char(string='API Key',
                            config_parameter='export_delete_login_log'
                                             '.ipapi_key')

    def set_values(self):
        """Set values to delete_log_models_ids Many2many field"""
        res = super().set_values()
        if self.env.user in self.env.ref(
                'export_delete_login_log.group_export_log_manager').users:
            self.env['ir.config_parameter'].sudo().set_param(
                'export_delete_login_log.delete_log_models_ids',
                self.delete_log_models_ids.ids)
            return res
        else:
            raise UserError(
                _("You don't have the permission to modify this record."))

    @api.model
    def get_values(self):
        """Get values from delete_log_models_ids Many2many field"""
        res = super().get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        tracked_models = with_user.get_param(
            'export_delete_login_log.delete_log_models_ids')
        res.update(delete_log_models_ids=[(6, 0, literal_eval(tracked_models))
                                          ] if tracked_models else False, )
        return res
