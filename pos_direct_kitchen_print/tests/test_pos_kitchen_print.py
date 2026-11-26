# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from ..models import pos_order, res_config_settings
from ..models.pos_order import PosOrder


def patch_gateway(target):
    return patch.object(target, 'Gateway')


class TestPosKitchenPrint(TransactionCase):

    def setUp(self):
        super(TestPosKitchenPrint, self).setUp()

        self.pos_config = self.env['pos.config'].search([('module_pos_restaurant', '=', False)], limit=1)
        if not self.pos_config:
            self.pos_config = self.env['pos.config'].search([], limit=1)
        self.pos_config.sudo().write({'limit_categories': False})

        self.category_kitchen = self.env['pos.category'].create({'name': 'Kitchen'})
        self.category_bar = self.env['pos.category'].create({'name': 'Bar'})

        self.printer_data = self.env['printer.details'].create({
            'id_of_printer': '123',
            'printers_name': 'Kitchen Printer',
        })

        self.kitchen_printer = self.env['pos.kitchen.printer'].create({
            'name': 'Kitchen Station',
            'printer_id': self.printer_data.id,
            'pos_config_ids': [(4, self.pos_config.id)],
            'category_ids': [(4, self.category_kitchen.id)],
        })

        products = self.env['product.product'].search([], limit=2)
        self.product_food = products[0]
        self.product_drink = products[1]

        self.product_food.write({
            'pos_categ_ids': [(4, self.category_kitchen.id)],
        })
        self.product_drink.write({
            'pos_categ_ids': [(4, self.category_bar.id)],
        })

    def test_printer_category_computation(self):
        self.kitchen_printer._compute_allowed_pos_category_ids()
        all_cats = self.env['pos.category'].search([])
        self.assertEqual(set(self.kitchen_printer.allowed_pos_category_ids.ids), set(all_cats.ids))

    def test_prepare_kitchen_tickets(self):
        order_data = {
            'lines': [
                {'product_id': self.product_food.id, 'qty': 2, 'full_product_name': 'Burger'},
                {'product_id': self.product_drink.id, 'qty': 1, 'full_product_name': 'Cola'},
            ]
        }
        tickets = self.env['pos.order']._prepare_kitchen_tickets(order_data, self.kitchen_printer)
        self.assertEqual(len(tickets), 1)
        self.assertEqual(len(tickets[self.kitchen_printer]), 1)
        self.assertEqual(tickets[self.kitchen_printer][0]['name'], 'Burger')

    def test_prepare_kitchen_tickets_no_match(self):
        order_data = {
            'lines': [
                {'product_id': self.product_drink.id, 'qty': 1, 'full_product_name': 'Cola'},
            ]
        }
        tickets = self.env['pos.order']._prepare_kitchen_tickets(order_data, self.kitchen_printer)
        self.assertEqual(len(tickets), 0)

    def test_prepare_kitchen_tickets_without_printer_categories(self):
        self.kitchen_printer.category_ids = [(5, 0, 0)]
        order_data = {
            'lines': [
                {'product_id': self.product_food.id, 'qty': 2},
                {'product_id': self.product_drink.id, 'qty': 1},
            ]
        }

        tickets = self.env['pos.order']._prepare_kitchen_tickets(
            order_data, self.kitchen_printer)

        self.assertEqual(len(tickets[self.kitchen_printer]), 2)
        self.assertEqual(tickets[self.kitchen_printer][0]['qty'], 2)
        self.assertEqual(tickets[self.kitchen_printer][1]['name'],
                         self.product_drink.display_name)

    def test_prepare_kitchen_tickets_preserves_notes(self):
        order_data = {
            'lines': [{
                'product_id': self.product_food.id,
                'qty': 1,
                'full_product_name': 'Burger (No onion)',
                'customer_note': 'Extra hot',
                'internal_note': '[{"text": "No salt"}]',
            }]
        }

        tickets = self.env['pos.order']._prepare_kitchen_tickets(
            order_data, self.kitchen_printer)

        self.assertEqual(tickets[self.kitchen_printer][0], {
            'qty': 1,
            'name': 'Burger (No onion)',
            'customer_note': 'Extra hot',
            'internal_note': '[{"text": "No salt"}]',
        })

    def test_print_kitchen_order_without_configured_printers(self):
        order_data = {
            'pos_config_id': 999999,
            'lines': [{'product_id': self.product_food.id, 'qty': 1}],
        }
        with patch.object(PosOrder, '_send_to_printnode') as send:
            result = self.env['pos.order'].print_kitchen_order(order_data)

        self.assertTrue(result)
        send.assert_not_called()

    @patch_gateway(pos_order)
    def test_send_to_printnode_formats_order_and_line_notes(self, mock_gateway):
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_direct_kitchen_print.api_key_print_node', 'fake_key')
        order_data = {
            'order_type': 'Dine In',
            'table_name': 'Table 4',
            'order_customer_note': 'Serve together',
            'order_internal_note': '[{"text": "Rush"}]',
        }
        lines = [{
            'qty': 2,
            'name': 'Burger (No onion)',
            'customer_note': 'Extra hot',
            'internal_note': '[{"text": "No salt"}]',
        }]

        self.env['pos.order']._send_to_printnode(
            self.kitchen_printer, lines, 'ORD/002', order_data)

        printed_message = mock_gateway.return_value.PrintJob.call_args.kwargs[
            'binary'].decode('utf-8')
        for expected_text in (
                'Order: ORD/002', 'Type: Dine In', 'Table: Table 4',
                'Order Note: Serve together', 'Order Message: Rush',
                '2 x Burger', '(No onion)', 'Customer Note: Extra hot',
                'Note: No salt'):
            self.assertIn(expected_text, printed_message)

    def test_send_to_printnode_without_api_key_skips_gateway(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_direct_kitchen_print.api_key_print_node', False)
        with patch_gateway(pos_order) as gateway:
            self.env['pos.order']._send_to_printnode(
                self.kitchen_printer, [{'qty': 1, 'name': 'Burger'}], 'ORD/003')

        gateway.assert_not_called()

    @patch_gateway(pos_order)
    def test_print_kitchen_order_execution(self, mock_gateway):
        order_data = {
            'pos_config_id': self.pos_config.id,
            'name': 'ORD/001',
            'lines': [
                {'product_id': self.product_food.id, 'qty': 1},
            ]
        }
        self.env['ir.config_parameter'].sudo().set_param('pos_direct_kitchen_print.api_key_print_node', 'fake_key')
        result = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertTrue(result)
        mock_gateway.return_value.PrintJob.assert_called()

    @patch_gateway(res_config_settings)
    def test_config_check_printers(self, mock_gateway):
        mock_computer = MagicMock()
        mock_computer.id = 1
        mock_gateway.return_value.computers.return_value = [mock_computer]

        mock_printer = MagicMock()
        mock_printer.id = 456
        mock_printer.name = 'New Printer'
        mock_printer.description = 'Desk'
        mock_printer.state = 'online'
        mock_gateway.return_value.printers.return_value = [mock_printer]

        config = self.env['res.config.settings'].create({
            'api_key_print_node': 'test_key'
        })
        config.action_check_printers()

        printer = self.env['printer.details'].search([('id_of_printer', '=', '456')])
        self.assertTrue(printer)
        self.assertEqual(printer.printers_name, 'New Printer')

    @patch_gateway(res_config_settings)
    def test_config_check_printers_without_api_key(self, mock_gateway):
        config = self.env['res.config.settings'].create({'api_key_print_node': False})

        action = config.action_check_printers()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertIn('API Key', action['params']['message'])
        mock_gateway.assert_not_called()

    @patch_gateway(res_config_settings)
    def test_config_check_printers_without_computers(self, mock_gateway):
        mock_gateway.return_value.computers.return_value = []
        config = self.env['res.config.settings'].create({'api_key_print_node': 'test_key'})

        action = config.action_check_printers()

        self.assertIn('No computers found', action['params']['message'])
        mock_gateway.return_value.printers.assert_not_called()

    @patch_gateway(res_config_settings)
    def test_config_check_printers_without_printers(self, mock_gateway):
        computer = MagicMock(id=1)
        mock_gateway.return_value.computers.return_value = [computer]
        mock_gateway.return_value.printers.return_value = []
        config = self.env['res.config.settings'].create({'api_key_print_node': 'test_key'})

        action = config.action_check_printers()

        self.assertIn('No printers found', action['params']['message'])
