# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDirectPrint(TransactionCase):
    """Test cases for direct print logic and PrintNode integration."""

    def setUp(self):
        super(TestDirectPrint, self).setUp()
        self.company = self.env.company
        self.company.api_key_print_node = 'test_api_key'
        self.ConfigSettings = self.env['res.config.settings']

    @patch('odoo.addons.direct_print_odoo.models.res_config_settings.Gateway')
    def test_action_check_printers(self, mock_gateway_class):
        """Test action_check_printers with mocked Gateway."""
        # Setup mocks
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        mock_computer = MagicMock()
        mock_computer.id = '1'
        mock_gateway.computers.return_value = [mock_computer]

        mock_printer = MagicMock()
        mock_printer.id = '101'
        mock_printer.name = 'Test Mock Printer'
        mock_printer.description = 'Mocked Printer for Testing'
        mock_printer.state = 'online'
        mock_gateway.printers.return_value = [mock_printer]

        # Execute
        config = self.ConfigSettings.create({})
        config.action_check_printers()

        # Verify
        printer = self.env['printer.details'].search([('id_of_printer', '=', '101')])
        self.assertTrue(printer.exists())
        self.assertEqual(printer.printers_name, 'Test Mock Printer')

    @patch('odoo.addons.direct_print_odoo.models.res_config_settings.Gateway')
    def test_action_check_printers_no_computer(self, mock_gateway_class):
        """Test action_check_printers when no computer is found."""
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway
        mock_gateway.computers.return_value = []

        config = self.ConfigSettings.create({})
        with self.assertRaises(ValidationError):
            config.action_check_printers()

    @patch('odoo.addons.direct_print_odoo.models.res_config_settings.Gateway')
    def test_action_check_printers_invalid_credentials(self, mock_gateway_class):
        """Test action_check_printers with invalid credentials (exception)."""
        mock_gateway_class.side_effect = Exception("Invalid API Key")

        config = self.ConfigSettings.create({})
        with self.assertRaises(ValidationError):
            config.action_check_printers()
