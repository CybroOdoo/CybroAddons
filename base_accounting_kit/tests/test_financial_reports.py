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
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestFinancialReports(AccountingKitTestCommon):
    """Profit and Loss, Balance Sheet and Cash Flow Statement (P1.3, P1.4,
    SP.3): figures and signs, statement layout, comparison, drill-down,
    configurable structure, exports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank = cls.kit_journal('bank').default_account_id
        acc = {t: cls.kit_account(t) for t in (
            'equity', 'income', 'expense_direct_cost', 'asset_current',
            'income_other', 'expense', 'liability_payable',
            'expense_depreciation', 'asset_fixed', 'asset_receivable')}
        cls.acc = acc
        day = cls.ymd(1, 15)
        cls.kit_entry(day, [(cls.bank, 10000, 0), (acc['equity'], 0, 10000)])
        cls.kit_entry(day, [(acc['asset_receivable'], 1000, 0), (acc['income'], 0, 1000)])
        cls.kit_entry(day, [(acc['expense_direct_cost'], 400, 0), (acc['asset_current'], 0, 400)])
        cls.kit_entry(day, [(cls.bank, 50, 0), (acc['income_other'], 0, 50)])
        cls.kit_entry(day, [(acc['expense'], 200, 0), (acc['liability_payable'], 0, 200)])
        cls.kit_entry(day, [(acc['expense_depreciation'], 100, 0), (acc['asset_fixed'], 0, 100)])
        cls.pl = cls.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        cls.bs = cls.env.ref('base_accounting_kit.account_financial_report_balancesheet0')

    def ref(self, xmlid):
        return self.env.ref('base_accounting_kit.' + xmlid)

    def figures(self, report, column=0):
        """Figure of each report line: on its "Total" line when it adds up
        other lines, else on its own line."""
        res = {}
        for line in report['lines']:
            kind, _sep, rid = line['id'].partition('_')
            if kind == 'total' or (kind == 'report' and line.get('class') != 'section'):
                res[int(rid)] = line['columns'][column]
        return res

    def financial(self, report, **options):
        return self.dyn('financial').get_report(dict(account_report_id=report.id, **options))

    # ------------------------------------------------------------------
    def test_profit_and_loss_figures(self):
        """P&L lines carry the P1.3 figures and signs (net profit 350)."""
        figures = self.figures(self.financial(self.pl))
        expected = {
            'account_financial_report_profitandloss0': 350,
            'account_financial_report_income0': 650,
            'financial_report_gross_profit': 600,
            'account_financial_report_operating_income0': 1000,
            'financial_report_cost_of_revenue': -400,
            'account_financial_report_other_income0': 50,
            'account_financial_report_expense0': 300,
            'account_financial_report_expense_operating0': 200,
            'account_financial_report_expense_depreciation0': 100,
            'account_financial_report_expense_other0': 0,
        }
        for xmlid, amount in expected.items():
            self.assertAmount(figures[self.ref(xmlid).id], amount, xmlid)

    def test_balance_sheet_figures(self):
        """Balance Sheet: assets = liabilities + equity, current year
        earnings in equity, root 0."""
        expected = {
            'account_financial_report_balancesheet0': 0,
            'account_financial_report_assets0': 10550,
            'account_financial_report_liabilitysum0': 200,
            'account_financial_report_equitysum0': 10350,
            'account_financial_report_equity0': 10000,
            'account_financial_report_profitloss_toreport0': 350,
        }
        for options in ({}, {'date_preset': 'custom', 'date_from': str(self.today),
                             'date_to': str(self.today)}):
            figures = self.figures(self.financial(self.bs, **options))
            for xmlid, amount in expected.items():
                self.assertAmount(figures[self.ref(xmlid).id], amount, (xmlid, options))

    def test_profit_and_loss_empty_period(self):
        """A period after the last entry gives a P&L of zeros."""
        next_year = self.year + 1
        report = self.financial(self.pl, date_preset='custom',
                                date_from='%s-01-01' % next_year,
                                date_to='%s-12-31' % next_year)
        self.assertTrue(all(abs(v or 0) < 0.005 for v in self.figures(report).values()))

    def test_wrong_dates_rejected(self):
        """A start date after the end date is refused."""
        with self.assertRaises(UserError):
            self.financial(self.bs, date_preset='custom', date_from='%s-05-01' % self.year,
                           date_to='%s-01-01' % self.year)

    def test_statement_layout(self):
        """Statements read top-down: heading, lines, "Total <name>" below,
        result last; grey only on main sections and the result."""
        lines = self.financial(self.pl)['lines']
        self.assertEqual([(line['name'], line.get('class', '')) for line in lines], [
            ('Income', 'main'), ('Gross Profit', 'section'), ('Operating Income', ''),
            ('Cost of Revenue', ''), ('Total Gross Profit', 'section'), ('Other Income', ''),
            ('Total Income', 'section'), ('Expenses', 'main'), ('Expenses', ''),
            ('Depreciation', ''), ('Other Expenses', ''), ('Total Expenses', 'section'),
            ('Net Profit', 'total')])
        heading = lines[0]
        self.assertEqual(heading['columns'], [''])
        self.assertFalse(heading.get('unfoldable'))
        bs_lines = [(line['name'], line.get('class', ''))
                    for line in self.financial(self.bs)['lines']]
        self.assertEqual(bs_lines[0], ('Assets', 'main'))
        self.assertGreater(bs_lines.index(('Total Assets', 'section')), bs_lines.index(('Receivable', '')))
        self.assertEqual(bs_lines[-1], ('Total Balance Sheet', 'total'))
        _data, table = self.dyn('financial')._export_table({'account_report_id': self.pl.id})
        self.assertEqual([row['cells'][0] for row in table['rows'] if row['highlight']],
                         ['Income', 'Expenses', 'Net Profit'])

    def test_comparison(self):
        """Comparison with earlier periods: one column per period and the
        variance (current - previous)."""
        self.kit_entry(self.ymd(6, 1, years_back=1), [(self.bank, 400, 0), (self.acc['income'], 0, 400)])
        report = self.financial(self.pl, comparison={'periods': 2})
        y1, y2 = self.year - 1, self.year - 2
        self.assertEqual([col['name'] for col in report['columns']], [
            'Balance', '%s-01-01 - %s-12-31' % (y1, y1), '%s-01-01 - %s-12-31' % (y2, y2), 'Variance'])
        net = self.by_id(report)['report_%s' % self.pl.id]
        self.assertEqual(net['name'], 'Net Profit')
        for value, expected in zip(net['columns'], (350, 400, 0, -50)):
            self.assertAmount(value, expected)

    def test_debit_credit_columns(self):
        """Debit/Credit columns on request, hidden while comparing."""
        report = self.financial(self.pl, debit_credit=True)
        self.assertEqual([col['name'] for col in report['columns']], ['Debit', 'Credit', 'Balance'])
        report = self.financial(self.pl, debit_credit=True, comparison={'periods': 1})
        self.assertNotIn('Debit', [col['name'] for col in report['columns']])

    def test_unfold_and_drill_down(self):
        """A line unfolds into its accounts; an account opens the General
        Ledger of that account only, unfolded, for the same period: its
        balance is the P&L figure (period, no opening balance) or the
        Balance Sheet figure (with the opening balance)."""
        report = self.dyn('financial')
        options = {'account_report_id': self.pl.id}
        line_id = 'report_%s' % self.ref('account_financial_report_operating_income0').id
        children = report.get_lines(options, line_id)
        self.assertEqual(len(children), 1)
        self.assertTrue(children[0]['name'].startswith(self.acc['income'].code))
        self.assertAmount(children[0]['columns'][0], 1000)

        def ledger(opts, line):
            action = report.action_open_line(opts, line)
            self.assertEqual(action['tag'], 'kit_dynamic_report')
            self.assertEqual(action['params']['model'], 'account.dynamic.report.general_ledger')
            return action['params']['options'], self.dyn('general_ledger').get_report(action['params']['options'])

        gl_options, gl = ledger(options, children[0]['id'])
        self.assertFalse(gl_options['initial_balance'])
        accounts = [line for line in gl['lines'] if line['id'].startswith('account_')]
        self.assertEqual([line['id'] for line in accounts], ['account_%s' % self.acc['income'].id])
        self.assertTrue(accounts[0].get('unfolded'))
        self.assertTrue([line for line in gl['lines'] if line.get('parent_id') == accounts[0]['id']])
        self.assertAmount(accounts[0]['columns'][2], -1000)  # credit balance, shown +1000 in the P&L
        self.assertEqual(gl['options']['account_ids'], [self.acc['income'].id])

        bs_options = {'account_report_id': self.bs.id}
        bank_lines = report.get_lines(bs_options, 'report_%s' % self.ref('account_financial_report_bank_cash0').id)
        bank_line = next(line for line in bank_lines if line['id'].endswith('_%s' % self.bank.id))
        gl_options, gl = ledger(bs_options, bank_line['id'])
        self.assertTrue(gl_options['initial_balance'])
        bank_gl = next(line for line in gl['lines'] if line['id'] == 'account_%s' % self.bank.id)
        self.assertAmount(bank_gl['columns'][2], bank_line['columns'][0])
        self.assertFalse(report.action_open_line(options, line_id))

    def test_columns_by_period(self):
        """Columns by period (RI 3.2): the year by quarter / month with a
        Total; P&L columns add up to the Total; Balance Sheet columns are
        the balances at each period end; no comparison meanwhile; more than
        24 periods refused; a period amount opens the General Ledger of that
        period only."""
        year = {'date_preset': 'custom', 'date_from': '%s-01-01' % self.year,
                'date_to': '%s-12-31' % self.year}
        self.kit_entry(self.ymd(5, 10), [(self.acc['asset_receivable'], 250, 0), (self.acc['income'], 0, 250)])
        report = self.financial(self.pl, columns_by='quarter', comparison={'periods': 2}, **year)
        self.assertEqual(report['options']['comparison']['periods'], 0)
        self.assertEqual(len(report['columns']), 5)
        self.assertEqual(report['columns'][1]['date_from'], '%s-04-01' % self.year)
        self.assertEqual(report['columns'][-1]['name'], 'Total')
        net = self.by_id(report)['report_%s' % self.pl.id]['columns']
        self.assertAmount(net[0], 350)  # Q1 (January entries)
        self.assertAmount(net[1], 250)  # Q2 (May entry)
        self.assertAmount(net[4], sum(net[:4]))
        self.assertEqual(len(self.financial(self.pl, columns_by='month', **year)['columns']), 13)
        bank = self.ref('account_financial_report_bank_cash0')
        bs = self.financial(self.bs, columns_by='quarter', **year)
        bank_line = next(line for line in bs['lines'] if line['id'] == 'report_%s' % bank.id)
        self.assertAmount(bank_line['columns'][0], 10050)
        self.assertAmount(bank_line['columns'][3], bank_line['columns'][4])
        with self.assertRaises(UserError):
            self.financial(self.pl, columns_by='month', date_preset='custom',
                           date_from='%s-01-01' % (self.year - 2), date_to='%s-12-31' % self.year)
        self.assertFalse(self.dyn('cash_flow').get_report({'columns_by': 'month'})['options']['columns_by'])
        report = self.dyn('financial')
        options = dict(year, account_report_id=self.pl.id, columns_by='quarter')
        income_line = report.get_lines(options, 'report_%s' % self.ref('account_financial_report_operating_income0').id)[0]
        self.assertEqual(len(income_line['columns']), 5)
        column = report.get_report(options)['columns'][1]
        action = report.action_open_line(dict(options, date_preset='custom', date_from=column['date_from'],
                                              date_to=column['date_to'], columns_by=''), income_line['id'])
        gl = self.dyn('general_ledger').get_report(action['params']['options'])
        account = next(line for line in gl['lines'] if line['id'].startswith('account_'))
        self.assertAmount(account['columns'][2], -250)

    def test_configurable_structure(self):
        """Configuration > Financial Reports: a new root report is offered
        and computes; a line added to the P&L shows on the screen."""
        custom = self.env['account.financial.report'].create({
            'name': 'Kit Income KPI', 'type': 'account_type', 'account_type_ids': 'income',
            'sign': '-1', 'display_detail': 'detail_flat'})
        values = [v[0] for v in self.dyn('financial').get_report({})['option_defs'][0]['values']]
        self.assertIn(custom.id, values)
        self.assertNotIn(self.ref('account_financial_report_cash_flow0').id, values)
        report = self.financial(custom)
        self.assertEqual(report['title'], 'Kit Income KPI')
        self.assertAmount(report['lines'][0]['columns'][0], 1000)
        extra = self.env['account.financial.report'].create({
            'name': 'Kit added line', 'parent_id': self.pl.id, 'type': 'account_type',
            'account_type_ids': 'equity', 'sign': '-1', 'sequence': 99})
        self.assertAmount(self.by_id(self.financial(self.pl))['report_%s' % extra.id]['columns'][0], 10000)

    def test_line_style(self):
        """The "Financial Report Style" of a line sets its font on the
        screen data, in the PDF and in the XLSX."""
        income = self.ref('account_financial_report_income0')
        other = self.ref('account_financial_report_other_income0')
        income.style_overwrite, other.style_overwrite = '4', '5'
        lines = self.by_id(self.financial(self.pl))
        self.assertEqual(lines['report_%s' % income.id].get('style'), '4')
        self.assertEqual(lines['total_%s' % income.id].get('style'), '4')
        _data, table = self.dyn('financial')._export_table({'account_report_id': self.pl.id})
        income_row = next(row for row in table['rows'] if row['cells'][0] == 'Income')
        self.assertFalse(income_row['bold'])
        self.assertTrue(income_row['highlight'])
        self.assertIn('font-style: italic', self.pdf_html('financial', {'account_report_id': self.pl.id}))
        sheet = self.xlsx_sheet('financial', {'account_report_id': self.pl.id})
        cell = next(row[0] for row in sheet.iter_rows() if row[0].value == 'Other Income')
        self.assertTrue(cell.font.i)

    def test_cash_flow(self):
        """Cash Flow Statement: its own tree (a forged report is ignored),
        tagged accounts listed, debit/credit and comparison columns."""
        self.ref('account_financial_report_operation0').account_ids = [(4, self.bank.id)]
        report = self.dyn('cash_flow')
        cash_flow = report.get_report({'debit_credit': True, 'unfold_all': True})
        self.assertEqual(cash_flow['title'], 'Cash Flow Statement')
        self.assertEqual([col['name'] for col in cash_flow['columns']], ['Debit', 'Credit', 'Balance'])
        self.assertTrue(any(line['name'].startswith(self.bank.code) for line in cash_flow['lines']))
        self.assertEqual(cash_flow['lines'][-1]['name'], 'Net Cash Flow')
        forged = report.get_report({'account_report_id': self.pl.id})['options']['account_report_id']
        self.assertEqual(forged, self.ref('account_financial_report_cash_flow0').id)
        compared = report.get_report({'comparison': {'periods': 1}})
        self.assertEqual(compared['columns'][-1]['name'], 'Variance')

    def test_exports_match_screen(self):
        """PDF and XLSX are recomputed on the server and carry the figures
        of the screen; their file name is the title and the period."""
        options = {'account_report_id': self.pl.id}
        self.assertIn('350.00', self.pdf_html('financial', options))
        self.assertIn(350, self.sheet_values(self.xlsx_sheet('financial', options)))
        name = self.dyn('financial')._export_filename(options)
        self.assertEqual(name, 'Profit and Loss %s-01-01 - %s-12-31' % (self.year, self.year))
