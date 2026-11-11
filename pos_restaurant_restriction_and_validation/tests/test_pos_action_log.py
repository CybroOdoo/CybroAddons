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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosActionLog(TransactionCase):
    """Unit tests for pos.action.log model behavior and immutability."""

    @classmethod
    def setUpClass(cls):
        """Set up test users, products, and user groups."""
        super().setUpClass()
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')

        cls.cashier_user = cls.env['res.users'].create({
            'name': 'Audit Test Cashier',
            'login': 'audit_cashier_user',
            'email': 'cashier@audit.com',
            'group_ids': [(6, 0, [cls.pos_user_group.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Audit Test Manager',
            'login': 'audit_manager_user',
            'email': 'manager@audit.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id])],
            'pos_security_pin': '1234',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Audit Log Product',
            'list_price': 25.0,
            'available_in_pos': True,
        })

    def test_action_log_creation(self):
        """Verify action log creates with all fields populated."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': 'Test Cashier Front',
            'action_type': 'orderline_quantity_update',
            'approved_by': self.manager_user.id,
            'order_ref': 'POS/TEST/001',
            'product_id': self.product.id,
            'old_qty': 2.0,
            'new_qty': 1.0,
        })
        self.assertEqual(log.user_id, self.cashier_user)
        self.assertEqual(log.cashier_name, 'Test Cashier Front')
        self.assertEqual(log.action_type, 'orderline_quantity_update')
        self.assertEqual(log.approved_by, self.manager_user)
        self.assertEqual(log.order_ref, 'POS/TEST/001')
        self.assertEqual(log.product_id, self.product)
        self.assertEqual(log.old_qty, 2.0)
        self.assertEqual(log.new_qty, 1.0)
        self.assertFalse(log.is_consumed)

    def test_action_log_immutability(self):
        """Verify non-superusers cannot modify audit log entries."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': 'Cashier 1',
            'action_type': 'orderline_delete',
            'approved_by': self.manager_user.id,
            'order_ref': 'POS/TEST/002',
        })
        with self.assertRaises(UserError):
            log.with_user(self.cashier_user).write({'cashier_name': 'Hacked Cashier'})

        with self.assertRaises(UserError):
            log.with_user(self.manager_user).write({'cashier_name': 'Modified By Manager'})

    def test_action_log_deletion_protection(self):
        """Verify non-superusers cannot delete audit log entries."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': 'Cashier 2',
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'POS/TEST/003',
        })
        with self.assertRaises(UserError):
            log.with_user(self.cashier_user).unlink()

        with self.assertRaises(UserError):
            log.with_user(self.manager_user).unlink()

    def test_action_log_superuser_bypass(self):
        """Verify superuser can write and delete log entries when necessary."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': 'Superuser Target',
            'action_type': 'session_close',
            'approved_by': self.manager_user.id,
        })
        su_env = self.env(su=True)
        log_su = log.with_env(su_env)
        log_su.write({'cashier_name': 'Updated By Superuser'})
        self.assertEqual(log_su.cashier_name, 'Updated By Superuser')
        log_su.unlink()
        self.assertFalse(log.exists())

    def test_all_action_types_support(self):
        """Verify all valid action types can be logged."""
        action_types = [
            'orderline_quantity_update',
            'orderline_delete',
            'delete_order',
            'session_close',
        ]
        for atype in action_types:
            log = self.env['pos.action.log'].sudo().create({
                'user_id': self.cashier_user.id,
                'action_type': atype,
                'approved_by': self.manager_user.id,
            })
            self.assertEqual(log.action_type, atype)
