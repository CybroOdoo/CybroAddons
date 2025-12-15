# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields,models


class ResConfigSettings(models.TransientModel):
    """Fields for configuring the API keys used by the Vapi Voice Assistant
     integration."""
    _inherit = 'res.config.settings'

    vapi_private_api_key = fields.Char(
        string="Private Key",
        config_parameter='ora_ai_base.vapi_private_api_key',
        help="Vapi Voice Assistant's private API key.")
    vapi_public_api_key = fields.Char(
        string="Public Key",
        config_parameter='ora_ai_base.vapi_public_api_key',
        help=" Vapi Voice Assistant's public API key. ")
