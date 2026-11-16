# -*- coding: utf-8 -*-
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

from odoo.tests.common import TransactionCase, tagged
from printnodeapi.auth import ApiError, NetworkError


@tagged('post_install', '-at_install')
class TestPosKitchenPrintBase(TransactionCase):
    """Base class for POS kitchen printer direct print test cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category_drinks = cls.env['pos.category'].create({
            'name': 'Drinks',
        })
        cls.category_food = cls.env['pos.category'].create({
            'name': 'Food',
        })
        cls.category_dessert = cls.env['pos.category'].create({
            'name': 'Dessert',
        })

        cls.product_coke = cls.env['product.product'].create({
            'name': 'Coca Cola',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [cls.category_drinks.id])],
        })
        cls.product_burger = cls.env['product.product'].create({
            'name': 'Cheese Burger',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [cls.category_food.id])],
        })
        cls.product_cake = cls.env['product.product'].create({
            'name': 'Chocolate Cake',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [cls.category_dessert.id])],
        })

        cls.pos_config_restricted = cls.env['pos.config'].create({
            'name': 'Restaurant Restricted POS',
            'module_pos_restaurant': True,
            'limit_categories': True,
            'iface_available_categ_ids': [(6, 0, [cls.category_drinks.id, cls.category_food.id])],
        })

        cls.pos_config_unrestricted = cls.env['pos.config'].create({
            'name': 'Restaurant Unrestricted POS',
            'module_pos_restaurant': True,
            'limit_categories': False,
        })

        cls.printer_details_bar = cls.env['printer.details'].create({
            'id_of_printer': '101',
            'printers_name': 'Bar Thermal Printer',
            'printer_description': 'Epson TM-T88VI at Bar Counter',
            'state': 'online',
        })

        cls.printer_details_kitchen = cls.env['printer.details'].create({
            'id_of_printer': '102',
            'printers_name': 'Kitchen Hot Station Printer',
            'printer_description': 'Star Micronics SP700 in Kitchen',
            'state': 'online',
        })

        cls.kitchen_printer_bar = cls.env['pos.kitchen.printer'].create({
            'name': 'Bar Station',
            'printer_id': cls.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [cls.pos_config_restricted.id])],
            'category_ids': [(6, 0, [cls.category_drinks.id])],
        })

        cls.kitchen_printer_kitchen = cls.env['pos.kitchen.printer'].create({
            'name': 'Kitchen Hot Station',
            'printer_id': cls.printer_details_kitchen.id,
            'pos_config_ids': [(6, 0, [cls.pos_config_restricted.id])],
            'category_ids': [(6, 0, [cls.category_food.id])],
        })

    def _set_config_param(self, key, value):
        param_model = self.env['ir.config_parameter'].sudo()
        if hasattr(param_model, 'set_str'):
            param_model.set_str(key, value)
        else:
            param_model.set_param(key, value)


@tagged('post_install', '-at_install')
class TestPrinterDetails(TestPosKitchenPrintBase):
    """Test suite for printer.details model."""

    def test_01_printer_details_crud(self):
        """Test CRUD operations and rec_name on printer.details model."""
        printer = self.env['printer.details'].create({
            'id_of_printer': '999',
            'printers_name': 'Expedite Printer',
            'printer_description': 'Line Printer for Expediter',
            'state': 'offline',
        })
        self.assertEqual(printer.printers_name, 'Expedite Printer')
        self.assertEqual(printer.display_name, 'Expedite Printer')
        self.assertEqual(printer.id_of_printer, '999')
        self.assertEqual(printer.state, 'offline')

        printer.write({
            'state': 'online',
            'printer_description': 'Updated Description',
        })
        self.assertEqual(printer.state, 'online')
        self.assertEqual(printer.printer_description, 'Updated Description')

        searched = self.env['printer.details'].search([('id_of_printer', '=', '999')])
        self.assertEqual(len(searched), 1)
        self.assertEqual(searched.id, printer.id)


@tagged('post_install', '-at_install')
class TestPosKitchenPrinter(TestPosKitchenPrintBase):
    """Test suite for pos.kitchen.printer model and category computation."""

    def test_01_kitchen_printer_crud(self):
        """Test CRUD on pos.kitchen.printer."""
        printer = self.env['pos.kitchen.printer'].create({
            'name': 'Dessert Station',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id])],
            'category_ids': [(6, 0, [self.category_dessert.id])],
        })
        self.assertEqual(printer.name, 'Dessert Station')
        self.assertEqual(printer.printer_id.id, self.printer_details_bar.id)
        self.assertIn(self.category_dessert, printer.category_ids)

    def test_02_compute_allowed_pos_category_ids_empty_config(self):
        """Test allowed_pos_category_ids is empty when no POS config is linked."""
        printer = self.env['pos.kitchen.printer'].create({
            'name': 'Unlinked Printer',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': False,
        })
        self.assertFalse(printer.allowed_pos_category_ids)

    def test_03_compute_allowed_pos_category_ids_restricted(self):
        """Test allowed_pos_category_ids returns restricted POS categories."""
        printer = self.env['pos.kitchen.printer'].create({
            'name': 'Restricted Printer',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id])],
        })
        expected_categories = self.pos_config_restricted.iface_available_categ_ids
        self.assertEqual(printer.allowed_pos_category_ids, expected_categories)

    def test_04_compute_allowed_pos_category_ids_unrestricted(self):
        """Test allowed_pos_category_ids returns all categories when any POS config is unrestricted."""
        printer = self.env['pos.kitchen.printer'].create({
            'name': 'Unrestricted Printer',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id, self.pos_config_unrestricted.id])],
        })
        all_categories = self.env['pos.category'].search([])
        self.assertEqual(printer.allowed_pos_category_ids, all_categories)

    def test_05_multi_recordset_compute(self):
        """Test _compute_allowed_pos_category_ids on a multi-record recordset."""
        printer_1 = self.env['pos.kitchen.printer'].create({
            'name': 'Multi 1',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id])],
        })
        printer_2 = self.env['pos.kitchen.printer'].create({
            'name': 'Multi 2',
            'printer_id': self.printer_details_kitchen.id,
            'pos_config_ids': [(6, 0, [self.pos_config_unrestricted.id])],
        })
        printers = printer_1 | printer_2
        printers._compute_allowed_pos_category_ids()
        self.assertEqual(printer_1.allowed_pos_category_ids, self.pos_config_restricted.iface_available_categ_ids)
        self.assertEqual(printer_2.allowed_pos_category_ids, self.env['pos.category'].search([]))


@tagged('post_install', '-at_install')
class TestResConfigSettings(TestPosKitchenPrintBase):
    """Test suite for PrintNode printer check and configuration settings."""

    def setUp(self):
        super().setUp()
        self.settings = self.env['res.config.settings'].create({})

    def test_01_printer_notification_structure(self):
        """Test _printer_notification returns proper dictionary structure."""
        notification = self.settings._printer_notification("Test Message", notification_type="warning")
        self.assertEqual(notification['type'], 'ir.actions.client')
        self.assertEqual(notification['tag'], 'display_notification')
        self.assertEqual(notification['params']['message'], 'Test Message')
        self.assertEqual(notification['params']['type'], 'warning')
        self.assertTrue(notification['params']['sticky'])

        success_notif = self.settings._printer_notification("Done", notification_type="success")
        self.assertFalse(success_notif['params']['sticky'])

    def test_02_action_check_printers_no_api_key(self):
        """Test action_check_printers when API key is missing."""
        self.settings.api_key_print_node = False
        res = self.settings.action_check_printers()
        self.assertIn('Please provide a PrintNode API Key first.', res['params']['message'])
        self.assertEqual(res['params']['type'], 'warning')

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
    def test_03_action_check_printers_no_computers(self, mock_gateway_cls):
        """Test action_check_printers when no computers are linked to PrintNode."""
        mock_gateway = MagicMock()
        mock_gateway.computers.return_value = []
        mock_gateway_cls.return_value = mock_gateway

        self.settings.api_key_print_node = "dummy_api_key_123"
        res = self.settings.action_check_printers()
        self.assertIn('No computers found in your PrintNode account', res['params']['message'])
        self.assertEqual(res['params']['type'], 'warning')

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
    def test_04_action_check_printers_no_printers_found(self, mock_gateway_cls):
        """Test action_check_printers when computer has no printers."""
        mock_gateway = MagicMock()
        mock_computer = MagicMock()
        mock_computer.id = 12
        mock_gateway.computers.return_value = [mock_computer]
        mock_gateway.printers.return_value = []
        mock_gateway_cls.return_value = mock_gateway

        self.settings.api_key_print_node = "dummy_api_key_123"
        res = self.settings.action_check_printers()
        self.assertIn('No printers found for the connected computer', res['params']['message'])
        self.assertEqual(res['params']['type'], 'warning')

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
    def test_05_action_check_printers_sync_success(self, mock_gateway_cls):
        """Test action_check_printers successfully synchronizes new and existing printers."""
        mock_gateway = MagicMock()
        mock_computer = MagicMock()
        mock_computer.id = 15
        mock_gateway.computers.return_value = [mock_computer]

        printer_1 = MagicMock()
        printer_1.id = "101"  # Existing printer
        printer_1.name = "Bar Thermal Printer"
        printer_1.description = "Bar printer desc"
        printer_1.state = "online"

        printer_2 = MagicMock()
        printer_2.id = "202"  # New printer
        printer_2.name = "Pantry Printer"
        printer_2.description = "Pantry station"
        printer_2.state = "online"

        mock_gateway.printers.return_value = [printer_1, printer_2]
        mock_gateway_cls.return_value = mock_gateway

        self.settings.api_key_print_node = "dummy_api_key_123"
        res = self.settings.action_check_printers()

        self.assertIn('Available printers have been checked successfully', res['params']['message'])
        self.assertEqual(res['params']['type'], 'success')

        new_printer = self.env['printer.details'].search([('id_of_printer', '=', '202')])
        self.assertTrue(new_printer)
        self.assertEqual(new_printer.printers_name, 'Pantry Printer')

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
    def test_06_action_check_printers_api_error(self, mock_gateway_cls):
        """Test action_check_printers handling ApiError and NetworkError."""
        mock_gateway = MagicMock()
        mock_gateway.computers.side_effect = ApiError(401, 'Unauthorized', "Invalid authentication key")
        mock_gateway_cls.return_value = mock_gateway

        self.settings.api_key_print_node = "invalid_api_key"
        res = self.settings.action_check_printers()
        self.assertIn('Connection failed:', res['params']['message'])
        self.assertIn('Invalid authentication key', res['params']['message'])
        self.assertEqual(res['params']['type'], 'danger')

        mock_gateway.computers.side_effect = NetworkError("PrintNode server unreachable")
        res_net = self.settings.action_check_printers()
        self.assertIn('Connection failed: PrintNode server unreachable', res_net['params']['message'])
        self.assertEqual(res_net['params']['type'], 'danger')

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
    def test_07_action_check_printers_type_value_error(self, mock_gateway_cls):
        """Test action_check_printers handling TypeError or ValueError."""
        mock_gateway = MagicMock()
        mock_gateway.computers.side_effect = ValueError("Malformed JSON")
        mock_gateway_cls.return_value = mock_gateway

        self.settings.api_key_print_node = "dummy_api_key"
        res = self.settings.action_check_printers()
        self.assertIn('Invalid response received from PrintNode', res['params']['message'])
        self.assertEqual(res['params']['type'], 'danger')


@tagged('post_install', '-at_install')
class TestPosOrderDirectPrint(TestPosKitchenPrintBase):
    """Test suite for pos.order direct kitchen print logic and ticket formatting."""

    def setUp(self):
        super().setUp()
        self._set_config_param(
            'pos_direct_kitchen_print.api_key_print_node',
            'valid_test_api_key',
        )

    def test_01_get_printnode_api_key(self):
        """Test _get_printnode_api_key retrieves the key via get_str and get_param."""
        pos_order_model = self.env['pos.order']
        key = pos_order_model._get_printnode_api_key()
        self.assertEqual(key, 'valid_test_api_key')

        # Test fallback when get_str is not available (mock legacy ir.config_parameter)
        mock_param = MagicMock(spec=['get_param', 'sudo'])
        mock_param.sudo.return_value = mock_param
        mock_param.get_param.return_value = 'legacy_key'

        orig_getitem = type(self.env).__getitem__

        def fake_getitem(*args):
            model_name = args[0] if len(args) == 1 else args[1]
            if model_name == 'ir.config_parameter':
                return mock_param
            return orig_getitem(*args)

        with patch.object(type(self.env), '__getitem__', side_effect=fake_getitem):
            key_fallback = pos_order_model._get_printnode_api_key()
            self.assertEqual(key_fallback, 'legacy_key')

    def test_02_print_kitchen_order_no_printers(self):
        """Test print_kitchen_order when POS has no kitchen printers assigned."""
        order_data = {
            'pos_config_id': self.pos_config_unrestricted.id,
            'lines': [{'product_id': self.product_coke.id, 'qty': 1}],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertFalse(res['success'])
        self.assertIn('No kitchen printers configured', res['message'])

    def test_03_print_kitchen_order_no_api_key(self):
        """Test print_kitchen_order when PrintNode API key is not set."""
        self._set_config_param(
            'pos_direct_kitchen_print.api_key_print_node',
            '',
        )
        order_data = {
            'pos_config_id': self.pos_config_restricted.id,
            'lines': [{'product_id': self.product_coke.id, 'qty': 1}],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertFalse(res['success'])
        self.assertIn('PrintNode API Key is not configured', res['message'])

    def test_04_print_kitchen_order_no_matching_lines(self):
        """Test print_kitchen_order when order items do not match printer categories."""
        order_data = {
            'pos_config_id': self.pos_config_restricted.id,
            'lines': [{'product_id': self.product_cake.id, 'qty': 1}],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertFalse(res['success'])
        self.assertIn('No order items match the configured kitchen printer categories', res['message'])

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.PosOrder._send_to_printnode')
    def test_05_print_kitchen_order_all_success(self, mock_send):
        """Test print_kitchen_order succeeds for all printers."""
        mock_send.return_value = (True, "")

        order_data = {
            'pos_config_id': self.pos_config_restricted.id,
            'name': 'Order 001',
            'lines': [
                {'product_id': self.product_coke.id, 'qty': 2},
                {'product_id': self.product_burger.id, 'qty': 1},
            ],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertTrue(res['success'])
        self.assertIn('Kitchen order printed successfully on:', res['message'])
        self.assertEqual(mock_send.call_count, 2)

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.PosOrder._send_to_printnode')
    def test_06_print_kitchen_order_partial_success(self, mock_send):
        """Test print_kitchen_order when one printer succeeds and one printer fails."""
        def side_effect(printer, lines, order_name, order_data=None):
            if printer.id == self.kitchen_printer_bar.id:
                return True, ""
            return False, "Offline"

        mock_send.side_effect = side_effect

        order_data = {
            'pos_config_id': self.pos_config_restricted.id,
            'name': 'Order 002',
            'lines': [
                {'product_id': self.product_coke.id, 'qty': 1},
                {'product_id': self.product_burger.id, 'qty': 1},
            ],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertTrue(res['success'])
        self.assertTrue(res.get('partial'))
        self.assertIn('Printed to:', res['message'])
        self.assertIn('Failed:', res['message'])

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.PosOrder._send_to_printnode')
    def test_07_print_kitchen_order_all_failed(self, mock_send):
        """Test print_kitchen_order when all printers fail."""
        mock_send.return_value = (False, "Network Timeout")

        order_data = {
            'pos_config_id': self.pos_config_restricted.id,
            'name': 'Order 003',
            'lines': [
                {'product_id': self.product_coke.id, 'qty': 1},
            ],
        }
        res = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertFalse(res['success'])
        self.assertIn('Failed to send print job:', res['message'])

    def test_08_prepare_kitchen_tickets_routing(self):
        """Test _prepare_kitchen_tickets splits tickets per printer categories correctly."""
        order_data = {
            'lines': [
                {
                    'product_id': self.product_coke.id,
                    'qty': 2,
                    'full_product_name': 'Coca Cola 330ml',
                    'customer_note': 'With Ice',
                    'internal_note': '[{"text": "Add Lemon"}]',
                },
                {
                    'product_id': self.product_burger.id,
                    'qty': 1,
                    'full_product_name': 'Cheese Burger (No Pickle)',
                    'customer_note': '',
                    'internal_note': '',
                },
            ],
        }
        printers = self.kitchen_printer_bar | self.kitchen_printer_kitchen
        tickets = self.env['pos.order']._prepare_kitchen_tickets(order_data, printers)

        self.assertIn(self.kitchen_printer_bar, tickets)
        self.assertIn(self.kitchen_printer_kitchen, tickets)
        self.assertEqual(len(tickets[self.kitchen_printer_bar]), 1)
        self.assertEqual(tickets[self.kitchen_printer_bar][0]['name'], 'Coca Cola 330ml')
        self.assertEqual(tickets[self.kitchen_printer_bar][0]['qty'], 2)
        self.assertEqual(tickets[self.kitchen_printer_bar][0]['customer_note'], 'With Ice')

        self.assertEqual(len(tickets[self.kitchen_printer_kitchen]), 1)
        self.assertEqual(tickets[self.kitchen_printer_kitchen][0]['name'], 'Cheese Burger (No Pickle)')

        # Test printer with no category_ids assigned (catches all products)
        all_printer = self.env['pos.kitchen.printer'].create({
            'name': 'All Categ Printer',
            'printer_id': self.printer_details_bar.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id])],
            'category_ids': False,
        })
        all_tickets = self.env['pos.order']._prepare_kitchen_tickets(order_data, all_printer)
        self.assertEqual(len(all_tickets[all_printer]), 2)

    def test_09_send_to_printnode_guard_clauses(self):
        """Test guard clauses and validation in _send_to_printnode."""
        pos_order = self.env['pos.order']

        # Empty lines
        ok, msg = pos_order._send_to_printnode(self.kitchen_printer_bar, [], 'Order 1')
        self.assertFalse(ok)
        self.assertEqual(msg, "No lines to print.")

        # Missing API Key
        self._set_config_param(
            'pos_direct_kitchen_print.api_key_print_node',
            '',
        )
        lines = [{'name': 'Drink', 'qty': 1}]
        ok, msg = pos_order._send_to_printnode(self.kitchen_printer_bar, lines, 'Order 1')
        self.assertFalse(ok)
        self.assertIn("PrintNode API Key not configured", msg)

        # Restore API Key
        self._set_config_param(
            'pos_direct_kitchen_print.api_key_print_node',
            'valid_test_api_key',
        )

        # Printer without id_of_printer
        unconfigured_details = self.env['printer.details'].create({
            'printers_name': 'Ghost Printer',
            'id_of_printer': False,
        })
        bad_printer = self.env['pos.kitchen.printer'].create({
            'name': 'Bad Printer',
            'printer_id': unconfigured_details.id,
            'pos_config_ids': [(6, 0, [self.pos_config_restricted.id])],
        })
        ok, msg = pos_order._send_to_printnode(bad_printer, lines, 'Order 1')
        self.assertFalse(ok)
        self.assertIn("has no mapped PrintNode printer", msg)

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.Gateway')
    def test_10_send_to_printnode_formatting_and_execution(self, mock_gateway_cls):
        """Test full ticket formatting with tables, notes, parenthesized product names, and API call."""
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway

        order_data = {
            'order_type': 'Dine In',
            'table_name': 'Table 5',
            'order_customer_note': 'VIP Guest',
            'order_internal_note': '[{"text": "Urgent"}]',
        }
        lines = [
            {
                'name': 'Double Burger (Extra Cheese)',
                'qty': 2,
                'customer_note': 'Well done',
                'internal_note': '[{"text": "No Mayo"}, {"text": "Extra Napkins"}]',
            },
            {
                'name': 'French Fries',
                'qty': 1,
                'customer_note': '',
                'internal_note': 'Raw string note',  # fallback non-JSON
            },
        ]

        ok, msg = self.env['pos.order']._send_to_printnode(
            self.kitchen_printer_kitchen,
            lines,
            order_name='POS/2026/001',
            order_data=order_data,
        )

        self.assertTrue(ok)
        self.assertEqual(msg, "")
        mock_gateway_cls.assert_called_once_with(url="https://api.printnode.com", apikey="valid_test_api_key")
        mock_gateway.PrintJob.assert_called_once()

        job_kwargs = mock_gateway.PrintJob.call_args[1]
        self.assertEqual(job_kwargs['printer'], 102)
        self.assertEqual(job_kwargs['job_type'], 'raw')
        self.assertIn("POS/2026/001", job_kwargs['title'])

        binary_text = job_kwargs['binary'].decode('utf-8')
        self.assertIn("KITCHEN ORDER", binary_text)
        self.assertIn("Order: POS/2026/001", binary_text)
        self.assertIn("Type: Dine In", binary_text)
        self.assertIn("Table: Table 5", binary_text)
        self.assertIn("Order Note: VIP Guest", binary_text)
        self.assertIn("Order Message: Urgent", binary_text)
        self.assertIn("2 x Double Burger", binary_text)
        self.assertIn("(Extra Cheese)", binary_text)
        self.assertIn("Customer Note: Well done", binary_text)
        self.assertIn("Note: No Mayo\nExtra Napkins", binary_text)
        self.assertIn("1 x French Fries", binary_text)
        self.assertIn("Note: Raw string note", binary_text)

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.Gateway')
    def test_11_send_to_printnode_exception_handling(self, mock_gateway_cls):
        """Test _send_to_printnode handles exceptions raised during Gateway.PrintJob."""
        mock_gateway = MagicMock()
        mock_gateway.PrintJob.side_effect = RuntimeError("Socket timeout")
        mock_gateway_cls.return_value = mock_gateway

        lines = [{'name': 'Drink', 'qty': 1}]
        ok, msg = self.env['pos.order']._send_to_printnode(
            self.kitchen_printer_bar,
            lines,
            order_name='POS/001',
        )
        self.assertFalse(ok)
        self.assertIn("Socket timeout", msg)