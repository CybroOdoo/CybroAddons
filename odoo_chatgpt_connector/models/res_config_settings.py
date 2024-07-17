# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
import requests
from odoo import fields, models, _


def notification_response(title, notification_type, message):
    """Method notification_response returns the notification data according
    to each conditions while checking the connection to ChatGPT."""
    notification_data = {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _(title),
            'type': notification_type,
            'message': message,
            'sticky': False,
        }
    }
    return notification_data


class ResConfigSettings(models.TransientModel):
    """This class extends the base 'res.config.settings' model to include
        additional fields for configuring ChatGPT integration settings."""
    _inherit = "res.config.settings"

    api_key = fields.Char(string="API Key", help="Provide the API key here",
                          config_parameter="odoo_chatgpt_connector.api_key")

    def action_test_api(self):
        """Method action_test_api to test the connection from Odoo to
        ChatGPT"""
        url = "https://api.openai.com/v1/completions"
        payload = {'model': 'gpt-3.5-turbo-instruct'}
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_chatgpt_connector.api_key')
        if not api_key:
            notification = notification_response(title="No API key!",
                                                 notification_type="danger",
                                                 message="Please provide "
                                                         "an API Key")
            return notification
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': "application/json"
        }
        try:
            response = requests.post(url, headers=headers, json=payload,
                                     timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            notification = notification_response(title="Connection "
                                                       "Successful!",
                                                 notification_type="success",
                                                 message="Successfully "
                                                         "connected to "
                                                         "ChatGPT")
            return notification
        except requests.exceptions.Timeout:
            notification = notification_response(title="Connection Timeout!",
                                                 notification_type="danger",
                                                 message="The request to "
                                                         "ChatGPT timed out")
            return notification
        except requests.exceptions.RequestException:
            notification = notification_response(title="Connection Error!",
                                                 notification_type="danger",
                                                 message="Error connecting to "
                                                         "ChatGPT: API Key is "
                                                         "not valid")
            return notification
