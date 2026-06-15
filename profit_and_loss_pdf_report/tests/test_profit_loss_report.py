# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestProfitLossReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProfitLossReport, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.company
        cls.company.external_report_layout_id = cls.env.ref('web.external_layout_standard')

        # Create accounts
        cls.account_income = cls.env['account.account'].create({
            'code': 'INC01',
            'name': 'Operating Income',
            'account_type': 'income',
            'company_ids': [Command.set(cls.company.ids)],
        })
        cls.account_expense = cls.env['account.account'].create({
            'code': 'EXP01',
            'name': 'Expense',
            'account_type': 'expense',
            'company_ids': [Command.set(cls.company.ids)],
        })

        cls.test_date = date.today() + timedelta(days=3650)
        # Create move
        cls.move = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': cls.test_date,
            'line_ids': [
                (0, 0, {
                    'account_id': cls.account_income.id,
                    'name': 'Income',
                    'credit': 1000.0,
                    'debit': 0.0,
                }),
                (0, 0, {
                    'account_id': cls.account_expense.id,
                    'name': 'Expense',
                    'credit': 0.0,
                    'debit': 500.0,
                }),
                (0, 0, {
                    'account_id': cls.account_income.id,
                    'name': 'Balancing Line',
                    'credit': 0.0,
                    'debit': 500.0,
                })
            ]
        })
        cls.move.action_post()

    def test_check_start_date_validation(self):
        """Test validation error when start_date > end_date"""
        with self.assertRaises(ValidationError):
            self.env['profit.loss.report'].create({
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=1),
            })

    def test_action_button_to_print_pdf(self):
        """Test the report action to print pdf"""
        wizard = self.env['profit.loss.report'].create({
            'start_date': self.test_date - timedelta(days=5),
            'end_date': self.test_date + timedelta(days=5),
        })

        action = wizard.action_button_to_print_pdf()
        self.assertTrue(action)
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'], 'profit_and_loss_pdf_report.pl_report_temp')

        # Check data inside action
        data = action.get('data', {})
        self.assertEqual(data.get('net_profit'), 500.0)
        self.assertEqual(data.get('total_op_income'), 1000.0)
        self.assertEqual(data.get('total_expense'), 500.0)

    def test_action_button_to_print_pdf_no_dates(self):
        """Test report action when no dates are provided"""
        wizard = self.env['profit.loss.report'].create({})

        action = wizard.action_button_to_print_pdf()
        self.assertTrue(action)
        self.assertEqual(action['type'], 'ir.actions.report')

        data = action.get('data', {})
        self.assertIn('net_profit', data)
        self.assertIn('total_op_income', data)
