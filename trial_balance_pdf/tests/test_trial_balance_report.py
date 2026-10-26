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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import Command, fields
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
import logging
_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestTrialBalanceReport(AccountTestInvoicingCommon):
    """Test suite for the Trial Balance PDF Report wizard and filters."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.external_report_layout_id = cls.env.ref('web.external_layout_standard')
        cls.account_revenue = cls.company_data['default_account_revenue']
        cls.account_expense = cls.company_data['default_account_expense']
        cls.journal_misc = cls.company_data['default_journal_misc']

        cls.journal_secondary = cls.env['account.journal'].create({
            'name': 'Secondary Operations Journal',
            'code': 'SOJ',
            'type': 'general',
            'company_id': cls.company.id,
        })

        # Move 1: Posted in January 2026 on primary misc journal
        cls.move_jan = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2026-01-15'),
            'journal_id': cls.journal_misc.id,
            'line_ids': [
                Command.create({
                    'name': 'Jan Debit',
                    'account_id': cls.account_revenue.id,
                    'debit': 500.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'Jan Credit',
                    'account_id': cls.account_expense.id,
                    'debit': 0.0,
                    'credit': 500.0,
                }),
            ],
        })
        cls.move_jan.action_post()

        # Move 2: Posted in February 2026 on primary misc journal
        cls.move_feb = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2026-02-15'),
            'journal_id': cls.journal_misc.id,
            'line_ids': [
                Command.create({
                    'name': 'Feb Debit',
                    'account_id': cls.account_revenue.id,
                    'debit': 300.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'Feb Credit',
                    'account_id': cls.account_expense.id,
                    'debit': 0.0,
                    'credit': 300.0,
                }),
            ],
        })
        cls.move_feb.action_post()

        # Move 3: Posted in March 2026 on secondary journal
        cls.move_mar_secondary = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2026-03-10'),
            'journal_id': cls.journal_secondary.id,
            'line_ids': [
                Command.create({
                    'name': 'March Debit',
                    'account_id': cls.account_revenue.id,
                    'debit': 200.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'March Credit',
                    'account_id': cls.account_expense.id,
                    'debit': 0.0,
                    'credit': 200.0,
                }),
            ],
        })
        cls.move_mar_secondary.action_post()

        # Move 4: Draft in April 2026 on primary misc journal
        cls.move_draft = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2026-04-05'),
            'journal_id': cls.journal_misc.id,
            'line_ids': [
                Command.create({
                    'name': 'April Draft Debit',
                    'account_id': cls.account_revenue.id,
                    'debit': 150.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'April Draft Credit',
                    'account_id': cls.account_expense.id,
                    'debit': 0.0,
                    'credit': 150.0,
                }),
            ],
        })

    def test_01_wizard_defaults(self):
        """Test the initial field values and defaults of trial.balance.report."""
        wizard = self.env['trial.balance.report'].create({})
        self.assertEqual(wizard.state, 'posted')
        self.assertEqual(wizard.company_id, self.company)
        self.assertFalse(wizard.start_date)
        self.assertFalse(wizard.end_date)
        self.assertFalse(wizard.journals_ids)

    def test_02_trial_balance_all_posted_default(self):
        """Test default report generation containing all posted entries."""
        wizard = self.env['trial.balance.report'].create({})
        action = wizard.button_to_get_pdf()

        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'trial_balance_pdf.report_trial_balance')

        data = action.get('data', {})
        self.assertEqual(data.get('state'), 'Posted Entries only')
        self.assertEqual(data.get('company_id'), self.company.id)
        # Total debit of posted moves 1, 2, 3 = 500 + 300 + 200 = 1000.0
        self.assertAlmostEqual(data.get('total_debit'), 1000.0)
        self.assertAlmostEqual(data.get('total_credit'), 1000.0)
        self.assertAlmostEqual(data.get('balance'), 0.0)

        # Revenue account debited by 1000, Expense account credited by 1000
        account_results = {row['code']: row for row in data.get('query', [])}
        rev_row = account_results.get(self.account_revenue.code)
        exp_row = account_results.get(self.account_expense.code)
        self.assertIsNotNone(rev_row)
        self.assertIsNotNone(exp_row)
        self.assertAlmostEqual(rev_row['debit'], 1000.0)
        self.assertAlmostEqual(exp_row['credit'], 1000.0)

    def test_03_date_filtering_range(self):
        """Test filtering journal lines within a specific start and end date range."""
        wizard = self.env['trial.balance.report'].create({
            'start_date': fields.Date.from_string('2026-02-01'),
            'end_date': fields.Date.from_string('2026-02-28'),
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        self.assertEqual(data.get('start_date'), fields.Date.from_string('2026-02-01'))
        self.assertEqual(data.get('end_date'), fields.Date.from_string('2026-02-28'))
        # Only Move 2 (Feb) is in this range: debit = 300.0, credit = 300.0
        self.assertAlmostEqual(data.get('total_debit'), 300.0)
        self.assertAlmostEqual(data.get('total_credit'), 300.0)
        self.assertAlmostEqual(data.get('balance'), 0.0)

    def test_04_date_filtering_start_date_only(self):
        """Test filtering with only a start_date defined (open-ended)."""
        wizard = self.env['trial.balance.report'].create({
            'start_date': fields.Date.from_string('2026-02-01'),
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        # Excludes Jan (500.0), includes Feb (300.0) and Mar (200.0) = 500.0
        self.assertAlmostEqual(data.get('total_debit'), 500.0)
        self.assertAlmostEqual(data.get('total_credit'), 500.0)

    def test_05_date_filtering_end_date_only(self):
        """Test filtering with only an end_date defined (open-ended start)."""
        wizard = self.env['trial.balance.report'].create({
            'end_date': fields.Date.from_string('2026-02-28'),
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        # Includes Jan (500.0) and Feb (300.0) = 800.0, excludes Mar (200.0)
        self.assertAlmostEqual(data.get('total_debit'), 800.0)
        self.assertAlmostEqual(data.get('total_credit'), 800.0)

    def test_06_journal_filtering(self):
        """Test filtering entries by selecting specific journals."""
        wizard = self.env['trial.balance.report'].create({
            'journals_ids': [Command.link(self.journal_secondary.id)],
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        self.assertEqual(data.get('journals_name'), self.journal_secondary.name)
        # Only Move 3 (200.0) belongs to the secondary journal
        self.assertAlmostEqual(data.get('total_debit'), 200.0)
        self.assertAlmostEqual(data.get('total_credit'), 200.0)

    def test_07_state_filtering_draft_includes_unposted(self):
        """Test that state='draft' includes unposted draft entries."""
        wizard = self.env['trial.balance.report'].create({
            'state': 'draft',
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        self.assertEqual(data.get('state'), 'Include Unposted Entries')
        # Includes posted (1000.0) + draft (150.0) = 1150.0
        self.assertAlmostEqual(data.get('total_debit'), 1150.0)
        self.assertAlmostEqual(data.get('total_credit'), 1150.0)

    def test_08_cancelled_entries_excluded(self):
        """Test that cancelled moves are excluded even when draft state is selected."""
        move_cancelled = self.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2026-02-20'),
            'journal_id': self.journal_misc.id,
            'line_ids': [
                Command.create({
                    'name': 'Cancel Debit',
                    'account_id': self.account_revenue.id,
                    'debit': 999.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'Cancel Credit',
                    'account_id': self.account_expense.id,
                    'debit': 0.0,
                    'credit': 999.0,
                }),
            ],
        })
        move_cancelled.action_post()
        move_cancelled.button_cancel()

        wizard = self.env['trial.balance.report'].create({
            'state': 'draft',
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        # Cancelled move (999.0) must not be counted in totals
        self.assertAlmostEqual(data.get('total_debit'), 1150.0)
        self.assertAlmostEqual(data.get('total_credit'), 1150.0)

    def test_09_empty_report_for_non_matching_filter(self):
        """Test behavior when no journal entries match the filter criteria."""
        wizard = self.env['trial.balance.report'].create({
            'start_date': fields.Date.from_string('2099-01-01'),
            'end_date': fields.Date.from_string('2099-12-31'),
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})

        self.assertEqual(data.get('query'), [])
        self.assertAlmostEqual(data.get('total_debit'), 0.0)
        self.assertAlmostEqual(data.get('total_credit'), 0.0)
        self.assertAlmostEqual(data.get('balance'), 0.0)

    def test_10_qweb_report_rendering(self):

        """Test rendering the QWeb report template with data and with empty results."""
        wizard = self.env['trial.balance.report'].create({})
        action = wizard.button_to_get_pdf()
        report = self.env['ir.actions.report']._get_report_from_name(action['report_name'])

        # Render with data
        html_content = report._render_qweb_html(report.id, [wizard.id], data=action['data'])[0]
        self.assertIn(b'Trial Balance', html_content)
        self.assertIn(self.account_revenue.code.encode(), html_content)
        self.assertIn(self.account_expense.code.encode(), html_content)

        # Render without data
        empty_wizard = self.env['trial.balance.report'].create({
            'start_date': fields.Date.from_string('2099-01-01'),
            'end_date': fields.Date.from_string('2099-12-31'),
        })
        empty_action = empty_wizard.button_to_get_pdf()
        empty_html = report._render_qweb_html(report.id, [empty_wizard.id], data=empty_action['data'])[0]
        self.assertIn(b'There is no data', empty_html)

    def test_11_state_filtering_none_fallback(self):
        """Test fallback where state is False (includes all non-cancelled entries)."""
        wizard = self.env['trial.balance.report'].create({
            'state': False,
        })
        action = wizard.button_to_get_pdf()
        data = action.get('data', {})
        self.assertEqual(data.get('state'), '')
        self.assertAlmostEqual(data.get('total_debit'), 1150.0)
        self.assertAlmostEqual(data.get('total_credit'), 1150.0)

