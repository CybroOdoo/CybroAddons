# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class PosConfig(models.Model):
    """Inherit pos configuration and add new fields."""
    _inherit = 'pos.config'

    refund_security = fields.Integer(string='Refund Security')


class ResConfigSettings(models.TransientModel):
    """Adding a new field to res_config_settings model."""
    _inherit = 'res.config.settings'

    global_refund_security = fields.Integer(
        string='Global Refund Security',
        config_parameter='pos_refund_password.global_refund_security')

    @api.model
    def get_value(self):
        security_password = self.env['ir.config_parameter'].sudo().get_param(
            'pos_refund_password.global_refund_security')
        return security_password
