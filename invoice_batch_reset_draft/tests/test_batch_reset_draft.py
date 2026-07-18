# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestBatchResetDraft(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['invoice.batch.reset.draft.wizard']

    def _invoice(self, move_type='out_invoice', post=True, price=100.0):
        """Create (and optionally post) a simple invoice/bill/refund."""
        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.product_a.id,
                'quantity': 1.0,
                'price_unit': price,
            })],
        })
        if post:
            move.action_post()
        return move

    def _wizard(self, moves, operation='draft', reason=False):
        return self.Wizard.with_context(
            active_model='account.move', active_ids=moves.ids
        ).create({'operation': operation, 'reason': reason})

    def test_bulk_reset_to_draft(self):
        """Posted invoice + vendor bill are both reset to draft in one go."""
        moves = self._invoice() + self._invoice(move_type='in_invoice')
        self.assertEqual(set(moves.mapped('state')), {'posted'})
        wiz = self._wizard(moves, 'draft')
        self.assertEqual(wiz.eligible_count, 2)
        self.assertEqual(wiz.skipped_count, 0)
        wiz.action_confirm()
        self.assertEqual(set(moves.mapped('state')), {'draft'})

    def test_cancelled_reset_to_draft(self):
        """A cancelled invoice can also be reset to draft."""
        inv = self._invoice()
        inv.button_cancel()
        self.assertEqual(inv.state, 'cancel')
        wiz = self._wizard(inv, 'draft')
        self.assertEqual(wiz.eligible_count, 1)
        wiz.action_confirm()
        self.assertEqual(inv.state, 'draft')

    def test_non_posted_is_skipped(self):
        """A draft record in the selection is skipped; the posted one resets,
        and the batch does not fail as a whole."""
        posted = self._invoice()
        draft = self._invoice(post=False)
        wiz = self._wizard(posted + draft, 'draft')
        self.assertEqual(wiz.eligible_count, 1)
        self.assertEqual(wiz.skipped_count, 1)
        wiz.action_confirm()
        self.assertEqual(posted.state, 'draft')
        self.assertEqual(draft.state, 'draft')  # unchanged

    def test_reason_logged_in_chatter(self):
        """The reason is written to each affected invoice's chatter."""
        inv = self._invoice()
        self._wizard(inv, 'draft', reason='Year-end correction').action_confirm()
        self.assertEqual(inv.state, 'draft')
        logged = inv.message_ids.filtered(
            lambda m: m.body and 'Year-end correction' in m.body)
        self.assertTrue(logged, "the reason should be logged in the chatter")

    def test_bulk_cancel(self):
        """Bulk cancel sets posted invoices to cancelled."""
        moves = self._invoice() + self._invoice()
        wiz = self._wizard(moves, 'cancel')
        self.assertEqual(wiz.eligible_count, 2)
        wiz.action_confirm()
        self.assertEqual(set(moves.mapped('state')), {'cancel'})

    def test_non_invoice_moves_filtered_out(self):
        """Misc journal entries are ignored (not invoices/bills/refunds)."""
        entry = self.env['account.move'].create({
            'move_type': 'entry',
            'line_ids': [
                Command.create({
                    'account_id': self.company_data['default_account_revenue'].id,
                    'debit': 0.0, 'credit': 100.0}),
                Command.create({
                    'account_id': self.company_data['default_account_expense'].id,
                    'debit': 100.0, 'credit': 0.0}),
            ],
        })
        wiz = self._wizard(entry, 'draft')
        self.assertFalse(wiz.move_ids)
        self.assertEqual(wiz.eligible_count, 0)

    def test_requires_account_manager(self):
        """A non-manager accounting user cannot use the wizard (ACL)."""
        billing_user = self.env['res.users'].create({
            'name': 'Billing Only',
            'login': 'ibrd_billing',
            'email': 'ibrd_billing@example.com',
            'group_ids': [Command.set(
                [self.env.ref('account.group_account_user').id])],
        })
        inv = self._invoice()
        with self.assertRaises(AccessError):
            self.Wizard.with_user(billing_user).with_context(
                active_model='account.move', active_ids=inv.ids
            ).create({'operation': 'draft'})
