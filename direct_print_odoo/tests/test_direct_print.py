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
#############################################################################
from unittest.mock import MagicMock, patch
from werkzeug.exceptions import HTTPException
from odoo.exceptions import ValidationError
from odoo.http import request_var
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.direct_print_odoo.controllers.direct_print_odoo import (
    ReportControllers,
)

GATEWAY_CTRL_PATH = (
    'odoo.addons.direct_print_odoo.controllers.direct_print_odoo.Gateway'
)



class MockComputer:
    """Mock PrintNode computer object."""

    def __init__(self, computer_id):
        self.id = computer_id


class MockPrinter:
    """Mock PrintNode printer object."""

    def __init__(self, printer_id, name, description, state):
        self.id = printer_id
        self.name = name
        self.description = description
        self.state = state


@tagged('post_install', '-at_install')
class TestDirectPrintOdoo(TransactionCase):
    """Test suite for Direct Print module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key_print_node = False
        cls.company.available_printers_id = False
        cls.company.printers_ids = [(5, 0, 0)]
        cls.company.is_multiple_printers = False

        cls.report_cls = type(cls.env['ir.actions.report'])

        cls.printer_1 = cls.env['printer.details'].create({
            'id_of_printer': '101',
            'printers_name': 'Office Printer 1',
            'printer_description': 'LaserJet',
            'state': 'online',
        })
        cls.printer_2 = cls.env['printer.details'].create({
            'id_of_printer': '102',
            'printers_name': 'Warehouse Printer 2',
            'printer_description': 'Thermal',
            'state': 'online',
        })

    def test_settings_and_company_fields(self):
        """Verify configuration settings and company fields."""
        self.env['res.config.settings'].create({
            'api_key_print_node': 'test_api_key_123',
            'available_printers_id': self.printer_1.id,
            'is_multiple_printers': True,
            'printers_ids': [(6, 0, [self.printer_1.id, self.printer_2.id])],
        })
        self.assertEqual(self.company.api_key_print_node, 'test_api_key_123')
        self.assertEqual(
            self.company.available_printers_id.id, self.printer_1.id
        )
        self.assertTrue(self.company.is_multiple_printers)
        self.assertEqual(
            set(self.company.printers_ids.ids),
            {self.printer_1.id, self.printer_2.id},
        )

    def test_action_check_printers_no_api_key(self):
        """Action check printers must raise ValidationError when no API key."""
        self.company.api_key_print_node = False
        settings = self.env['res.config.settings'].create({})
        with self.assertRaises(ValidationError):
            settings.action_check_printers()

    def test_action_check_printers_no_computers(self):
        """Action check printers raises ValidationError if no computers."""
        self.company.api_key_print_node = 'test_key'
        settings = self.env['res.config.settings'].create({})
        with patch(
            'odoo.addons.direct_print_odoo.models.res_config_settings.Gateway'
        ) as mock_gateway_cls:
            mock_gateway = MagicMock()
            mock_gateway.computers.return_value = []
            mock_gateway_cls.return_value = mock_gateway
            with self.assertRaises(ValidationError) as cm:
                settings.action_check_printers()
            self.assertIn('connect a computer', str(cm.exception).lower())

    def test_action_check_printers_multiple_computers(self):
        """Action check printers iterates across all connected computers."""
        self.company.api_key_print_node = 'valid_test_key'
        settings = self.env['res.config.settings'].create({})

        comp_1 = MockComputer(1)
        comp_2 = MockComputer(2)
        printer_c1 = MockPrinter(201, 'DeskJet', 'Desk printer', 'online')
        printer_c2_a = MockPrinter(
            202, 'LabelJet', 'Label printer', 'online'
        )
        printer_c2_b = MockPrinter(
            203, 'Receipt', 'Receipt printer', 'offline'
        )

        with patch(
            'odoo.addons.direct_print_odoo.models.res_config_settings.Gateway'
        ) as mock_gateway_cls:
            mock_gateway = MagicMock()
            mock_gateway.computers.return_value = [comp_1, comp_2]

            def fake_printers(computer=None):
                if computer == 1:
                    return [printer_c1]
                if computer == 2:
                    return [printer_c2_a, printer_c2_b]
                return []

            mock_gateway.printers.side_effect = fake_printers
            mock_gateway_cls.return_value = mock_gateway

            settings.action_check_printers()

            details = self.env['printer.details'].search([
                ('id_of_printer', 'in', ['201', '202', '203'])
            ])
            self.assertEqual(len(details), 3)

            # Re-running updates records without duplication
            settings.action_check_printers()
            details_after = self.env['printer.details'].search([
                ('id_of_printer', 'in', ['201', '202', '203'])
            ])
            self.assertEqual(len(details_after), 3)

    def test_action_check_printers_api_error(self):
        """Action check printers handles invalid credentials / exceptions."""
        self.company.api_key_print_node = 'invalid_key'
        settings = self.env['res.config.settings'].create({})
        with patch(
            'odoo.addons.direct_print_odoo.models.res_config_settings.Gateway'
        ) as mock_gateway_cls:
            mock_gateway = MagicMock()
            mock_gateway.computers.side_effect = Exception("Auth failed")
            mock_gateway_cls.return_value = mock_gateway
            with self.assertRaises(ValidationError) as cm:
                settings.action_check_printers()
            self.assertIn('credentials', str(cm.exception).lower())

    def test_controller_pdf_single_printer(self):
        """Controller sends PDF to single printer when configured."""
        self.company.api_key_print_node = 'test_key'
        self.company.is_multiple_printers = False
        self.company.available_printers_id = self.printer_1.id

        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.make_response = MagicMock(return_value="pdf_response")
        token = request_var.set(mock_req)

        try:
            with patch(
                GATEWAY_CTRL_PATH
            ) as mock_gateway_cls, patch.object(
                self.report_cls,
                '_render_qweb_pdf',
                return_value=(b'%PDF-1.4 test content', 'pdf'),
            ):
                mock_gw = MagicMock()
                mock_gateway_cls.return_value = mock_gw

                controller = ReportControllers()
                res = controller.report_routes(
                    'test_report', docids='1', converter='pdf'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.data, b"pdf_response")
                mock_gw.PrintJob.assert_called_once()
                call_kwargs = mock_gw.PrintJob.call_args[1]
                self.assertEqual(
                    call_kwargs['printer'], int(self.printer_1.id_of_printer)
                )
        finally:
            request_var.reset(token)

    def test_controller_pdf_multiple_printers(self):
        """Controller sends PDF to each printer when multiple enabled."""
        self.company.api_key_print_node = 'test_key'
        self.company.is_multiple_printers = True
        self.company.printers_ids = [
            (6, 0, [self.printer_1.id, self.printer_2.id])
        ]

        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.make_response = MagicMock(return_value="pdf_response")
        token = request_var.set(mock_req)

        try:
            with patch(
                GATEWAY_CTRL_PATH
            ) as mock_gateway_cls, patch.object(
                self.report_cls,
                '_render_qweb_pdf',
                return_value=(b'%PDF-1.4 test content', 'pdf'),
            ):
                mock_gw = MagicMock()
                mock_gateway_cls.return_value = mock_gw

                controller = ReportControllers()
                res = controller.report_routes(
                    'test_report', docids='1,2', converter='pdf'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.data, b"pdf_response")
                self.assertEqual(mock_gw.PrintJob.call_count, 2)
        finally:
            request_var.reset(token)

    def test_controller_pdf_printnode_failure_handled(self):
        """Controller catches PrintNode error and still returns PDF."""
        self.company.api_key_print_node = 'test_key'
        self.company.is_multiple_printers = False
        self.company.available_printers_id = self.printer_1.id

        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.make_response = MagicMock(return_value="pdf_response")
        token = request_var.set(mock_req)

        try:
            with patch(
                GATEWAY_CTRL_PATH
            ) as mock_gateway_cls, patch.object(
                self.report_cls,
                '_render_qweb_pdf',
                return_value=(b'%PDF-1.4 test content', 'pdf'),
            ):
                mock_gw = MagicMock()
                mock_gw.PrintJob.side_effect = Exception(
                    "Connection timed out"
                )
                mock_gateway_cls.return_value = mock_gw

                controller = ReportControllers()
                res = controller.report_routes(
                    'test_report', docids='1', converter='pdf'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.data, b"pdf_response")
        finally:
            request_var.reset(token)

    def test_controller_other_converters(self):
        """Test HTML, TEXT and unknown converter routing."""
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.make_response = MagicMock(side_effect=lambda x, **kw: x)
        token = request_var.set(mock_req)

        try:
            controller = ReportControllers()

            with patch.object(
                self.report_cls,
                '_render_qweb_html',
                return_value=('<html>test</html>', 'html'),
            ):
                res = controller.report_routes(
                    'test_rep', docids='1', converter='html'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.data, b'<html>test</html>')

            with patch.object(
                self.report_cls,
                '_render_qweb_text',
                return_value=('text report', 'txt'),
            ):
                res = controller.report_routes(
                    'test_rep', docids='1', converter='text'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.data, b'text report')

            with self.assertRaises(HTTPException):
                controller.report_routes(
                    'test_rep', docids='1', converter='unknown'
                )
        finally:
            request_var.reset(token)
