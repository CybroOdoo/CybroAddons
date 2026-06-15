# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026 TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjali VP(<https://www.cybrosys.com>)
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
import json
from odoo.tests.common import TransactionCase, HttpCase, tagged


@tagged('post_install', '-at_install')
class TestMandatoryFieldHighlight(TransactionCase):
    """Test case for the mandatory_field_highlight config settings."""

    def test_config_settings_get_set_values(self):
        """Test setting and getting values in res.config.settings"""
        # Create a new config settings record
        config = self.env['res.config.settings'].create({
            'margin_left_color': '#FF0000',
            'margin_right_color': '#00FF00',
            'margin_top_color': '#0000FF',
            'margin_bottom_color': '#FFFF00',
            'field_background_color': '#00FFFF',
        })

        # Save the settings (execute() is normally used in res.config.settings)
        config.execute()

        # Check if the values are correctly set in the system parameters
        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(
            get_param('mandatory_field_highlight.margin_left_color'),
            '#FF0000',
            "Margin left color config parameter was not saved correctly"
        )
        self.assertEqual(
            get_param('mandatory_field_highlight.margin_right_color'),
            '#00FF00',
            "Margin right color config parameter was not saved correctly"
        )
        self.assertEqual(
            get_param('mandatory_field_highlight.margin_top_color'),
            '#0000FF',
            "Margin top color config parameter was not saved correctly"
        )
        self.assertEqual(
            get_param('mandatory_field_highlight.margin_bottom_color'),
            '#FFFF00',
            "Margin bottom color config parameter was not saved correctly"
        )
        self.assertEqual(
            get_param('mandatory_field_highlight.field_background_color'),
            '#00FFFF',
            "Field background color config parameter was not saved correctly"
        )

        # Retrieve settings through get_values
        retrieved_values = config.get_values()
        self.assertEqual(retrieved_values.get('margin_left_color'), '#FF0000')
        self.assertEqual(retrieved_values.get('margin_right_color'), '#00FF00')
        self.assertEqual(retrieved_values.get('margin_top_color'), '#0000FF')
        self.assertEqual(retrieved_values.get('margin_bottom_color'), '#FFFF00')
        self.assertEqual(retrieved_values.get('field_background_color'), '#00FFFF')


@tagged('post_install', '-at_install')
class TestMandatoryFieldHighlightController(HttpCase):
    """Test suite for the MandatoryFieldSettings controller routes."""

    def test_get_config_params_route(self):
        """Verify the controller endpoint /mandatory/config_params returns colors."""
        # Setup specific config values
        self.env['ir.config_parameter'].sudo().set_param(
            'mandatory_field_highlight.margin_left_color', '#FF0000')
        self.env['ir.config_parameter'].sudo().set_param(
            'mandatory_field_highlight.margin_right_color', '#00FF00')
        self.env['ir.config_parameter'].sudo().set_param(
            'mandatory_field_highlight.margin_top_color', '#0000FF')
        self.env['ir.config_parameter'].sudo().set_param(
            'mandatory_field_highlight.margin_bottom_color', '#FFFF00')
        self.env['ir.config_parameter'].sudo().set_param(
            'mandatory_field_highlight.field_background_color', '#00FFFF')

        # Since it is a public JSON-RPC route, we can call it without authentication.
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {},
            "id": 1,
        }

        response = self.url_open(
            '/mandatory/config_params',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertIn('result', res_json, "Response should contain a result key")
        
        result = res_json['result']
        self.assertEqual(result.get('margin_left_color'), '#FF0000')
        self.assertEqual(result.get('margin_right_color'), '#00FF00')
        self.assertEqual(result.get('margin_top_color'), '#0000FF')
        self.assertEqual(result.get('margin_bottom_color'), '#FFFF00')
        self.assertEqual(result.get('field_background_color'), '#00FFFF')
