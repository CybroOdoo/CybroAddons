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
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderDiscountApproval(SaleCommon):
    """Test cases for Sale Order Discount Approval workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and users for discount approval tests."""
        super().setUpClass()
        cls._enable_discounts()

        cls.user_discount_controlled = cls.env['res.users'].create({
            'name': 'Discount Controlled User',
            'login': 'controlled_user',
            'email': 'controlled@example.com',
            'is_discount_control': True,
            'allow_discount': 10.0,
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_salesman').id),
            ],
        })

        cls.user_normal = cls.env['res.users'].create({
            'name': 'Normal User',
            'login': 'normal_user',
            'email': 'normal@example.com',
            'is_discount_control': False,
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_salesman').id),
            ],
        })

        mgr_group_ref = (
            'sale_order_discount_approval_odoo.'
            'sale_order_discount_approval_odoo_group_manager'
        )
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Discount Approval Manager',
            'login': 'manager_user',
            'email': 'manager@example.com',
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_manager').id),
                Command.link(cls.env.ref(mgr_group_ref).id),
            ],
        })

        cls.discount_product = cls.env['product.product'].create({
            'name': 'Discount Product',
            'type': 'service',
        })
        cls.env.company.sale_discount_product_id = cls.discount_product

    def test_line_discount_within_limit(self):
        """Test confirming a sale order with discount within user limit
        goes straight to 'sale' state without needing approval."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 5.0,
                }),
            ],
        })
        self.assertEqual(sale_order.state, 'draft')
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertFalse(sale_order.approval_user_id)

    def test_line_discount_exceeds_limit(self):
        """Test that confirming an order with discount exceeding limit
        does NOT confirm early, logs to chatter, sends notification,
        and confirms properly only upon manager approval."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 15.0,
                }),
            ],
        })

        mail_count_before = self.env['mail.mail'].sudo().search_count([])
        sale_order.action_confirm()

        # Critical Check: Verify order was NOT confirmed early
        self.assertEqual(sale_order.state, 'waiting_for_approval')
        self.assertNotEqual(sale_order.state, 'sale')
        self.assertFalse(sale_order.approval_user_id)
        if hasattr(sale_order, 'picking_ids'):
            self.assertFalse(
                sale_order.picking_ids,
                "Stock pickings must not be created prior to manager approval",
            )

        # Check chatter log for approval request
        self.assertTrue(
            any(
                "Waiting For Approval" in (m.body or "")
                or "exceeds" in (m.body or "")
                for m in sale_order.message_ids
            ),
            "Approval request must be logged in chatter",
        )

        mail_count_after = self.env['mail.mail'].sudo().search_count([])
        self.assertGreater(mail_count_after, mail_count_before)

        # Manager approves the order
        sale_order.with_user(self.user_manager).action_waiting_approval()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(sale_order.approval_user_id, self.user_manager)

        # Check chatter log for approval confirmation
        self.assertTrue(
            any(
                "Discount approved by" in (m.body or "")
                for m in sale_order.message_ids
            ),
            "Manager approval must be logged in chatter",
        )

    def test_normal_user_no_discount_control(self):
        """Test that users without discount control can confirm orders."""
        sale_order = self.env['sale.order'].with_user(
            self.user_normal,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 50.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertFalse(sale_order.approval_user_id)

    def test_global_discount_within_limit(self):
        """Test global discount percentage within limit confirms normally."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': self.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -5.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')

    def test_global_discount_exceeds_limit(self):
        """Test that global discount exceeding limit does not confirm early."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': self.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -15.0,
                }),
            ],
        })
        sale_order.action_confirm()

        # Check order was NOT confirmed early
        self.assertEqual(sale_order.state, 'waiting_for_approval')
        self.assertNotEqual(sale_order.state, 'sale')
        self.assertFalse(sale_order.approval_user_id)

        # Manager approves
        sale_order.with_user(self.user_manager).action_waiting_approval()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(sale_order.approval_user_id, self.user_manager)

    def test_action_draft_resets_approval_user(self):
        """Test resetting cancelled order to draft clears approval_user_id."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 15.0,
                }),
            ],
        })
        sale_order.action_confirm()
        sale_order.with_user(self.user_manager).action_waiting_approval()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(sale_order.approval_user_id, self.user_manager)

        sale_order.with_user(self.user_manager).action_cancel()
        self.assertEqual(sale_order.state, 'cancel')

        sale_order.action_draft()
        self.assertEqual(sale_order.state, 'draft')
        self.assertFalse(sale_order.approval_user_id)

    def test_batch_confirmation(self):
        """Test confirming multiple sale orders in a batch."""
        orders = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create([
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({
                        'product_id': self.product.id,
                        'product_uom_qty': 1,
                        'price_unit': 100.0,
                        'discount': 2.0,
                    }),
                ],
            },
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({
                        'product_id': self.product.id,
                        'product_uom_qty': 1,
                        'price_unit': 100.0,
                        'discount': 20.0,
                    }),
                ],
            },
        ])
        orders.action_confirm()
        self.assertEqual(orders[0].state, 'sale')
        self.assertEqual(orders[1].state, 'waiting_for_approval')

    def test_manager_without_email(self):
        """Test notification skip when a manager has no email set."""
        original_email = self.user_manager.partner_id.email
        self.user_manager.partner_id.sudo().email = False
        try:
            sale_order = self.env['sale.order'].with_user(
                self.user_discount_controlled,
            ).create({
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({
                        'product_id': self.product.id,
                        'product_uom_qty': 1,
                        'price_unit': 100.0,
                        'discount': 25.0,
                    }),
                ],
            })
            sale_order.action_confirm()
            self.assertEqual(sale_order.state, 'waiting_for_approval')
        finally:
            self.user_manager.partner_id.sudo().email = original_email

    def test_non_manager_cannot_approve(self):
        """Test that a non-manager cannot approve an order."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 15.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'waiting_for_approval')
        with self.assertRaises(UserError):
            sale_order.with_user(
                self.user_discount_controlled,
            ).action_waiting_approval()

    def test_cancel_waiting_for_approval_order(self):
        """Test cancelling an order directly from waiting_for_approval."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 20.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'waiting_for_approval')
        sale_order.with_user(self.user_manager).action_cancel()
        self.assertEqual(sale_order.state, 'cancel')

    def test_exact_boundary_discount(self):
        """Test discount equal to user limit confirms without approval."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 10.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')

    def test_order_with_section_and_note_lines(self):
        """Test order containing sections and notes alongside discounts."""
        sale_order = self.env['sale.order'].with_user(
            self.user_discount_controlled,
        ).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Main Section',
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'display_type': 'line_note',
                    'name': 'Special instructions note',
                }),
                Command.create({
                    'product_id': self.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -12.0,
                }),
            ],
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'waiting_for_approval')
