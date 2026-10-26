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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountRestrictJournal(TransactionCase):
    """Test the journal restriction of the users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref('account_restrict_journal.account_restrict_journal_group_admin')
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
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted Test User',
            'login': 'restricted_test_user',
            'email': 'restricted_test_user@example.com',
            'group_ids': [Command.set([
                cls.env.ref('base.group_user').id,
                cls.group.id,
                cls.env.ref('account.group_account_manager').id,
            ])],
            'journal_ids': [Command.link(cls.journal_restricted.id)],
        })

    def _payment_vals(self, journal, amount=100.0):
        """Return the values of an inbound customer payment."""
        return {
            'amount': amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': journal.id,
        }

    def test_user_restriction_toggling(self):
        """Toggle is_check_user and verify the group and the journal cleanup."""
        user = self.env['res.users'].create({
            'name': 'Toggling Test User',
            'login': 'toggling_test_user',
            'email': 'toggling_test_user@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        self.assertFalse(user.is_check_user)
        self.assertNotIn(self.group, user.group_ids)

        user.is_check_user = True
        self.assertIn(self.group, user.group_ids)

        user.journal_ids = [Command.link(self.journal_restricted.id)]
        self.assertEqual(user.journal_ids, self.journal_restricted)

        user.is_check_user = False
        self.assertNotIn(self.group, user.group_ids)
        self.assertFalse(user.journal_ids, "Restricted journals should be cleared when the restriction is disabled")

    def test_group_removal_clears_journals(self):
        """Removing the group directly also clears the restricted journals."""
        self.assertIn(self.journal_restricted, self.restricted_user.journal_ids)
        self.restricted_user.group_ids = [Command.unlink(self.group.id)]
        self.assertFalse(self.restricted_user.is_check_user)
        self.assertFalse(self.restricted_user.journal_ids)

    def test_journal_record_rules(self):
        """Restricted journals stay readable but cannot be modified."""
        journals = self.env['account.journal'].with_user(self.restricted_user).search([
            ('id', 'in', [self.journal_restricted.id, self.journal_allowed.id]),
        ])
        self.assertIn(self.journal_restricted, journals, "Restricted journal should stay readable")
        self.assertIn(self.journal_allowed, journals, "Allowed journal should be visible to the user")

        self.journal_allowed.with_user(self.restricted_user).write({'name': 'Renamed Allowed Journal'})
        self.assertEqual(self.journal_allowed.name, 'Renamed Allowed Journal')
        with self.assertRaises(AccessError):
            self.journal_restricted.with_user(self.restricted_user).write({'name': 'Renamed Restricted Journal'})

    def test_payment_record_rules(self):
        """Payments of restricted journals stay readable but cannot be modified."""
        payment_allowed = self.env['account.payment'].create(self._payment_vals(self.journal_allowed))
        payment_restricted = self.env['account.payment'].create(self._payment_vals(self.journal_restricted, 200.0))

        payments = self.env['account.payment'].with_user(self.restricted_user).search([
            ('id', 'in', [payment_allowed.id, payment_restricted.id]),
        ])
        self.assertIn(payment_allowed, payments)
        self.assertIn(payment_restricted, payments)

        with self.assertRaises(AccessError):
            payment_restricted.with_user(self.restricted_user).write({'amount': 300.0})

    def test_account_move_validation(self):
        """Validate the restricted journal check and the partner onchange."""
        move_allowed = self.env['account.move'].create({
            'journal_id': self.journal_allowed.id,
            'move_type': 'entry',
        })
        self.assertTrue(move_allowed.with_user(self.restricted_user).is_check_journal)

        move_restricted = self.env['account.move'].create({
            'journal_id': self.journal_restricted.id,
            'move_type': 'entry',
        })
        with self.assertRaises(ValidationError):
            move_restricted.with_user(self.restricted_user)._compute_is_check_journal()

        move_onchange = self.env['account.move'].with_user(self.restricted_user).new({
            'journal_id': self.journal_restricted.id,
            'move_type': 'entry',
        })
        self.assertEqual(move_onchange.journal_id, self.journal_restricted)
        move_onchange._onchange_partner_id()
        self.assertFalse(move_onchange.journal_id, "Restricted journal should be cleared on partner onchange")

    def test_account_payment_validation(self):
        """Reject payments created or moved into a restricted journal."""
        payment = self.env['account.payment'].with_user(self.restricted_user).create(
            self._payment_vals(self.journal_allowed))
        self.assertEqual(payment.journal_id, self.journal_allowed)

        with self.assertRaises((ValidationError, AccessError)):
            self.env['account.payment'].with_user(self.restricted_user).create(
                self._payment_vals(self.journal_restricted))

        with self.assertRaises((ValidationError, AccessError)):
            payment.write({'journal_id': self.journal_restricted.id})

    def test_payment_create_accepts_single_dict(self):
        """The create method accepts a single dictionary of values."""
        payment = self.env['account.payment'].create(self._payment_vals(self.journal_allowed))
        self.assertEqual(payment.journal_id, self.journal_allowed)

    def test_payment_register_wizard_filtering(self):
        """The register payment wizard hides the restricted journals."""
        partner = self.env['res.partner'].create({'name': 'Test Customer'})
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
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'account_id': account.id,
                'quantity': 1.0,
                'price_unit': 100.0,
            })],
        })
        invoice.action_post()

        active_ids = invoice.line_ids.filtered(lambda line: line.display_type == 'payment_term').ids
        wizard = self.env['account.payment.register'].with_user(self.restricted_user).with_context(
            active_ids=active_ids,
            active_model='account.move.line',
        ).create({})

        self.assertNotIn(self.journal_restricted, wizard.available_journal_ids)
        self.assertIn(self.journal_allowed, wizard.available_journal_ids)
