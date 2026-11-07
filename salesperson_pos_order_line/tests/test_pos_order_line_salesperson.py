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


@tagged('post_install', '-at_install', 'salesperson_pos_order_line')
class TestPosOrderLineSalesperson(TransactionCase):
    """Comprehensive test suite for Sales Person on POS Order Line module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesperson_1 = cls.env['res.users'].create({
            'name': 'Salesperson Alice',
            'login': 'alice@example.com',
            'email': 'alice@example.com',
        })
        cls.salesperson_2 = cls.env['res.users'].create({
            'name': 'Salesperson Bob',
            'login': 'bob@example.com',
            'email': 'bob@example.com',
        })
        cls.product_with_salesperson = cls.env['product.product'].create({
            'name': 'Product With Salesperson',
            'available_in_pos': True,
            'pos_sales_person_id': cls.salesperson_1.id,
        })
        cls.product_without_salesperson = cls.env['product.product'].create({
            'name': 'Product Without Salesperson',
            'available_in_pos': True,
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Main POS Shop',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def _create_pos_order(self, lines_data):
        """Helper to create a POS order with lines."""
        lines = []
        for line in lines_data:
            lines.append((0, 0, {
                'product_id': line.get('product_id', self.product_with_salesperson.id),
                'qty': line.get('qty', 1),
                'price_unit': line.get('price_unit', 50.0),
                'price_subtotal': line.get('price_subtotal', 50.0),
                'price_subtotal_incl': line.get('price_subtotal_incl', 50.0),
                'user_id': line.get('user_id', False),
            }))
        return self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'lines': lines,
            'amount_total': sum(l.get('price_subtotal_incl', 50.0) for l in lines_data),
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

    def test_01_create_pos_order_line_with_salesperson(self):
        """Test creating a POS order line with a single salesperson assigned."""
        order = self._create_pos_order([{'user_id': self.salesperson_1.id}])
        self.assertEqual(len(order.lines), 1)
        line = order.lines[0]
        self.assertEqual(line.user_id, self.salesperson_1)
        self.assertEqual(line.user_id.name, 'Salesperson Alice')

    def test_02_create_multiple_lines_distinct_salespersons(self):
        """Test POS order containing multiple lines with different salespersons and unassigned lines."""
        order = self._create_pos_order([
            {'product_id': self.product_with_salesperson.id, 'user_id': self.salesperson_1.id},
            {'product_id': self.product_without_salesperson.id, 'user_id': self.salesperson_2.id},
            {'product_id': self.product_without_salesperson.id, 'user_id': False},
        ])
        self.assertEqual(len(order.lines), 3)
        self.assertEqual(order.lines[0].user_id, self.salesperson_1)
        self.assertEqual(order.lines[1].user_id, self.salesperson_2)
        self.assertFalse(order.lines[2].user_id)

    def test_03_update_order_line_salesperson(self):
        """Test reassigning and unassigning salesperson on existing POS order lines."""
        order = self._create_pos_order([{'user_id': self.salesperson_1.id}])
        line = order.lines[0]
        self.assertEqual(line.user_id, self.salesperson_1)

        # Reassign to Salesperson 2
        line.write({'user_id': self.salesperson_2.id})
        self.assertEqual(line.user_id, self.salesperson_2)

        # Unassign salesperson
        line.write({'user_id': False})
        self.assertFalse(line.user_id)

    def test_04_load_pos_data_fields(self):
        """Test that user_id is properly exposed in _load_pos_data_fields for pos.order.line."""
        fields = self.env['pos.order.line']._load_pos_data_fields(self.pos_config)
        self.assertIn('user_id', fields)

    def test_05_load_pos_data_domain_users(self):
        """Test that res.users._load_pos_data_domain returns an empty domain to load all users in POS."""
        domain = self.env['res.users']._load_pos_data_domain({})
        self.assertEqual(domain, [])

    def test_06_product_salesperson_field(self):
        """Test setting, updating, and clearing pos_sales_person_id on product.product."""
        self.assertEqual(self.product_with_salesperson.pos_sales_person_id, self.salesperson_1)
        self.assertFalse(self.product_without_salesperson.pos_sales_person_id)

        # Update product's default salesperson
        self.product_without_salesperson.write({'pos_sales_person_id': self.salesperson_2.id})
        self.assertEqual(self.product_without_salesperson.pos_sales_person_id, self.salesperson_2)

        # Clear product's default salesperson
        self.product_without_salesperson.write({'pos_sales_person_id': False})
        self.assertFalse(self.product_without_salesperson.pos_sales_person_id)

    def test_07_pos_order_prepare_order_line(self):
        """Test pos.order._prepare_order_line with various input payloads."""
        order = self.env['pos.order'].new()

        # With user_id present
        res = order._prepare_order_line({'user_id': self.salesperson_1.id, 'qty': 2})
        self.assertEqual(res.get('user_id'), self.salesperson_1.id)

        # Without user_id present
        res_no_user = order._prepare_order_line({'qty': 5})
        self.assertIsNone(res_no_user.get('user_id'))

        # With user_id as False
        res_false_user = order._prepare_order_line({'user_id': False})
        self.assertFalse(res_false_user.get('user_id'))

    def test_08_controller_get_pos_sales_person(self):
        """Test /get_pos_sales_person controller response with valid, empty, and optional arguments."""
        from odoo.addons.salesperson_pos_order_line.controllers.pos_salesperson import PosSalesPersonController

        controller = PosSalesPersonController()
        mock_request = MagicMock()
        mock_request.env = self.env

        with patch('odoo.addons.salesperson_pos_order_line.controllers.pos_salesperson.request', mock_request):
            # Product with salesperson assigned
            data = controller.get_pos_sales_person(self.product_with_salesperson.id)
            self.assertEqual(data.get('sales_person'), 'Salesperson Alice')

            # Product without salesperson assigned
            data_empty = controller.get_pos_sales_person(self.product_without_salesperson.id)
            self.assertEqual(data_empty.get('sales_person'), '')

            # Calling with optional pos_order_line_id
            data_with_line = controller.get_pos_sales_person(
                self.product_with_salesperson.id, pos_order_line_id=123
            )
            self.assertEqual(data_with_line.get('sales_person'), 'Salesperson Alice')

            # Non-existent product ID
            data_non_existent = controller.get_pos_sales_person(999999)
            self.assertEqual(data_non_existent.get('sales_person'), '')

    def test_09_order_copy_preserves_salesperson(self):
        """Test duplicating a POS order preserves salesperson on lines if lines are copied."""
        order = self._create_pos_order([{'user_id': self.salesperson_1.id}])
        copied_order = order.copy()
        if copied_order.lines:
            self.assertEqual(copied_order.lines[0].user_id, self.salesperson_1)
