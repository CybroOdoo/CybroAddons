# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Noushid Khan.P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """Inherits the model res.config.settings to add extra fields"""
    _inherit = 'res.config.settings'

    send_grid_api_check = fields.Boolean(string="SendGrid API",
                                         config_parameter="sendgrid_email.send_grid_api_check")
    send_grid_api_value = fields.Char(string='API key',
                                      config_parameter="sendgrid_email.send_grid_api_value")
