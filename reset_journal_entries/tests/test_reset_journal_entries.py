# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestResetJournalEntries(common.TransactionCase):
    """Test suite for Reset Journal Entries server actions."""

    def setUp(self):
        super().setUp()
        self.module = self.env['ir.module.module'].search([
            ('name', '=', 'reset_journal_entries'),
        ])
        company = self.env.company
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not self.journal:
            self.journal = self.env['account.journal'].search([
                ('company_id', '=', company.id),
            ], limit=1)

        accounts = self.env['account.account'].search([
            ('company_ids', 'in', company.id),
        ], limit=2)
        self.account_debit = accounts[0]
        self.account_credit = accounts[1] if len(accounts) > 1 else accounts[0]

        self.move1 = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.account_debit.id, 'debit': 100.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.account_credit.id, 'debit': 0.0, 'credit': 100.0}),
            ],
        })
        self.move2 = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.account_debit.id, 'debit': 250.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.account_credit.id, 'debit': 0.0, 'credit': 250.0}),
            ],
        })
        self.moves = self.move1 | self.move2

    def test_01_module_installation(self):
        """Verify module installation state."""
        self.assertTrue(self.module, "Module reset_journal_entries should exist.")
        self.assertEqual(
            self.module.state,
            'installed',
            "Module reset_journal_entries should be installed.",
        )

    def test_02_server_actions_configuration(self):
        """Verify the definition and model binding of the three server actions."""
        action_xml_ids = [
            'reset_journal_entries.action_reset_to_draft',
            'reset_journal_entries.action_post_journal',
            'reset_journal_entries.action_cancel_journal',
        ]
        for xml_id in action_xml_ids:
            action = self.env.ref(xml_id)
            self.assertTrue(action, f"Server action {xml_id} must exist.")
            self.assertEqual(action.state, 'code')
            self.assertEqual(
                action.binding_model_id.model,
                'account.move',
                f"Action {xml_id} must be bound to account.move",
            )

    def test_03_action_post_journal_entries(self):
        """Verify bulk posting of journal entries via action_post_journal."""
        self.assertEqual(set(self.moves.mapped('state')), {'draft'})
        act_post = self.env.ref('reset_journal_entries.action_post_journal')
        act_post.with_context(
            active_ids=self.moves.ids,
            active_model='account.move',
        ).run()
        self.assertEqual(
            set(self.moves.mapped('state')),
            {'posted'},
            "All moves should be posted after running action_post_journal.",
        )

    def test_04_action_reset_to_draft_entries(self):
        """Verify bulk resetting of posted journal entries back to draft."""
        self.moves.action_post()
        self.assertEqual(set(self.moves.mapped('state')), {'posted'})

        act_reset = self.env.ref('reset_journal_entries.action_reset_to_draft')
        act_reset.with_context(
            active_ids=self.moves.ids,
            active_model='account.move',
        ).run()
        self.assertEqual(
            set(self.moves.mapped('state')),
            {'draft'},
            "All moves should be reset to draft after running action_reset_to_draft.",
        )

    def test_05_action_cancel_journal_entries(self):
        """Verify bulk cancellation of journal entries via action_cancel_journal."""
        self.assertEqual(set(self.moves.mapped('state')), {'draft'})
        act_cancel = self.env.ref('reset_journal_entries.action_cancel_journal')
        act_cancel.with_context(
            active_ids=self.moves.ids,
            active_model='account.move',
        ).run()
        self.assertEqual(
            set(self.moves.mapped('state')),
            {'cancel'},
            "All moves should be canceled after running action_cancel_journal.",
        )

    def test_06_static_resources_exist(self):
        """Verify all declared static and data resources exist on disk."""
        mod_path = get_module_path('reset_journal_entries')
        self.assertTrue(mod_path, "Module path for reset_journal_entries must exist.")
        required_files = [
            'data/ir_action_server_data.xml',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/index.html',
        ]
        for rel_path in required_files:
            full_path = os.path.join(mod_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required file {rel_path} was not found on disk at {full_path}.",
            )
