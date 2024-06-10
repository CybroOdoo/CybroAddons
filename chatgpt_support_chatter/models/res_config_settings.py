# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (<https://www.cybrosys.com>)
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
##############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Add field to configuration settings """
    _inherit = "res.config.settings"

    chat_gpt_api_key = fields.Char(
        string="API Key",
        config_parameter="chatgpt_support_chatter.chat_gpt_api_key",
        help="Provide the API Key of Chat Gpt")

    def get_chat_gpt_key(self):
        """ To get Chatgpt Api Key """
        return self.env['ir.config_parameter'].sudo().get_param(
            'chatgpt_support_chatter.chat_gpt_api_key')
