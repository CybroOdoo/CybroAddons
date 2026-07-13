# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
import requests

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Configuration settings for AI Dynamic Dashboard."""
    _inherit = 'res.config.settings'

    api_key = fields.Char(
        string="API Key",
        copy=False,
        help="Enter your secret API key. This key is required to authenticate requests to external AI services. It is stored securely and hidden from view."
    )
    ai_service_type = fields.Selection(
        selection=[('gemini', 'Google Gemini')],
        string="AI Service",
        help="Choose the external AI service for dashboard insights."
    )
    enable_external_ai = fields.Boolean(
        string="Use External AI",
        help="Toggle this to enable external AI models for dashboard analysis. When enabled, the system will use external AI services to generate insights and summaries."
    )

    @api.model
    def get_values(self):
        """Retrieves the saved OpenAI configuration settings from the database to display in the settings view."""
        res = super().get_values()
        res.update({
            'api_key': self.env['ir.config_parameter'].sudo().get_param(
                'odoo_dynamic_dashboard.api_key', default=''),
            'ai_service_type': self.env['ir.config_parameter'].sudo().get_param(
                'odoo_dynamic_dashboard.ai_service_type', default=''),
            'enable_external_ai': self.env['ir.config_parameter'].sudo().get_param(
                'odoo_dynamic_dashboard.enable_ai', default=False) == 'True',
        })
        return res

    def set_values(self):
        """Validates and securely saves the active OpenAI configuration parameters to the database."""
        if self.enable_external_ai:
            if not self.api_key:
                raise ValidationError("Please provide an OpenAI API key.")
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_dynamic_dashboard.api_key',
            self.api_key or ''
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_dynamic_dashboard.ai_service_type',
            self.ai_service_type or ''
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_dynamic_dashboard.enable_ai',
            self.enable_external_ai
        )

    def action_test_connection(self):
        """Tests the provided OpenAI API key and displays a success notification if the connection is valid."""
        if not self.api_key:
            raise ValidationError("Please enter an AI API key.")
        self._validate_openai_connection()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'AI connection successful.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _validate_openai_connection(self):
        """Verifies the Gemini API key by listing available models."""
        url = "https://generativelanguage.googleapis.com/v1beta/models?key={}".format(self.api_key)

        try:
            response = requests.get(url, timeout=15)

            if response.status_code in [400, 401, 403]:
                raise ValidationError("Invalid Gemini API Key or Permission Denied.")

            if response.status_code != 200:
                raise ValidationError(
                    "Gemini Error ({}): {}".format(response.status_code, response.text)
                )

        except requests.exceptions.Timeout:
            raise ValidationError("Gemini connection timed out.")
        except requests.exceptions.ConnectionError:
            raise ValidationError("Cannot connect to Google servers.")