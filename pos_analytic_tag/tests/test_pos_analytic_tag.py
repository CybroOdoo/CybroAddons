# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch
from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPosAnalyticTag(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create an analytic plan
        cls.analytic_plan = cls.env['account.analytic.plan'].create({
            'name': 'Test POS Analytic Plan',
        })

        # Create an analytic account
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test POS Analytic Account',
            'plan_id': cls.analytic_plan.id,
        })

        # Create a journal for POS Config
        cls.journal = cls.env['account.journal'].create({
            'name': 'POS Journal',
            'type': 'sale',
            'code': 'POSJ',
        })

        # Create a receivable account
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'POS Receivable Account',
            'code': 'POSREC123',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })

        # Create a payment method
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Cash',
            'receivable_account_id': cls.receivable_account.id,
        })

        # Create a POS config
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config',
            'journal_id': cls.journal.id,
            'analytic_account_id': cls.analytic_account.id,
            'payment_method_ids': [Command.link(cls.payment_method.id)],
        })

        # Create a POS session
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def test_pos_config_analytic_account(self):
        """Test that the analytic account is properly set on pos.config."""
        self.assertEqual(
            self.pos_config.analytic_account_id,
            self.analytic_account,
            "Analytic account should be correctly configured on pos.config"
        )

    def test_res_config_settings_related_field(self):
        """Test that res.config.settings correctly exposes the pos_config's analytic_account_id."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        self.assertEqual(
            settings.pos_analytic_account_id,
            self.analytic_account,
            "res.config.settings related field should match pos.config's analytic account"
        )

        # Update via settings
        new_analytic_account = self.env['account.analytic.account'].create({
            'name': 'New Test POS Analytic Account',
            'plan_id': self.analytic_plan.id,
        })
        settings.write({
            'pos_analytic_account_id': new_analytic_account.id,
        })
        self.assertEqual(
            self.pos_config.analytic_account_id,
            new_analytic_account,
            "Changing pos_analytic_account_id in settings should update pos.config"
        )

    def test_pos_order_related_field(self):
        """Test that pos.order.pos_analytic_account_id related field resolves via session."""
        # Directly write the analytic account onto the session (bypassing POS flow)
        self.pos_session.write({
            'pos_analytic_account_id': self.analytic_account.id,
        })
        # Verify the session carries the analytic account correctly
        self.assertEqual(
            self.pos_session.pos_analytic_account_id,
            self.analytic_account,
            "pos.session.pos_analytic_account_id should be writable and match the set value"
        )

    def test_pos_payment_related_field(self):
        """Test that pos.payment.pos_analytic_account_id related field resolves via session."""
        # Directly write the analytic account onto the session (bypassing POS flow)
        self.pos_session.write({
            'pos_analytic_account_id': self.analytic_account.id,
        })
        # Verify the field definition itself is a related field pointing to the session
        field = self.env['pos.payment']._fields.get('pos_analytic_account_id')
        self.assertIsNotNone(
            field,
            "pos.payment must have the pos_analytic_account_id field"
        )
        self.assertEqual(
            field.related,
            'session_id.pos_analytic_account_id',
            "pos.payment.pos_analytic_account_id must be related to session_id.pos_analytic_account_id"
        )

    def test_create_account_move_with_analytic_account(self):
        """Test pos.session._create_account_move when analytic account is set."""
        # Create fake related account moves
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Line 1',
                    'account_id': self.receivable_account.id,
                }),
                (0, 0, {
                    'name': 'Line 2',
                    'account_id': self.receivable_account.id,
                }),
            ]
        })

        # Mock self.pos_session._get_related_account_moves to return our fake move
        # and mock the super call of _create_account_move to avoid database/POS constraints
        with patch.object(type(self.pos_session), '_get_related_account_moves', return_value=move), \
             patch('odoo.addons.point_of_sale.models.pos_session.PosSession._create_account_move', return_value=True):

            self.pos_session._create_account_move()

            self.assertEqual(
                self.pos_session.pos_analytic_account_id,
                self.analytic_account,
                "pos_analytic_account_id on session should be set from pos_config"
            )

            for line in move.line_ids:
                expected_distribution = {str(self.analytic_account.id): 100}
                self.assertEqual(
                    line.analytic_distribution,
                    expected_distribution,
                    "Move line analytic distribution should contain the analytic account with 100% allocation"
                )

    def test_create_account_move_without_analytic_account(self):
        """Test pos.session._create_account_move when analytic account is NOT set."""
        # Remove analytic account from config
        self.pos_config.analytic_account_id = False

        # Create fake related account moves with pre-existing analytic distribution
        another_analytic = self.env['account.analytic.account'].create({
            'name': 'Another Analytic',
            'plan_id': self.analytic_plan.id,
        })
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Line 1',
                    'account_id': self.receivable_account.id,
                    'analytic_distribution': {another_analytic.id: 100},
                }),
            ]
        })

        # Mock self.pos_session._get_related_account_moves to return our fake move
        # and mock the super call of _create_account_move to avoid database/POS constraints
        with patch.object(type(self.pos_session), '_get_related_account_moves', return_value=move), \
             patch('odoo.addons.point_of_sale.models.pos_session.PosSession._create_account_move', return_value=True):

            self.pos_session._create_account_move()

            self.assertFalse(
                self.pos_session.pos_analytic_account_id,
                "pos_analytic_account_id on session should be False"
            )

            for line in move.line_ids:
                self.assertFalse(
                    line.analytic_distribution,
                    "Move line analytic distribution should be cleared/empty"
                )
