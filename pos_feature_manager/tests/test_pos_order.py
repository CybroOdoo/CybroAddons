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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestPosOrderServerRestrictions(TransactionCase):
    """Test suite for server-side enforcement of POS feature restrictions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Restriction Test Store',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'name': 'Restriction Test Session',
            'config_id': cls.pos_config.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test POS Product',
            'list_price': 100.0,
            'available_in_pos': True,
        })
        cls.payment_method = cls.env['pos.payment.method'].search([], limit=1)
        if not cls.payment_method:
            cls.payment_method = cls.env['pos.payment.method'].create({
                'name': 'Cash Test Method',
                'type': 'cash',
            })

        # Restricted Cashier Employee
        cls.restricted_employee = cls.env['hr.employee'].create({
            'name': 'Restricted Employee',
            'pos_allow_payments': False,
            'pos_allow_discount': False,
        })

        # Allowed Cashier Employee
        cls.allowed_employee = cls.env['hr.employee'].create({
            'name': 'Allowed Employee',
            'pos_allow_payments': True,
            'pos_allow_discount': True,
        })

        # Manager Employee with bypass
        cls.manager_employee = cls.env['hr.employee'].create({
            'name': 'Manager Employee',
            'pos_allow_payments': False,
            'pos_allow_discount': False,
        })

        # Restricted User without employee
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted POS User',
            'login': 'restricted_pos_user_test',
            'email': 'restricted_user_order@test.com',
            'pos_allow_payments': False,
            'pos_allow_discount': False,
        })

        if hasattr(cls.pos_config, 'manager_employee_ids'):
            cls.pos_config.write({
                'manager_employee_ids': [(4, cls.manager_employee.id)],
            })

    def test_server_check_blocks_discount_for_restricted_cashier(self):
        """Verify that server-side check raises ValidationError when a restricted cashier applies discount."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'employee_id': self.restricted_employee.id,
            'amount_tax': 0.0,
            'amount_total': 90.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 90.0,
                'price_subtotal_incl': 90.0,
                'discount': 10.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order._check_pos_feature_restrictions()

    def test_server_check_blocks_payments_for_restricted_cashier(self):
        """Verify that server-side check raises ValidationError when a restricted cashier processes payments."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'employee_id': self.restricted_employee.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'payment_ids': [(0, 0, {
                'payment_method_id': self.payment_method.id,
                'amount': 100.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order._check_pos_feature_restrictions()

    def test_server_check_allows_order_for_permitted_cashier(self):
        """Verify that an order with discount and payments passes validation when permitted."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'employee_id': self.allowed_employee.id,
            'amount_tax': 0.0,
            'amount_total': 95.0,
            'amount_paid': 95.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 95.0,
                'price_subtotal_incl': 95.0,
                'discount': 5.0,
            })],
            'payment_ids': [(0, 0, {
                'payment_method_id': self.payment_method.id,
                'amount': 95.0,
            })],
        })

        # Should not raise any exception
        order._check_pos_feature_restrictions()

    def test_server_check_manager_bypass_restrictions(self):
        """Verify that a manager employee bypasses server-side discount and payment restrictions."""
        if hasattr(self.pos_config, 'manager_employee_ids'):
            order = self.env['pos.order'].create({
                'session_id': self.pos_session.id,
                'employee_id': self.manager_employee.id,
                'amount_tax': 0.0,
                'amount_total': 85.0,
                'amount_paid': 85.0,
                'amount_return': 0.0,
                'lines': [(0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100.0,
                    'qty': 1,
                    'price_subtotal': 85.0,
                    'price_subtotal_incl': 85.0,
                    'discount': 15.0,
                })],
                'payment_ids': [(0, 0, {
                    'payment_method_id': self.payment_method.id,
                    'amount': 85.0,
                })],
            })

            # Should bypass restrictions because employee is a manager in the POS config
            order._check_pos_feature_restrictions()

    def test_server_check_blocks_discount_for_restricted_user(self):
        """Verify that server-side check raises ValidationError when a restricted user (cashier) applies discount."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'user_id': self.restricted_user.id,
            'employee_id': False,
            'amount_tax': 0.0,
            'amount_total': 90.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 90.0,
                'price_subtotal_incl': 90.0,
                'discount': 10.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order._check_pos_feature_restrictions()

    def test_server_check_blocks_payments_for_restricted_user(self):
        """Verify that server-side check raises ValidationError when a restricted user (cashier) processes payments."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'user_id': self.restricted_user.id,
            'employee_id': False,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'payment_ids': [(0, 0, {
                'payment_method_id': self.payment_method.id,
                'amount': 100.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order._check_pos_feature_restrictions()

    def test_process_saved_order_enforces_restrictions(self):
        """Verify that _process_saved_order calls _check_pos_feature_restrictions and blocks invalid orders."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'employee_id': self.restricted_employee.id,
            'amount_tax': 0.0,
            'amount_total': 90.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 90.0,
                'price_subtotal_incl': 90.0,
                'discount': 10.0,
            })],
        })

        with self.assertRaises(ValidationError):
            order._process_saved_order(False)

    def test_server_check_order_without_payments_or_discounts_allowed(self):
        """Verify that an order with neither discount nor payments is permitted for restricted cashier."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'employee_id': self.restricted_employee.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
                'qty': 1,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
                'discount': 0.0,
            })],
        })

        # Should not raise
        order._check_pos_feature_restrictions()
