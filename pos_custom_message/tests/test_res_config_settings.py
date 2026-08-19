# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for the res_config_settings model."""

    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        # Create a POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config',
        })
        # Create a Custom Message
        self.custom_message = self.env['pos.custom.message'].create({
            'title': 'Test Message',
            'message_text': 'This is a test message',
            'message_type': 'info',
            'execution_time': 10.5,
            'pos_config_ids': [(4, self.pos_config.id)]
        })

    def test_res_config_settings_values(self):
        """Test set_values and get_values of res.config.settings."""
        # Create settings record
        config_settings = self.env['res.config.settings'].create({
            'message_ids': [(4, self.custom_message.id)]
        })

        # Test set_values
        config_settings.set_values()
        param = self.env['ir.config_parameter'].sudo().get_param('pos_custom_message.message_ids')
        self.assertEqual(param, str([self.custom_message.id]),
                         "Parameter should store the message IDs")

        # Test get_values
        values = config_settings.get_values()
        self.assertIn('message_ids', values, "get_values should return message_ids")
        self.assertEqual(values['message_ids'][0][2], [self.custom_message.id],
                         "get_values should return correct message IDs")
