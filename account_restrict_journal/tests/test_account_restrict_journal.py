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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccountRestrictJournal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountRestrictJournal, cls).setUpClass()

        # Get admin group
        cls.admin_group = cls.env.ref('account_restrict_journal.account_restrict_journal_group_admin')

        # Create test journals
        cls.journal_restricted = cls.env['account.journal'].create({
            'name': 'Restricted Test Journal',
            'code': 'RTJ',
            'type': 'bank',
        })
        cls.journal_allowed = cls.env['account.journal'].create({
            'name': 'Allowed Test Journal',
            'code': 'ATJ',
            'type': 'bank',
        })

        # Create restricted user
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted Test User',
            'login': 'restricted_test_user',
            'email': 'restricted_test_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.admin_group.id, cls.env.ref('account.group_account_invoice').id])],
            'journal_ids': [(4, cls.journal_restricted.id)],
        })

    def test_user_restriction_toggling(self):
        """Test toggling is_check_user and verify group assignment and journal cleanup."""
        user = self.env['res.users'].create({
            'name': 'Toggling Test User',
            'login': 'toggling_test_user',
            'email': 'toggling_test_user@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        # Initially, is_check_user is False and not in admin_group
        self.assertFalse(user.is_check_user)
        self.assertNotIn(self.admin_group, user.group_ids)

        # Toggle is_check_user to True
        user.is_check_user = True
        self.assertIn(self.admin_group, user.group_ids)

        # Assign a restricted journal
        user.journal_ids = [(4, self.journal_restricted.id)]
        self.assertEqual(user.journal_ids, self.journal_restricted)

        # Toggle is_check_user to False
        user.is_check_user = False
        self.assertNotIn(self.admin_group, user.group_ids)
        self.assertFalse(user.journal_ids, "Restricted journals should be cleared when restriction is disabled")

    def test_journal_record_rules(self):
        """Test that record rules correctly hide restricted journals from the restricted user."""
        # Query journals as the restricted user
        journals = self.env['account.journal'].with_user(self.restricted_user).search([
            ('id', 'in', [self.journal_restricted.id, self.journal_allowed.id])
        ])
        self.assertNotIn(self.journal_restricted, journals, "Restricted journal should not be visible to the user")
        self.assertIn(self.journal_allowed, journals, "Allowed journal should be visible to the user")

    def test_payment_record_rules(self):
        """Test that record rules correctly filter payments for the restricted user."""
        # Create payments as admin
        payment_allowed = self.env['account.payment'].create({
            'amount': 100.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': self.journal_allowed.id,
        })
        payment_restricted = self.env['account.payment'].create({
            'amount': 200.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': self.journal_restricted.id,
        })

        # Query payments as the restricted user
        payments = self.env['account.payment'].with_user(self.restricted_user).search([
            ('id', 'in', [payment_allowed.id, payment_restricted.id])
        ])
        self.assertNotIn(payment_restricted, payments, "Payment with restricted journal should not be visible")
        self.assertIn(payment_allowed, payments, "Payment with allowed journal should be visible")

    def test_account_move_validation(self):
        """Test account.move validations and partner onchange logic."""
        # Check is_check_journal on move with allowed journal
        move_allowed = self.env['account.move'].create({
            'journal_id': self.journal_allowed.id,
            'move_type': 'entry',
        })
        move_allowed.with_user(self.restricted_user).is_check_journal

        # Check is_check_journal raises ValidationError on move with restricted journal
        move_restricted = self.env['account.move'].create({
            'journal_id': self.journal_restricted.id,
            'move_type': 'entry',
        })
        with self.assertRaises(ValidationError, msg="Restricted journals found."):
            move_restricted.with_user(self.restricted_user).is_check_journal

        # Check onchange_partner_id sets journal_id to False if restricted
        move_onchange = self.env['account.move'].with_user(self.restricted_user).new({
            'journal_id': self.journal_restricted.id,
            'move_type': 'entry',
        })
        self.assertEqual(move_onchange.journal_id, self.journal_restricted)
        move_onchange._onchange_partner_id()
        self.assertFalse(move_onchange.journal_id, "Restricted journal should be cleared on partner onchange")

    def test_account_payment_validation(self):
        """Test creation/modification validation for payments with restricted journals."""
        from odoo.exceptions import ValidationError, AccessError

        # Create payment with allowed journal should succeed
        payment = self.env['account.payment'].with_user(self.restricted_user).create({
            'amount': 100.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': self.journal_allowed.id,
        })
        self.assertEqual(payment.journal_id, self.journal_allowed)

        # Create payment with restricted journal should raise ValidationError or AccessError
        try:
            self.env['account.payment'].with_user(self.restricted_user).create({
                'amount': 100.0,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'journal_id': self.journal_restricted.id,
            })
            self.fail("Expected ValidationError or AccessError on create")
        except (ValidationError, AccessError):
            pass

        # Write/modify payment to restricted journal should raise ValidationError or AccessError
        try:
            payment.write({'journal_id': self.journal_restricted.id})
            self.fail("Expected ValidationError or AccessError on write")
        except (ValidationError, AccessError):
            pass

    def test_payment_register_wizard_filtering(self):
        """Test that account.payment.register filters available journals correctly."""
        # Create invoice/move to register payment for
        partner = self.env['res.partner'].create({'name': 'Test Customer'})
        # Create a sale journal for the invoice
        journal_sale = self.env['account.journal'].create({
            'name': 'Test Sale Journal',
            'code': 'TSJ',
            'type': 'sale',
        })
        product = self.env['product.product'].create({'name': 'Test Product'})
        account = self.env['account.account'].search([('company_ids', 'in', self.env.company.id)], limit=1)
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'account_id': account.id,
                'quantity': 1.0,
                'price_unit': 100.0,
            })],
        })
        invoice.action_post()

        # Create the payment register wizard
        active_ids = invoice.line_ids.filtered(lambda l: l.display_type == 'payment_term').ids
        wizard = self.env['account.payment.register'].with_user(self.restricted_user).with_context(
            active_ids=active_ids,
            active_model='account.move.line',
        ).create({})

        # Check available journals
        self.assertNotIn(self.journal_restricted, wizard.available_journal_ids, "Restricted journal should not be available in wizard")
        self.assertIn(self.journal_allowed, wizard.available_journal_ids, "Allowed journal should be available in wizard")
