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
class TestPosOrderLine(TransactionCase):
    """Unit tests for pos.order.line deletion and quantity update restrictions."""

    @classmethod
    def setUpClass(cls):
        """Set up POS order line test environment."""
        super().setUpClass()
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Line Test Manager',
            'login': 'line_test_mgr',
            'email': 'line_mgr@test.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': '1234',
        })
        cls.cashier_user = cls.env['res.users'].create({
            'name': 'Line Test Cashier',
            'login': 'line_test_cashier',
            'email': 'line_cashier@test.com',
            'group_ids': [(6, 0, [cls.pos_user_group.id])],
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Line Restaurant Store',
            'pos_restaurant_restriction': True,
            'pos_orderline_delete': True,
            'pos_orderline_quantity_update': True,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'name': 'Line Restaurant Session',
            'config_id': cls.pos_config.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Kitchen Burger',
            'list_price': 10.0,
            'available_in_pos': True,
        })

    def _create_order_with_line(self, pos_reference='Order Line Test', kitchen_sent=True):
        """Helper to create an order and line, optionally linked to prep lines."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': pos_reference,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 10.0,
                'qty': 2.0,
                'price_subtotal': 20.0,
                'price_subtotal_incl': 20.0,
            })],
            'amount_total': 20.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        line = order.lines[0]
        if kitchen_sent:
            prep_order = self.env['pos.prep.order'].create({
                'pos_order_id': order.id,
            })
            self.env['pos.prep.line'].create({
                'pos_order_line_id': line.id,
                'prep_order_id': prep_order.id,
                'product_id': self.product.id,
                'quantity': 2.0,
            })
        return order, line

    def test_unlink_kitchen_line_blocks_unauthorized(self):
        """Verify deleting a kitchen-sent line raises UserError for regular cashier."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/001', kitchen_sent=True
        )
        with self.assertRaises(UserError):
            line.with_user(self.cashier_user).unlink()

    def test_unlink_kitchen_line_allows_with_approval_log(self):
        """Verify deleting a kitchen-sent line succeeds when approved."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/002', kitchen_sent=True
        )
        vals = {
            'action_type': 'orderline_delete',
            'product_id': self.product.id,
            'approved_by': self.manager_user.id,
            'order_ref': 'LINE/REF/002',
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
        }
        self.env['pos.action.log'].sudo().create(vals)
        line.with_user(self.cashier_user).unlink()
        self.assertFalse(line.exists())

    def test_unlink_non_kitchen_line_succeeds(self):
        """Verify deleting a line not sent to kitchen succeeds without approval."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/NONKITCHEN', kitchen_sent=False
        )
        line.with_user(self.cashier_user).unlink()
        self.assertFalse(line.exists())

    def test_update_qty_kitchen_line_blocks_unauthorized(self):
        """Verify changing quantity of kitchen-sent line raises UserError without approval."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/003', kitchen_sent=True
        )
        with self.assertRaises(UserError):
            line.with_user(self.cashier_user).write({'qty': 3.0})

    def test_update_qty_kitchen_line_allows_with_approval(self):
        """Verify changing quantity succeeds when manager approval log exists."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/004', kitchen_sent=True
        )
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_quantity_update',
            'approved_by': self.manager_user.id,
            'order_ref': 'LINE/REF/004',
            'product_id': self.product.id,
            'old_qty': 2.0,
            'new_qty': 3.0,
        })
        line.with_user(self.cashier_user).write({'qty': 3.0})
        self.assertEqual(line.qty, 3.0)

    def test_update_non_qty_fields_allowed(self):
        """Verify modifying fields other than qty does not require approval."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/005', kitchen_sent=True
        )
        line.with_user(self.cashier_user).write({'discount': 5.0})
        self.assertEqual(line.discount, 5.0)

    def test_update_qty_same_value_allowed(self):
        """Verify writing the same quantity does not trigger validation error."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/006', kitchen_sent=True
        )
        line.with_user(self.cashier_user).write({'qty': line.qty})
        self.assertEqual(line.qty, 2.0)

    def test_unlink_kitchen_line_allows_manager(self):
        """Verify manager can delete a kitchen-sent line directly."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/MGR/01', kitchen_sent=True
        )
        line.with_user(self.manager_user).unlink()
        self.assertFalse(line.exists())

    def test_unlink_kitchen_line_allows_with_context_bypass(self):
        """Verify deleting kitchen line succeeds with pos_restriction_approved context."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/CTX/01', kitchen_sent=True
        )
        line.with_user(self.cashier_user).with_context(pos_restriction_approved=True).unlink()
        self.assertFalse(line.exists())

    def test_unlink_kitchen_line_restriction_disabled(self):
        """Verify deleting kitchen line succeeds when restriction toggle is turned off."""
        self.pos_config.write({'pos_orderline_delete': False})
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/DIS/01', kitchen_sent=True
        )
        line.with_user(self.cashier_user).unlink()
        self.assertFalse(line.exists())

        # Test with master restriction toggle disabled
        self.pos_config.write({
            'pos_orderline_delete': True,
            'pos_restaurant_restriction': False,
        })
        _order2, line2 = self._create_order_with_line(
            pos_reference='LINE/REF/DIS/02', kitchen_sent=True
        )
        line2.with_user(self.cashier_user).unlink()
        self.assertFalse(line2.exists())

    def test_update_qty_kitchen_line_allows_manager(self):
        """Verify manager can update quantity on kitchen-sent line directly."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/MGR/02', kitchen_sent=True
        )
        line.with_user(self.manager_user).write({'qty': 5.0})
        self.assertEqual(line.qty, 5.0)

    def test_update_qty_kitchen_line_allows_with_context_bypass(self):
        """Verify updating quantity succeeds with pos_restriction_approved context."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/CTX/02', kitchen_sent=True
        )
        line.with_user(self.cashier_user).with_context(
            pos_restriction_approved=True
        ).write({'qty': 4.0})
        self.assertEqual(line.qty, 4.0)

    def test_update_qty_kitchen_line_restriction_disabled(self):
        """Verify updating quantity succeeds when quantity update restriction is disabled."""
        self.pos_config.write({'pos_orderline_quantity_update': False})
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/DIS/03', kitchen_sent=True
        )
        line.with_user(self.cashier_user).write({'qty': 6.0})
        self.assertEqual(line.qty, 6.0)

        # Test with master toggle disabled
        self.pos_config.write({
            'pos_orderline_quantity_update': True,
            'pos_restaurant_restriction': False,
        })
        _order2, line2 = self._create_order_with_line(
            pos_reference='LINE/REF/DIS/04', kitchen_sent=True
        )
        line2.with_user(self.cashier_user).write({'qty': 7.0})
        self.assertEqual(line2.qty, 7.0)

    def test_update_qty_non_kitchen_line_allowed(self):
        """Verify modifying quantity on non-kitchen lines succeeds without approval."""
        _order, line = self._create_order_with_line(
            pos_reference='LINE/REF/NONKITCHEN/QTY', kitchen_sent=False
        )
        line.with_user(self.cashier_user).write({'qty': 9.0})
        self.assertEqual(line.qty, 9.0)

    def test_unlink_kitchen_line_allowed_with_order_name_reference(self):
        """Verify deleting kitchen line succeeds using order.name fallback when pos_reference is empty."""
        order, line = self._create_order_with_line(pos_reference='LINE/NAME/TEST', kitchen_sent=True)
        order.sudo().write({'pos_reference': False})
        order_name = order.name or 'ORDER/LINE/NAME/FALLBACK'
        if not order.name:
            order.sudo().write({'name': order_name})
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_delete',
            'product_id': self.product.id,
            'approved_by': self.manager_user.id,
            'order_ref': order.name,
        })
        line.with_user(self.cashier_user).unlink()
        self.assertFalse(line.exists())

    def test_update_qty_kitchen_line_allowed_with_order_name_reference(self):
        """Verify updating quantity succeeds using order.name fallback when pos_reference is empty."""
        order, line = self._create_order_with_line(pos_reference='LINE/QTY/TEST', kitchen_sent=True)
        order.sudo().write({'pos_reference': False})
        order_name = order.name or 'ORDER/LINE/QTY/FALLBACK'
        if not order.name:
            order.sudo().write({'name': order_name})
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_quantity_update',
            'product_id': self.product.id,
            'approved_by': self.manager_user.id,
            'order_ref': order.name,
            'old_qty': 2.0,
            'new_qty': 5.0,
        })
        line.with_user(self.cashier_user).write({'qty': 5.0})
        self.assertEqual(line.qty, 5.0)

    def test_update_qty_multi_line_recordset_blocked(self):
        """Verify updating quantity across multiple lines blocks if any kitchen-sent line lacks approval."""
        _order1, line1 = self._create_order_with_line(pos_reference='LINE/MULTI/1', kitchen_sent=True)
        _order2, line2 = self._create_order_with_line(pos_reference='LINE/MULTI/2', kitchen_sent=False)
        lines = line1 | line2
        with self.assertRaises(UserError):
            lines.with_user(self.cashier_user).write({'qty': 8.0})

