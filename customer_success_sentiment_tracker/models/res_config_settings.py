# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """
    This class is Inheriting the model res.config.setting.
     add some extra fields and functions for the model.
    """
    _inherit = 'res.config.settings'

    openai_api_key = fields.Char(
        string="OpenAI API Key",
        copy=False,
        help="Enter your secret API key from the OpenAI platform. This key is required to authenticate "
             "requests for sentiment analysis and summary generation. It is stored securely and hidden from view."

    )

    model_id = fields.Selection([
        ('gpt-4o-mini', 'gpt-4o-mini'),
        ('gpt-4o', 'gpt-4o'),
        ('gpt-3.5-turbo', 'gpt-3.5-turbo'),
    ], string="OpenAI Model",
        help="Select the GPT model used for processing text. 'gpt-4o-mini' is the "
             "recommended default as it provides high accuracy with faster response times "
             "and lower costs.")

    enable_ai_sentiment = fields.Boolean(
        string="Enable AI Sentiment",
        help="Toggle this to activate real-time AI sentiment analysis. When enabled, "
             "every new helpdesk ticket and customer message will be automatically "
             "analyzed and scored."
    )

    @api.model
    def get_values(self):
        """Retrieves the saved OpenAI configuration settings from the database to display in the settings view."""
        res = super().get_values()
        res.update({
            'openai_api_key': self.env['ir.config_parameter'].sudo().get_param(
                'customer_success_sentiment_tracker.openai_api_key', default=''),
            'model_id': self.env['ir.config_parameter'].sudo().get_param(
                'customer_success_sentiment_tracker.model_id', default=''),
            'enable_ai_sentiment': self.env['ir.config_parameter'].sudo().get_param(
                'customer_success_sentiment_tracker.enable_ai', default=False) == 'True',
        })
        return res

    def set_values(self):
        """Validates and securely saves the active OpenAI configuration parameters to the database."""
        # Validate before saving
        if self.enable_ai_sentiment:
            if not self.openai_api_key:
                raise ValidationError("Please provide an OpenAI API key.")
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_success_sentiment_tracker.openai_api_key',
            self.openai_api_key or '')
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_success_sentiment_tracker.model_id',
            self.model_id or '')
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_success_sentiment_tracker.enable_ai',
            self.enable_ai_sentiment)

    def action_test_openai_connection(self):
        """Tests the provided OpenAI API key and displays a success notification if the connection is valid."""
        if not self.openai_api_key:
            raise ValidationError("Please enter an OpenAI API key.")
        self._validate_openai_connection()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'OpenAI connection successful.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _validate_openai_connection(self):
        """Makes a test HTTP request to the OpenAI models endpoint to verify the API key is authentic and active."""
        url = "https://api.openai.com/v1/models"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 401:
                raise ValidationError("Invalid OpenAI API Key.")
            if response.status_code != 200:
                raise ValidationError(
                    f"OpenAI Error ({response.status_code}): {response.text}"
                )
        except requests.exceptions.Timeout:
            raise ValidationError("OpenAI connection timed out.")
        except requests.exceptions.ConnectionError:
            raise ValidationError("Cannot connect to OpenAI servers.")
