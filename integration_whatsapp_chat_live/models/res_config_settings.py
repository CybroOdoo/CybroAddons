# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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
    """
        This class used to inherit Res Configuration for adding extra fields
    """
    _inherit = 'res.config.settings'

    mobile_phone_no = fields.Char(srting='Mobile Phone No:',
                                  help='User Can add mobile number')
    custom_message = fields.Text(string="Custom Message",
                                 help='User Can add custom message')

    @api.model
    def get_values(self):
        """
                Return values for the fields mobile number and custom messages
        """
        res = super(ResConfigSettings, self).get_values()

        params = self.env['ir.config_parameter'].sudo()
        mobile_no_id = params.get_param(
            'integration_whatsapp_chat_live.mobile_phone_no')
        custom_message_id = params.get_param(
            'integration_whatsapp_chat_live.custom_message')
        res.update(
            mobile_phone_no=mobile_no_id,
            custom_message=custom_message_id,
        )
        return res

    @api.model
    def set_values(self):
        """
            Set values for the fields mobile number and custom messages
        """
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "integration_whatsapp_chat_live.mobile_phone_no",
            self.mobile_phone_no)
        self.env['ir.config_parameter'].sudo().set_param(
            "integration_whatsapp_chat_live.custom_message",
            self.custom_message)
