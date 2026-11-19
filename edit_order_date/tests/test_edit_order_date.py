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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEditOrderDate(TransactionCase):
    """Test suite for edit_order_date module functionality and security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_edit_order_date = cls.env.ref(
            'edit_order_date.edit_order_date_group_user',
        )
        cls.group_sale_user = cls.env.ref(
            'sales_team.group_sale_salesman_all_leads',
        )

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

        cls.user_authorized = cls.env['res.users'].create({
            'name': 'Authorized User',
            'login': 'authorized_test_user@example.com',
            'email': 'authorized_test_user@example.com',
            'group_ids': [
                (6, 0, [cls.group_sale_user.id, cls.group_edit_order_date.id]),
            ],
        })

        cls.user_unauthorized = cls.env['res.users'].create({
            'name': 'Unauthorized User',
            'login': 'unauthorized_test_user@example.com',
            'email': 'unauthorized_test_user@example.com',
            'group_ids': [
                (6, 0, [cls.group_sale_user.id]),
            ],
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
            ],
        })
        cls.sale_order.action_confirm()

    def test_01_authorized_user_can_edit_date_order(self):
        """Test that a user with the security group can edit date_order on a confirmed order."""
        new_date = fields.Datetime.now() - timedelta(days=2)
        self.sale_order.with_user(self.user_authorized).write({
            'date_order': new_date,
        })
        self.assertEqual(
            self.sale_order.date_order,
            new_date,
            "Authorized user should be able to update order date.",
        )

    def test_02_unauthorized_user_cannot_edit_date_order(self):
        """Test that a user without the security group receives a UserError on a confirmed order."""
        new_date = fields.Datetime.now() - timedelta(days=5)
        with self.assertRaises(UserError):
            self.sale_order.with_user(self.user_unauthorized).write({
                'date_order': new_date,
            })

    def test_03_unauthorized_user_can_write_other_fields(self):
        """Test that modifying fields other than date_order succeeds for an unauthorized user."""
        self.sale_order.with_user(self.user_unauthorized).write({
            'client_order_ref': 'PO-TEST-1234',
        })
        self.assertEqual(
            self.sale_order.client_order_ref,
            'PO-TEST-1234',
            "Unauthorized user should be able to edit other allowed fields.",
        )

    def test_04_unauthorized_user_can_edit_date_on_draft_order(self):
        """Test that date_order can be changed on draft orders without requiring the security group."""
        draft_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        new_date = fields.Datetime.now() + timedelta(days=3)
        draft_order.with_user(self.user_unauthorized).write({
            'date_order': new_date,
        })
        self.assertEqual(
            draft_order.date_order,
            new_date,
            "Any user should be able to edit order date on a quotation/draft order.",
        )

    def test_05_unauthorized_user_writing_same_date_does_not_raise(self):
        """Test that writing the existing date_order does not trigger UserError."""
        self.sale_order.with_user(self.user_unauthorized).write({
            'date_order': self.sale_order.date_order,
        })

    def test_06_form_view_rendering_for_both_users(self):
        """Test that sale order form view renders successfully for both authorized and unauthorized users."""
        form_view_id = self.env.ref('sale.view_order_form').id
        view_unauthorized = self.env['sale.order'].with_user(self.user_unauthorized).get_view(
            view_id=form_view_id, view_type='form',
        )
        self.assertIn('date_order', view_unauthorized['arch'])

        view_authorized = self.env['sale.order'].with_user(self.user_authorized).get_view(
            view_id=form_view_id, view_type='form',
        )
        self.assertIn('date_order', view_authorized['arch'])
