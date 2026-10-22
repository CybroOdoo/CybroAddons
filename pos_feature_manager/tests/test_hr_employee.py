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


@tagged('post_install', '-at_install')
class TestHrEmployeePosRestrictions(TransactionCase):
    """Test suite for POS feature restriction fields on hr.employee."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POS_FIELDS = [
            'pos_allow_numpad',
            'pos_allow_payments',
            'pos_allow_discount',
            'pos_allow_qty',
            'pos_allow_price_edit',
            'pos_allow_remove_order_line',
            'pos_allow_customer_selection',
            'pos_allow_plus_minus',
        ]
        cls.employee_default = cls.env['hr.employee'].create({
            'name': 'Default Cashier Employee',
        })
        cls.employee_restricted = cls.env['hr.employee'].create({
            'name': 'Restricted Cashier Employee',
            'pos_allow_numpad': False,
            'pos_allow_payments': False,
            'pos_allow_discount': False,
            'pos_allow_qty': False,
            'pos_allow_price_edit': False,
            'pos_allow_remove_order_line': False,
            'pos_allow_customer_selection': False,
            'pos_allow_plus_minus': False,
        })

    def test_default_permissions(self):
        """Verify that all POS restriction boolean fields default to True on hr.employee."""
        for field_name in self.POS_FIELDS:
            self.assertTrue(
                self.employee_default[field_name],
                f"Field '{field_name}' should default to True on hr.employee."
            )

    def test_custom_permissions_creation(self):
        """Verify that POS restriction fields can be explicitly set to False on creation."""
        for field_name in self.POS_FIELDS:
            self.assertFalse(
                self.employee_restricted[field_name],
                f"Field '{field_name}' should be False on employee_restricted."
            )

    def test_toggle_permissions(self):
        """Verify that POS restriction fields can be updated and toggled."""
        emp = self.env['hr.employee'].create({'name': 'Toggle Test Employee'})

        # Initially True
        self.assertTrue(emp.pos_allow_qty)
        self.assertTrue(emp.pos_allow_price_edit)

        # Update to False
        emp.write({
            'pos_allow_qty': False,
            'pos_allow_price_edit': False,
        })
        self.assertFalse(emp.pos_allow_qty)
        self.assertFalse(emp.pos_allow_price_edit)

        # Other fields remain True
        self.assertTrue(emp.pos_allow_numpad)
        self.assertTrue(emp.pos_allow_payments)

        # Toggle back to True
        emp.write({'pos_allow_qty': True})
        self.assertTrue(emp.pos_allow_qty)

    def test_multiple_employees_independence(self):
        """Verify that restriction settings on one employee do not affect another."""
        emp_1 = self.env['hr.employee'].create({
            'name': 'Employee Alpha',
            'pos_allow_discount': False,
        })
        emp_2 = self.env['hr.employee'].create({
            'name': 'Employee Beta',
            'pos_allow_discount': True,
        })

        self.assertFalse(emp_1.pos_allow_discount)
        self.assertTrue(emp_2.pos_allow_discount)
