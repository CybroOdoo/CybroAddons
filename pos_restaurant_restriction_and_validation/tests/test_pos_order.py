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
class TestPosOrder(TransactionCase):
    """Unit tests for pos.order restaurant restriction enforcement."""

    @classmethod
    def setUpClass(cls):
        """Set up POS order test environment."""
        super().setUpClass()
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Order Test Manager',
            'login': 'order_test_mgr',
            'email': 'order_mgr@test.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': '1234',
        })
        cls.cashier_user = cls.env['res.users'].create({
            'name': 'Order Test Cashier',
            'login': 'order_test_cashier',
            'email': 'order_cashier@test.com',
            'group_ids': [(6, 0, [cls.pos_user_group.id])],
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Restaurant Test Store',
            'pos_restaurant_restriction': True,
            'pos_order_delete': True,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'name': 'Restaurant Test Session',
            'config_id': cls.pos_config.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Kitchen Pasta',
            'list_price': 15.0,
            'available_in_pos': True,
        })

    def _create_order_with_kitchen_prep(self, pos_reference='Order 001'):
        """Helper to create an order with kitchen preparation records."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': pos_reference,
            'amount_total': 30.0,
            'amount_tax': 0.0,
            'amount_paid': 30.0,
            'amount_return': 0.0,
        })
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 2.0,
            'price_unit': 15.0,
            'price_subtotal': 30.0,
            'price_subtotal_incl': 30.0,
        })
        prep_order = self.env['pos.prep.order'].create({'pos_order_id': order.id})
        self.env['pos.prep.line'].create({
            'prep_order_id': prep_order.id,
            'pos_order_line_id': line.id,
            'quantity': 3.0,
            'product_id': self.product.id,
        })
        return order

    def test_unlink_kitchen_order_blocks_unauthorized(self):
        """Verify unlinking a kitchen order raises UserError without manager approval."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/BLOCKED/01')
        with self.assertRaises(UserError):
            order.with_user(self.cashier_user).unlink()

    def test_unlink_kitchen_order_allows_authorized_by_manager(self):
        """Verify unlinking a kitchen order succeeds when initiated by a manager."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/ALLOWED/MGR')
        order.with_user(self.manager_user).unlink()
        self.assertFalse(order.exists())

    def test_unlink_kitchen_order_allows_with_approval_log(self):
        """Verify unlinking succeeds when cashier has manager approval log."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/APPROVED/LOG')
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'REF/APPROVED/LOG',
        })
        order.with_user(self.cashier_user).unlink()
        self.assertFalse(order.exists())

    def test_unlink_non_kitchen_order_succeeds(self):
        """Verify orders not sent to kitchen can be deleted without manager approval."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/NON/KITCHEN',
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 15.0,
                'qty': 1.0,
                'price_subtotal': 15.0,
                'price_subtotal_incl': 15.0,
            })],
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        order.with_user(self.cashier_user).unlink()
        self.assertFalse(order.exists())

    def test_cancel_order_from_pos_checks_manager_approval(self):
        """Verify cancel_order_from_pos blocks unauthorized cancellation."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/TEST')
        with self.assertRaises(UserError):
            order.with_user(self.cashier_user).cancel_order_from_pos()

        # Succeeds when approved
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'REF/CANCEL/TEST',
        })
        order.with_user(self.cashier_user).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_restrictions_disabled(self):
        """Verify orders can be unlinked if pos_order_delete or master switch is False."""
        self.pos_config.write({'pos_order_delete': False})
        order = self._create_order_with_kitchen_prep(pos_reference='REF/RESTRICTION/OFF')
        order.with_user(self.cashier_user).unlink()
        self.assertFalse(order.exists())

        # Test with master toggle disabled
        self.pos_config.write({
            'pos_order_delete': True,
            'pos_restaurant_restriction': False,
        })
        order2 = self._create_order_with_kitchen_prep(pos_reference='REF/RESTRICTION/OFF2')
        order2.with_user(self.cashier_user).unlink()
        self.assertFalse(order2.exists())

    def test_unlink_kitchen_order_allows_with_context_bypass(self):
        """Verify unlinking kitchen order succeeds with pos_restriction_approved context."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/ORDER/CTX/01')
        order.with_user(self.cashier_user).with_context(pos_restriction_approved=True).unlink()
        self.assertFalse(order.exists())

    def test_cancel_order_from_pos_allows_manager(self):
        """Verify manager can cancel a kitchen order directly."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/MGR')
        order.with_user(self.manager_user).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_cancel_order_from_pos_non_kitchen_succeeds(self):
        """Verify non-kitchen orders can be cancelled without manager approval."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/CANCEL/NONKITCHEN',
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 15.0,
            'amount_return': 0.0,
        })
        order.with_user(self.cashier_user).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_cancel_order_from_pos_allows_with_context_bypass(self):
        """Verify cancelling kitchen order succeeds with pos_restriction_approved context."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/CTX')
        order.with_user(self.cashier_user).with_context(
            pos_restriction_approved=True
        ).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_cancel_order_from_pos_restrictions_disabled(self):
        """Verify cancel order succeeds when pos_order_delete or master switch is False."""
        self.pos_config.write({'pos_order_delete': False})
        order = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/DIS01')
        order.with_user(self.cashier_user).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

        self.pos_config.write({
            'pos_order_delete': True,
            'pos_restaurant_restriction': False,
        })
        order2 = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/DIS02')
        order2.with_user(self.cashier_user).cancel_order_from_pos()
        self.assertEqual(order2.state, 'cancel')

    def test_cancel_order_from_pos_with_active_ids_context(self):
        """Verify cancel_order_from_pos functions correctly when called with active_ids in context."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/CANCEL/ACTIVEIDS')
        # Blocked without approval
        with self.assertRaises(UserError):
            order.with_user(self.cashier_user).with_context(
                active_ids=[order.id]
            ).cancel_order_from_pos()

        # Succeeds when approved
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'REF/CANCEL/ACTIVEIDS',
        })
        order.with_user(self.cashier_user).with_context(
            active_ids=[order.id]
        ).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_unlink_order_with_line_prep_only_blocks_unauthorized(self):
        """Verify order with prep lines on orderline only (no prep_order_ids) blocks unlink."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/LINE/PREP/ONLY',
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 15.0,
            'amount_return': 0.0,
        })
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 15.0,
            'price_subtotal': 15.0,
            'price_subtotal_incl': 15.0,
        })
        # Attach prep line directly without prep_order_id on order
        prep_order = self.env['pos.prep.order'].create({})
        self.env['pos.prep.line'].create({
            'prep_order_id': prep_order.id,
            'pos_order_line_id': line.id,
            'quantity': 1.0,
            'product_id': self.product.id,
        })
        with self.assertRaises(UserError):
            order.with_user(self.cashier_user).unlink()

    def test_cancel_order_with_line_prep_only_blocks_unauthorized(self):
        """Verify order with prep lines on orderline only blocks cancel_order_from_pos."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/CANCEL/PREP/LINE',
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 15.0,
            'amount_return': 0.0,
        })
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 15.0,
            'price_subtotal': 15.0,
            'price_subtotal_incl': 15.0,
        })
        prep_order = self.env['pos.prep.order'].create({})
        self.env['pos.prep.line'].create({
            'prep_order_id': prep_order.id,
            'pos_order_line_id': line.id,
            'quantity': 1.0,
            'product_id': self.product.id,
        })
        with self.assertRaises(UserError):
            order.with_user(self.cashier_user).cancel_order_from_pos()

    def test_unlink_order_with_line_prep_only_allows_when_approved(self):
        """Verify order with prep lines on orderline only unlinks successfully when approved."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/LINE/APPROVED',
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 15.0,
            'amount_return': 0.0,
        })
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 15.0,
            'price_subtotal': 15.0,
            'price_subtotal_incl': 15.0,
        })
        prep_order = self.env['pos.prep.order'].create({})
        self.env['pos.prep.line'].create({
            'prep_order_id': prep_order.id,
            'pos_order_line_id': line.id,
            'quantity': 1.0,
            'product_id': self.product.id,
        })
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'REF/LINE/APPROVED',
        })
        order.with_user(self.cashier_user).unlink()
        self.assertFalse(order.exists())

    def test_cancel_order_with_line_prep_only_allows_when_approved(self):
        """Verify order with prep lines on orderline only cancels successfully when approved."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'REF/CANCEL/APPROVED/LINE',
            'amount_total': 15.0,
            'amount_tax': 0.0,
            'amount_paid': 15.0,
            'amount_return': 0.0,
        })
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 15.0,
            'price_subtotal': 15.0,
            'price_subtotal_incl': 15.0,
        })
        prep_order = self.env['pos.prep.order'].create({})
        self.env['pos.prep.line'].create({
            'prep_order_id': prep_order.id,
            'pos_order_line_id': line.id,
            'quantity': 1.0,
            'product_id': self.product.id,
        })
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'REF/CANCEL/APPROVED/LINE',
        })
        order.with_user(self.cashier_user).cancel_order_from_pos()
        self.assertEqual(order.state, 'cancel')

    def test_unlink_kitchen_order_allowed_with_order_name_reference(self):
        """Verify unlinking succeeds using order.name fallback when pos_reference is empty."""
        order = self._create_order_with_kitchen_prep(pos_reference='REF/NAME/TEST')
        order.sudo().write({'pos_reference': False})
        order_name = order.name or 'ORDER/FALLBACK/NAME'
        if not order.name:
            order.sudo().write({'name': order_name})
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': order.name,
        })
        order.with_user(self.cashier_user).unlink()
        self.assertFalse(order.exists())





