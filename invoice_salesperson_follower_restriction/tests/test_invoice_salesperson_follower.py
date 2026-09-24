# -*- coding: utf-8 -*-
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create user for SO creator
        cls.creator_user = cls.env['res.users'].create({
            'name': 'SO Creator User',
            'login': 'so_creator_user',
            'email': 'so_creator@example.com',
            'groups_id': [(6, 0, [
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('account.group_account_invoice').id,
            ])],
        })
        # Create user for assigned Salesperson
        cls.salesperson_user = cls.env['res.users'].create({
            'name': 'Assigned Salesperson User',
            'login': 'assigned_salesperson_user',
            'email': 'assigned_salesperson@example.com',
            'groups_id': [(6, 0, [
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
            'user_id': salesperson.id,
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

    def test_customer_remains_follower_when_restriction_enabled(self):
        """When restriction is enabled, the customer partner must NOT be removed
        from the invoice followers."""
        self._enable_restriction()
        so = self._create_sale_order(
            self.creator_user, self.salesperson_user
        )
        invoices = so._create_invoices()
        self.assertTrue(invoices, "Invoice should be created")

        # Explicitly ensure customer is subscribed if standard flow didn't subscribe them
        invoices.message_subscribe(partner_ids=[self.partner.id])
        follower_partners = invoices.message_follower_ids.partner_id

        self.assertIn(
            self.partner,
            follower_partners,
            "Customer partner should remain in invoice followers",
        )
        self.assertNotIn(
            self.salesperson_user.partner_id,
            follower_partners,
            "Salesperson partner should be removed from invoice followers",
        )


