# -*- coding: utf-8 -*-
"""Test suite for invoice_salesperson_follower_restriction."""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInvoiceSalespersonFollower(TransactionCase):
    """Test suite for salesperson follower restriction on customer invoices."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment, creating users, partner, and product."""
        super().setUpClass()
        # Create user for SO creator
        cls.creator_user = cls.env['res.users'].create({
            'name': 'SO Creator User',
            'login': 'so_creator_user',
            'email': 'so_creator@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('account.group_account_invoice').id,
            ])],
        })
        # Create user for assigned Salesperson
        cls.salesperson_user = cls.env['res.users'].create({
            'name': 'Assigned Salesperson User',
            'login': 'assigned_salesperson_user',
            'email': 'assigned_salesperson@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('account.group_account_invoice').id,
            ])],
        })
        # Create second salesperson user
        cls.salesperson_user_2 = cls.env['res.users'].create({
            'name': 'Second Salesperson User',
            'login': 'second_salesperson_user',
            'email': 'second_salesperson@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('account.group_account_invoice').id,
            ])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

    def _enable_restriction(self):
        """Helper to enable the salesperson follower restriction setting."""
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_salesperson_follower_restriction.enable_restriction',
            'True',
        )

    def _disable_restriction(self):
        """Helper to disable the salesperson follower restriction setting."""
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_salesperson_follower_restriction.enable_restriction',
            False,
        )

    def _create_sale_order(self, creator, salesperson):
        """Helper to create and confirm a sale order."""
        so = self.env['sale.order'].with_user(creator).create({
            'partner_id': self.partner.id,
            'user_id': salesperson.id if salesperson else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()
        return so

    def test_different_salesperson_restriction_enabled(self):
        """When the restriction is enabled and Salesperson and SO Creator
        are different, the Salesperson must be removed from the invoice
        followers."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )
        self.assertNotEqual(so.user_id, so.create_uid)

        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertNotIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson should NOT be a follower when restriction is "
            "enabled and SO creator is a different user",
        )

    def test_same_salesperson_restriction_enabled(self):
        """When the restriction is enabled and Salesperson and SO Creator
        are the same user, standard Odoo behavior is preserved and the
        Salesperson remains a follower."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.creator_user
        )
        self.assertEqual(so.user_id, so.create_uid)

        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertIn(
            self.creator_user.partner_id,
            follower_partners,
            "Salesperson should remain a follower when they are the "
            "same user as the SO creator",
        )

    def test_different_salesperson_restriction_disabled(self):
        """When the restriction is disabled, the Salesperson should remain
        a follower even if different from the SO Creator (standard Odoo
        behavior)."""
        self._disable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )
        self.assertNotEqual(so.user_id, so.create_uid)

        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson should remain a follower when restriction is "
            "disabled, even if SO creator is a different user",
        )

    def test_restriction_disabled_by_default(self):
        """By default the restriction should be disabled, preserving
        standard Odoo follower behavior."""
        # Ensure no param is set
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=',
             'invoice_salesperson_follower_restriction.enable_restriction'),
        ]).unlink()

        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )
        self.assertNotEqual(so.user_id, so.create_uid)

        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson should remain a follower by default when no "
            "setting is configured",
        )

    def test_down_payment_invoice_salesperson_restriction(self):
        """When creating a down payment invoice (percentage or fixed amount),
        the Salesperson must also be removed from invoice followers if different
        from SO creator when restriction is enabled."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )
        self.assertNotEqual(so.user_id, so.create_uid)

        wizard = self.env['sale.advance.payment.inv'].with_user(
            self.creator_user
        ).create({
            'advance_payment_method': 'percentage',
            'amount': 10,
            'sale_order_ids': [(6, 0, [so.id])],
        })
        invoices = wizard._create_invoices(so)
        self.assertTrue(invoices, "Down payment invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertNotIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson should NOT be a follower of down payment invoice "
            "when restriction is enabled",
        )

    def test_down_payment_invoice_restriction_disabled(self):
        """When creating a down payment invoice with restriction disabled,
        the Salesperson should remain a follower."""
        self._disable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )

        wizard = self.env['sale.advance.payment.inv'].with_user(
            self.creator_user
        ).create({
            'advance_payment_method': 'percentage',
            'amount': 10,
            'sale_order_ids': [(6, 0, [so.id])],
        })
        invoices = wizard._create_invoices(so)
        self.assertTrue(invoices, "Down payment invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson should remain a follower of down payment invoice "
            "when restriction is disabled",
        )

    def test_down_payment_invoice_same_salesperson(self):
        """When creating a down payment invoice with restriction enabled and
        Salesperson is the same user as SO Creator, Salesperson should remain a follower."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.creator_user
        )

        wizard = self.env['sale.advance.payment.inv'].with_user(
            self.creator_user
        ).create({
            'advance_payment_method': 'percentage',
            'amount': 10,
            'sale_order_ids': [(6, 0, [so.id])],
        })
        invoices = wizard._create_invoices(so)
        self.assertTrue(invoices, "Down payment invoice should be created")

        follower_partners = invoices.message_follower_ids.partner_id
        self.assertIn(
            self.creator_user.partner_id,
            follower_partners,
            "Salesperson should remain a follower of down payment invoice "
            "when Salesperson is the SO Creator",
        )

    def test_no_salesperson_assigned(self):
        """When no salesperson is assigned to the sales order (user_id is False),
        invoice creation should complete successfully without error."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, False
        )
        self.assertFalse(so.user_id)

        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created without assigned salesperson")

    def test_res_config_settings_toggle(self):
        """Verify that res.config.settings properly sets the ir.config_parameter."""
        config = self.env['res.config.settings'].create({
            'enable_salesperson_follower_restriction': True,
        })
        config.execute()

        param_val = self.env['ir.config_parameter'].sudo().get_param(
            'invoice_salesperson_follower_restriction.enable_restriction'
        )
        self.assertEqual(str(param_val).lower(), 'true')

        config = self.env['res.config.settings'].create({
            'enable_salesperson_follower_restriction': False,
        })
        config.execute()

        param_val = self.env['ir.config_parameter'].sudo().get_param(
            'invoice_salesperson_follower_restriction.enable_restriction'
        )
        self.assertEqual(str(param_val).lower(), 'false')

    def test_grouped_invoices_different_salespeople(self):
        """When multiple sales orders with different assigned salespeople are grouped
        into an invoice, the respective salespeople should be removed from followers."""
        self._enable_restriction()
        so1 = self._create_sale_order(self.creator_user, self.salesperson_user)
        so2 = self._create_sale_order(self.creator_user, self.salesperson_user_2)

        invoices = (so1 | so2)._create_invoices(grouped=True)
        self.assertTrue(invoices, "Invoices should be created")

        for invoice in invoices:
            follower_partners = invoice.message_follower_ids.partner_id
            self.assertNotIn(
                self.salesperson_user.partner_id,
                follower_partners,
                "Salesperson 1 should NOT be a follower of grouped invoice",
            )
            self.assertNotIn(
                self.salesperson_user_2.partner_id,
                follower_partners,
                "Salesperson 2 should NOT be a follower of grouped invoice",
            )

    def test_multiple_orders_batch_invoicing(self):
        """When creating invoices for multiple sale orders across different customers in a batch,
        the restriction logic should apply across all created invoices."""
        self._enable_restriction()
        partner2 = self.env['res.partner'].create({'name': 'Test Customer 2'})
        so1 = self._create_sale_order(self.creator_user, self.salesperson_user)
        so2 = self.env['sale.order'].with_user(self.creator_user).create({
            'partner_id': partner2.id,
            'user_id': self.salesperson_user.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        so2.action_confirm()

        invoices = (so1 | so2)._create_invoices()
        self.assertEqual(len(invoices), 2, "Two invoices should be created for different customers")

        for invoice in invoices:
            follower_partners = invoice.message_follower_ids.partner_id
            self.assertNotIn(
                self.salesperson_user.partner_id,
                follower_partners,
                "Salesperson should NOT be a follower on any invoice in batch",
            )

    def test_salesperson_not_already_follower(self):
        """If the salesperson is not in the invoice followers list prior to restriction check,
        the unlinking should complete gracefully without error."""
        self._enable_restriction()
        so = self._create_sale_order(self.creator_user, self.salesperson_user)

        # Create invoice
        invoices = so._create_invoices()
        self.assertTrue(invoices)

        # Verify salesperson is not a follower
        follower_partners = invoices.message_follower_ids.partner_id
        self.assertNotIn(self.salesperson_user.partner_id, follower_partners)

        # Attempting to unsubscribe non-existent follower on invoice
        # should complete gracefully
        invoices.sudo().message_unsubscribe(
            partner_ids=self.salesperson_user.partner_id.ids
        )
