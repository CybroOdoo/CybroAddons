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
    _inherit = 'res.config.settings'

    gemini_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter="ai_address_autofill.gemini_api_key",
        groups="base.group_system",
        help="Google Gemini API Key obtained from Google AI Studio (https://aistudio.google.com/).",
    )
    gemini_model = fields.Selection(
        selection=[
            ('gemini-3.5-flash', 'Gemini 3.5 Flash (Fast & Recommended)'),
            ('gemini-3.8-flash', 'Gemini 3.8 Flash (Latest & Most Powerful)'),
            ('gemini-3.5-flash-lite', 'Gemini 3.5 Flash Lite (Cost-Effective)'),
            ('gemini-flash-latest', 'Gemini Flash Latest (Auto-Updated)'),
        ],
        config_parameter="ai_address_autofill.gemini_model",
        default="gemini-3.5-flash",
        groups="base.group_system",
        required=True,
        help="The Google Gemini model used for address parsing.",
    )
    address_autofill = fields.Boolean(
        config_parameter="ai_address_autofill.address_autofill",
        default=True,
        help="Enable AI-powered address autofill in Contact form and list views.",
    )

    def action_test_gemini_connection(self):
        """Test the connection with Google Gemini using currently entered or saved credentials."""
        self.ensure_one()
        api_key = self.gemini_api_key
        if not api_key:
            params = self.env['ir.config_parameter'].sudo()
            api_key = params.get_str('ai_address_autofill.gemini_api_key', default='') if hasattr(params, 'get_str') else (params.get_param('ai_address_autofill.gemini_api_key', '') if hasattr(params, 'get_param') else '')

        if not api_key or not api_key.strip():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._('Configuration Missing'),
                    'message': self.env._('Please enter an API Key before testing the connection.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }

        success, msg = self.env['gemini.service'].test_connection(
            api_key=api_key.strip(),
            model_name=self.gemini_model,
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Connection Successful') if success else self.env._('Connection Failed'),
                'message': msg,
                'type': 'success' if success else 'danger',
                'sticky': not success,
            },
        }
