# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
from unittest.mock import patch
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosSessionAnalytic(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.analytic_plan = cls.env['account.analytic.plan'].create({
            'name': 'Test Analytic Plan',
        })
        
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test Analytic Account',
            'plan_id': cls.analytic_plan.id,
        })
        
        cls.pos_config_with_analytic = cls.env['pos.config'].create({
            'name': 'Config with Analytic',
            'analytic_account_id': cls.analytic_account.id,
        })
        
        cls.pos_config_without_analytic = cls.env['pos.config'].create({
            'name': 'Config without Analytic',
        })
        
        cls.session_with_analytic = cls.env['pos.session'].create({
            'config_id': cls.pos_config_with_analytic.id,
            'user_id': cls.env.uid,
        })
        
        cls.session_without_analytic = cls.env['pos.session'].create({
            'config_id': cls.pos_config_without_analytic.id,
            'user_id': cls.env.uid,
        })
        
        journal = cls.env['account.journal'].search([('type', '=', 'general')], limit=1)
        account = cls.env['account.account'].search([], limit=1)
        
        cls.mock_move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Line 1',
                    'account_id': account.id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Line 2',
                    'account_id': account.id,
                    'debit': 0.0,
                    'credit': 100.0,
                })
            ]
        })

    @patch('odoo.addons.point_of_sale.models.pos_session.PosSession._create_account_move')
    @patch('odoo.addons.point_of_sale.models.pos_session.PosSession._get_related_account_moves')
    def test_create_account_move_with_analytic_account(self, mock_get_related, mock_super_create):
        """Test _create_account_move sets analytic_distribution when config has analytic account."""
        mock_super_create.return_value = {}
        mock_get_related.return_value = self.mock_move

        for line in self.mock_move.line_ids:
            line.analytic_distribution = {}

        self.session_with_analytic._create_account_move()

        self.assertEqual(
            self.session_with_analytic.pos_analytic_account_id.id,
            self.analytic_account.id,
            "pos_analytic_account_id should be set to the config's analytic account"
        )

        expected_distribution = {str(self.analytic_account.id): 100.0}
        for line in self.mock_move.line_ids:
            self.assertEqual(
                line.analytic_distribution,
                expected_distribution,
                "Analytic distribution should be updated with the analytic account"
            )

    @patch('odoo.addons.point_of_sale.models.pos_session.PosSession._create_account_move')
    @patch('odoo.addons.point_of_sale.models.pos_session.PosSession._get_related_account_moves')
    def test_create_account_move_without_analytic_account(self, mock_get_related, mock_super_create):
        """Test _create_account_move clears analytic_distribution when config has no analytic account."""
        mock_super_create.return_value = {}
        mock_get_related.return_value = self.mock_move

        for line in self.mock_move.line_ids:
            line.analytic_distribution = {str(self.analytic_account.id): 100.0}

        self.session_without_analytic._create_account_move()

        self.assertFalse(
            self.session_without_analytic.pos_analytic_account_id,
            "pos_analytic_account_id should be False when config has no analytic account"
        )

        for line in self.mock_move.line_ids:
            self.assertFalse(
                line.analytic_distribution,
                "Analytic distribution should be empty when no analytic account is set"
            )
