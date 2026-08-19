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

    @patch('odoo.addons.pos_direct_kitchen_print.models.pos_order.Gateway')
    def test_print_kitchen_order_execution(self, mock_gateway):
        order_data = {
            'pos_config_id': self.pos_config.id,
            'name': 'ORD/001',
            'lines': [
                {'product_id': self.product_food.id, 'qty': 1},
            ]
        }
        self.env['ir.config_parameter'].sudo().set_param('pos_direct_kitchen_print.api_key_print_node', 'fake_key')
        kitchen_printer = self.kitchen_printer
        with patch.object(
            type(self.env['pos.kitchen.printer']),
            'search',
            return_value=kitchen_printer
        ):
            result = self.env['pos.order'].print_kitchen_order(order_data)
        self.assertTrue(result)
        mock_gateway.return_value.PrintJob.assert_called()

    @patch('odoo.addons.pos_direct_kitchen_print.models.res_config_settings.Gateway')
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
