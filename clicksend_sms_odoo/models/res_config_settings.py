# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raveena V (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This class inherits res config settings model to add the settings
    for clicksend sms gateway"""
    _inherit = 'res.config.settings'

    username = fields.Char(string="Username",
                           help="Your username of ClickSend account")
    api_key = fields.Char(string="API Key",
                          help="You will get the API key from ClickSend")

    @api.model
    def get_values(self):
        """ This function will super the getter method to get the values of
        username and api_key"""
        res = super(ResConfigSettings, self).get_values()
        username = self.env['ir.config_parameter'].sudo(). \
            get_param('clicksend_sms_odoo.username')
        api_key = self.env['ir.config_parameter'].sudo(). \
            get_param('clicksend_sms_odoo.api_key')
        res.update(
            username=username,
            api_key=api_key,
        )
        return res

    def set_values(self):
        """ This function will super the setter method to set the values of
         username and api_key"""
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('clicksend_sms_odoo.username', self.username)
        param.set_param('clicksend_sms_odoo.api_key', self.api_key)
