# -- coding: utf-8 --
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _


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
        placeholder='AIza...',
        help='Free API key from https://aistudio.google.com/apikey')

    gemini_model = fields.Selection([
        ('gemini-2.5-flash',      'Gemini 2.5 Flash'),
        ('gemini-2.5-flash-lite', 'Gemini 2.5 Flash-Lite'),
        ('gemini-2.5-pro',        'Gemini 2.5 Pro'),
        ('gemini-2.0-flash',      'Gemini 2.0 Flash'),
    ], string='Gemini Model',
       config_parameter='predict_late_payment.gemini_model',
       default='gemini-2.5-flash',
       help='Model to use for payment risk analysis.')

    def action_test_gemini_connection(self):
        """Test the Gemini API key and show result."""
        result = self.env['payment.risk.ai.service'].test_connection()
        ok = result.startswith('OK')
        return {
            'type': 'ir.actions.client',
            'tag':  'display_notification',
            'params': {
                'title':   _('Gemini Connected!') if ok else _('Gemini Connection Failed'),
                'message': result,
                'sticky':  True,
                'type':    'success' if ok else 'danger',
            },
        }

    def action_get_gemini_key(self):
        """Open Google AI Studio to get a free API key."""
        return {
            'type':   'ir.actions.act_url',
            'url':    'https://aistudio.google.com/apikey',
            'target': 'new',
        }
