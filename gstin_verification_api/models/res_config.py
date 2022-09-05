# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class ResConfig(models.TransientModel):
    _description = "Adding the Autotax API credentials in the General settings"
    _inherit = 'res.config.settings'

    autotax_username = fields.Char(string="Username")
    autotax_password = fields.Char(string="Password")
    autotax_client_id = fields.Char(string="Client ID")
    autotax_client_secret = fields.Char(string="Client Secret")

    @api.model
    def get_values(self):
        """
        Get values for fields in the settings
        and assign the value to the fields
        """
        res = super(ResConfig, self).get_values()
        res.update(
            autotax_username=self.env['ir.config_parameter'].sudo().get_param(
                'autotax_username'),
            autotax_password=self.env['ir.config_parameter'].sudo().get_param(
                'autotax_password'),
            autotax_client_id=self.env['ir.config_parameter'].sudo().get_param(
                'autotax_client_id'),
            autotax_client_secret=self.env[
                'ir.config_parameter'].sudo().get_param('autotax_client_secret')
        )
        return res

    def set_values(self):
        """
        save values in  the settings fields
        """
        super(ResConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('autotax_username',
                                                         self.autotax_username)
        self.env['ir.config_parameter'].sudo().set_param('autotax_password',
                                                         self.autotax_password)
        self.env['ir.config_parameter'].sudo().set_param('autotax_client_id',
                                                         self.autotax_client_id)
        self.env['ir.config_parameter'].sudo().set_param(
            'autotax_client_secret', self.autotax_client_secret)
