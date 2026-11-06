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
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestAccountMoveMultiCancel(TransactionCase):

    def setUp(self):
        super(TestAccountMoveMultiCancel, self).setUp()
        self.move_model = self.env['account.move']
        self.wizard_model = self.env['account.move.cancel.reset']

        # Find a journal and account to create moves
        self.journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        self.account = self.env['account.account'].search([], limit=1)

        # Create some journal entries
        self.move1 = self.move_model.create({
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.account.id, 'debit': 100, 'credit': 0}),
                (0, 0, {'account_id': self.account.id, 'debit': 0, 'credit': 100}),
            ]
        })
        self.move2 = self.move_model.create({
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.account.id, 'debit': 200, 'credit': 0}),
                (0, 0, {'account_id': self.account.id, 'debit': 0, 'credit': 200}),
            ]
        })

    def test_mass_cancel_and_reset(self):
        """ Test mass cancellation and reset of journal entries """
        # Post the moves first
        self.move1.action_post()
        self.move2.action_post()
        self.assertEqual(self.move1.state, 'posted')
        self.assertEqual(self.move2.state, 'posted')

        # Cancel the moves using the wizard
        wizard_cancel = self.wizard_model.with_context(active_ids=[self.move1.id, self.move2.id]).create({})
        wizard_cancel.action_mass_journal_entry_cancel()

        self.assertEqual(self.move1.state, 'cancel')
        self.assertEqual(self.move2.state, 'cancel')

        # Reset the moves to draft using the wizard
        wizard_reset = self.wizard_model.with_context(active_ids=[self.move1.id, self.move2.id]).create({})
        wizard_reset.action_mass_journal_entry_reset()

        self.assertEqual(self.move1.state, 'draft')
        self.assertEqual(self.move2.state, 'draft')

    def test_validation_error(self):
        """ Test validation errors in the wizard """
        # Try to cancel draft moves
        self.assertEqual(self.move1.state, 'draft')
        wizard = self.wizard_model.with_context(active_ids=[self.move1.id]).create({})

        with self.assertRaises(ValidationError):
            wizard.action_mass_journal_entry_cancel()

        # Post and then try to reset posted moves
        self.move1.action_post()
        self.assertEqual(self.move1.state, 'posted')

        with self.assertRaises(ValidationError):
            wizard.action_mass_journal_entry_reset()

    def test_action_windows(self):
        """ Test the actions that open the cancel and reset wizards """
        cancel_view = self.env.ref(
            'account_move_multi_cancel.account_move_cancel_reset_view_form')
        reset_view = self.env.ref(
            'account_move_multi_cancel.account_move_cancel_reset_reset_view_form')

        cancel_action = self.move1.action_cancel_multiple_journal_entry()
        self.assertEqual(cancel_action['res_model'],
                         'account.move.cancel.reset')
        self.assertEqual(cancel_action['target'], 'new')
        self.assertEqual(cancel_action['views'], [(cancel_view.id, 'form')])

        reset_action = self.move1.action_reset_multiple_journal_entry()
        self.assertEqual(reset_action['res_model'],
                         'account.move.cancel.reset')
        self.assertEqual(reset_action['target'], 'new')
        self.assertEqual(reset_action['views'], [(reset_view.id, 'form')])
