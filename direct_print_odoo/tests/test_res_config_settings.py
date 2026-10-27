# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import logging

from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)

GATEWAY = ('odoo.addons.direct_print_odoo.models.res_config_settings.'
           'Gateway')


def _printer(printer_id, name):
    return SimpleNamespace(id=printer_id, name=name,
                           description='%s description' % name,
                           state='online')


@tagged('post_install', '-at_install')
class TestCheckPrinters(TransactionCase):
    """Test cases for fetching printers from PrintNode."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key_print_node = 'test_api_key'
        cls.Printer = cls.env['printer.details']
        cls.Printer.search([]).unlink()
        cls.settings = cls.env['res.config.settings'].create({})

    @patch(GATEWAY)
    def test_printers_created(self, mock_gateway_class):
        """Printers returned by PrintNode are stored."""
        gateway = mock_gateway_class.return_value
        gateway.computers.return_value = [SimpleNamespace(id=1)]
        gateway.printers.return_value = [
            _printer(11, 'P1'), _printer(12, 'P2')
        ]
        self.settings.action_check_printers()
        self.assertEqual(
            sorted(self.Printer.search([]).mapped('id_of_printer')),
            ['11', '12'],
        )
        logger.info("PASSED : test_printers_created")

    @patch(GATEWAY)
    def test_existing_printers_not_duplicated(self, mock_gateway_class):
        """Running the check twice does not duplicate printers."""
        gateway = mock_gateway_class.return_value
        gateway.computers.return_value = [SimpleNamespace(id=1)]
        gateway.printers.return_value = [_printer(11, 'P1')]
        self.settings.action_check_printers()
        self.settings.action_check_printers()
        self.assertEqual(self.Printer.search_count([]), 1)
        logger.info("PASSED : test_existing_printers_not_duplicated")

    @patch(GATEWAY)
    def test_no_computer_connected(self, mock_gateway_class):
        """An empty computer list asks the user to connect a computer."""
        mock_gateway_class.return_value.computers.return_value = []
        with self.assertRaisesRegex(ValidationError, 'connect a computer'):
            self.settings.action_check_printers()
        logger.info("PASSED : test_no_computer_connected")

    @patch(GATEWAY)
    def test_computer_without_id(self, mock_gateway_class):
        """A computer id of zero asks the user to connect a computer."""
        gateway = mock_gateway_class.return_value
        gateway.computers.return_value = [SimpleNamespace(id=0)]
        with self.assertRaisesRegex(ValidationError, 'connect a computer'):
            self.settings.action_check_printers()
        logger.info("PASSED : test_computer_without_id")

    @patch(GATEWAY)
    def test_invalid_credentials(self, mock_gateway_class):
        """Any gateway failure is reported as invalid credentials."""
        mock_gateway_class.return_value.computers.side_effect = Exception
        with self.assertRaisesRegex(ValidationError, 'valid credentials'):
            self.settings.action_check_printers()
        logger.info("PASSED : test_invalid_credentials")
