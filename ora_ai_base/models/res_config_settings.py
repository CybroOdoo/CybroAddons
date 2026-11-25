# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


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
    vapi_webhook_secret = fields.Char(
        string="Webhook Secret",
        config_parameter='ora_ai_base.vapi_webhook_secret',
        help="Shared secret token used to authenticate incoming Vapi webhook requests.")
    voice_order_auto_confirm = fields.Boolean(
        string="Auto-Confirm Voice Orders",
        config_parameter='ora_ai_base.voice_order_auto_confirm',
        help="If checked, voice orders will be automatically confirmed. If unchecked, they will remain as draft Quotations.")

    def action_open_vapi(self):
        """Open the Vapi dashboard in a new browser tab."""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://dashboard.vapi.ai/api-keys',
            'target': 'new',
        }
