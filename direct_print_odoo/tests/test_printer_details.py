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
from odoo.tests.common import TransactionCase


class TestPrinterDetails(TransactionCase):
    """Test cases for printer.details model."""

    def setUp(self):
        super(TestPrinterDetails, self).setUp()
        self.printer_details_model = self.env['printer.details']

    def test_printer_details_creation(self):
        """Test the creation of printer details records."""
        printer = self.printer_details_model.create({
            'printers_name': 'Test Printer',
            'id_of_printer': '12345',
            'printer_description': 'A test printer for automated tests',
            'state': 'online'
        })
        self.assertEqual(printer.printers_name, 'Test Printer')
        self.assertEqual(printer.id_of_printer, '12345')
        self.assertEqual(printer.state, 'online')

    def test_printer_details_read(self):
        """Test reading printer details records."""
        printer = self.printer_details_model.create({
            'printers_name': 'Read Printer',
            'id_of_printer': '67890'
        })
        fetched_printer = self.printer_details_model.browse(printer.id)
        self.assertEqual(fetched_printer.printers_name, 'Read Printer')
