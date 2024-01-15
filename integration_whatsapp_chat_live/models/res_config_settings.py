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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
        This class used to inherit Res Configuration for adding extra fields
    """
    _inherit = 'res.config.settings'

    mobile_phone_no = fields.Char(srting='Mobile Phone No:',
                                  config_parameter="integration_whatsapp_chat_live.mobile_phone_no",
                                  help='User Can add mobile number')
    custom_message = fields.Char(string="Custom Message",
                                 config_parameter="integration_whatsapp_chat_live.custom_message",
                                 help='User Can add custom message')
