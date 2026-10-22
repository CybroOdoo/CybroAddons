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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    """
    Extend system settings to configure Google Gemini AI integration
    for payment risk analysis.
    """
    _inherit = 'res.config.settings'

    gemini_api_key = fields.Char(
        string='Gemini API Key',
        config_parameter='predict_late_payment.gemini_api_key',
        password=True,
        help='Free API key from https://aistudio.google.com/apikey',
    )

    gemini_model = fields.Selection([
        ('gemini-3.6-flash', 'Gemini 3.6 Flash'),
        ('gemini-3.6-pro', 'Gemini 3.6 Pro'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro'),
        ('gemini-2.5-flash', 'Gemini 2.5 Flash (Deprecated)'),
        ('gemini-2.5-flash-lite', 'Gemini 2.5 Flash-Lite (Deprecated)'),
        ('gemini-2.0-flash', 'Gemini 2.0 Flash (Deprecated)'),
    ], string='Gemini Model',
        config_parameter='predict_late_payment.gemini_model',
        default='gemini-3.6-flash',
        help='Model to use for payment risk analysis.')

    @api.model
    def get_values(self):
        res = super().get_values()
        if res.get('gemini_model') in ('gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash-lite'):
            res['gemini_model'] = 'gemini-3.6-flash'
        return res

    def action_test_gemini_connection(self):
        """Test the Gemini API key and show result."""
        result = self.env['payment.risk.ai.service'].test_connection()
        ok = result.startswith('OK')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Gemini Connected!') if ok else _('Gemini Connection Failed'),
                'message': result,
                'sticky': True,
                'type': 'success' if ok else 'danger',
            },
        }

    def action_get_gemini_key(self):
        """Open Google AI Studio to get a free API key."""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://aistudio.google.com/apikey',
            'target': 'new',
        }
