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
from datetime import timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestLedgers(AccountingKitTestCommon):
    """Trial Balance, General Ledger, Partner Ledger and Aged Receivable /
    Payable (P1.6, SP.1, SP.2): opening balances per fiscal year, Result
    Brought Forward, filters, comparison, unfold and drill-down."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rec = cls.kit_account('asset_receivable')
        cls.pay = cls.kit_account('liability_payable')
        cls.inc = cls.kit_account('income')
        cls.exp = cls.kit_account('expense')
        cls.cye = cls.kit_account('equity_unaffected')
        cls.bank = cls.kit_journal('bank').default_account_id
        cls.customer = cls.env['res.partner'].create({'name': 'Kit Customer'})
        cls.vendor = cls.env['res.partner'].create({'name': 'Kit Vendor'})
        cls.kit_entry(cls.ymd(6, 1, 1), [(cls.rec, 1000, 0, cls.customer), (cls.inc, 0, 1000, cls.customer)])
        cls.kit_entry(cls.ymd(7, 1, 1), [(cls.exp, 300, 0, cls.vendor), (cls.pay, 0, 300, cls.vendor)])
        cls.kit_entry(cls.ymd(2, 1), [(cls.rec, 500, 0, cls.customer), (cls.inc, 0, 500, cls.customer)])
        cls.kit_entry(cls.ymd(3, 1), [(cls.bank, 400, 0, cls.customer), (cls.rec, 0, 400, cls.customer)])
        cls.base = {'date_preset': 'custom', 'date_from': str(cls.ymd(3, 1)),
                    'date_to': str(cls.ymd(12, 31))}

    @staticmethod
    def line(report, prefix, rec_id):
        return next((line for line in report['lines'] if line['id'] == '%s_%s' % (prefix, rec_id)), None)

    # ------------------------------------------------------------------ TB
    def test_trial_balance_figures(self):
        """Trial Balance: initial / debit / credit / end per account, the
        total row and the Result Brought Forward of earlier years."""
        report = self.dyn('trial_balance').get_report(dict(self.base, display_account='all'))
        self.assertEqual(self.line(report, 'account', self.rec.id)['columns'], [1500, 0, 400, 1100])
        bank = self.line(report, 'account', self.bank.id)['columns']
        self.assertAmount(bank[1], 400)
        self.assertAmount(bank[3], 400)
        total = report['lines'][-1]
        self.assertEqual(total['class'], 'total')
        self.assertEqual([round(x, 2) for x in total['columns']], [0, 400, 400, 0])
        self.assertTrue(any(line['name'].startswith(self.cye.code) and abs(line['columns'][0] + 700) < 0.005
                            for line in report['lines']))
        movements = self.dyn('trial_balance').get_report(self.base)
        self.assertEqual({line['id'] for line in movements['lines']},
                         {'account_%s' % self.rec.id, 'account_%s' % self.bank.id, 'total'})

    def test_options_rebuilt_on_server(self):
        """Options sent by the browser are checked: unknown company, preset,
        journals, target moves and comparison fall back to safe values."""
        other = self.setup_other_company(name='Kit other company')['company']
        journal = self.kit_journal('bank', other)
        options = self.dyn('trial_balance').get_report({
            'company_id': other.id, 'date_preset': 'hack', 'journal_ids': [journal.id, 'x'],
            'target_move': 'drop table', 'comparison': {'periods': 99, 'type': 'evil'},
            'display_account': 'x'})['options']
        self.assertEqual(options['company_id'], self.company.id)
        self.assertEqual(options['date_preset'], 'this_year')
        self.assertEqual(options['journal_ids'], [])
        self.assertEqual(options['target_move'], 'posted')
        self.assertEqual(options['display_account'], 'movement')
        self.assertEqual(options['comparison'], {'periods': 12, 'type': 'previous'})
        with self.assertRaises(UserError):
            self.dyn('trial_balance').get_report(dict(self.base, date_from=str(self.ymd(12, 31)),
                                                      date_to=str(self.ymd(1, 1))))

    def test_trial_balance_comparison(self):
        """Comparison: previous period of the same length, same period last
        year, previous fiscal years; variance = current - previous."""
        report = self.dyn('trial_balance').get_report(dict(self.base, comparison={'periods': 1}))
        start, end = self.ymd(3, 1), self.ymd(12, 31)
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - (end - start)
        self.assertEqual([col['name'] for col in report['columns']][4:], [
            'Balance', '%s - %s' % (prev_start, prev_end), 'Variance'])
        self.assertEqual(self.line(report, 'account', self.rec.id)['columns'][4:], [-400, 1500, -1900])
        last_year = self.dyn('trial_balance').get_report(dict(self.base, comparison={'periods': 1, 'type': 'last_year'}))
        self.assertEqual(self.line(last_year, 'account', self.rec.id)['columns'][5], 1000)
        fiscal = self.dyn('trial_balance').get_report({'date_preset': 'this_year', 'comparison': {'periods': 2}})
        y1, y2 = self.year - 1, self.year - 2
        self.assertEqual([col['name'] for col in fiscal['columns']][5:7],
                         ['%s-01-01 - %s-12-31' % (y1, y1), '%s-01-01 - %s-12-31' % (y2, y2)])

    def test_trial_balance_by_period(self):
        """Trial Balance by month (RI 3.2): Initial Balance, then the balance
        at the end of each month (with all accounts listed, each column
        totals 0); journal items show
        their running balance under their month; an amount opens the General
        Ledger up to that month's end with the same ending balance."""
        # every account with a balance listed (not only those that moved),
        # so each column is a complete trial balance
        options = {'date_preset': 'custom', 'date_from': str(self.ymd(1, 1)), 'date_to': str(self.ymd(3, 31)),
                   'columns_by': 'month', 'display_account': 'not_zero'}
        report = self.dyn('trial_balance').get_report(options)
        names = [c['name'] for c in report['columns']]
        self.assertEqual((names[0], len(names)), ('Initial Balance', 4))
        self.assertEqual(report['columns'][2]['date_from'], str(self.ymd(1, 1)))
        self.assertEqual(report['columns'][2]['date_to'], str(self.ymd(2, 28)) if self.year % 4 else str(self.ymd(2, 29)))
        rec = self.by_id(report)['account_%s' % self.rec.id]['columns']
        self.assertAmount(rec[1], rec[0])            # January: no movement
        self.assertAmount(rec[2], rec[0] + 500)      # end of February
        self.assertAmount(rec[3], rec[0] + 100)      # end of March
        total = self.by_id(report)['total']['columns']
        for value in total[1:]:
            self.assertAmount(value, 0)
        children = self.dyn('trial_balance').get_lines(options, 'account_%s' % self.rec.id)
        february = [c for c in children if c['columns'][2] != '']
        self.assertTrue(february)
        self.assertAmount(february[-1]['columns'][2], rec[2])
        column = report['columns'][2]
        action = self.dyn('trial_balance').with_context(kit_period_cell=True).action_open_line(
            dict(options, date_from=column['date_from'], date_to=column['date_to'], columns_by=''),
            'account_%s' % self.rec.id)
        gl = self.dyn('general_ledger').get_report(action['params']['options'])
        self.assertAmount(self.by_id(gl)['account_%s' % self.rec.id]['columns'][2], rec[2])
        self.assertEqual(self.dyn('trial_balance').action_open_line(options, 'account_%s' % self.rec.id)['res_model'],
                         'account.move.line')

    def test_unfold_search_drill_down(self):
        """Unfold shows the opening line and journal items with a running
        balance; search keeps matching lines; drill-down opens journal
        items, then the journal entry."""
        report = self.dyn('trial_balance')
        children = report.get_lines(self.base, 'account_%s' % self.rec.id)
        self.assertTrue(children[0]['id'].startswith('init_'))
        self.assertAmount(children[0]['columns'][3], 1500)
        self.assertAmount(children[-1]['columns'][3], 1100)
        unfolded = report.get_report(dict(self.base, unfolded=['account_%s' % self.rec.id]))
        index = [line['id'] for line in unfolded['lines']].index('account_%s' % self.rec.id)
        self.assertEqual(unfolded['lines'][index + 1].get('parent_id'), 'account_%s' % self.rec.id)
        searched = report.get_report(dict(self.base, search=self.bank.name[:6]))
        self.assertEqual({line['id'] for line in searched['lines']}, {'account_%s' % self.bank.id, 'total'})
        action = report.action_open_line(self.base, 'account_%s' % self.rec.id)
        self.assertEqual(action['res_model'], 'account.move.line')
        self.assertIn(('account_id', '=', self.rec.id), [tuple(d) for d in action['domain']])
        item = children[-1]['id']
        action = report.action_open_line(self.base, item)
        self.assertEqual(action['res_id'], self.env['account.move.line'].browse(int(item.split('_')[1])).move_id.id)

    def test_exports_ignore_forged_figures(self):
        """PDF and XLSX are rebuilt from the options; figures sent in the
        request are ignored; XLSX amounts are numbers."""
        html = self.pdf_html('trial_balance', dict(self.base, unfolded=['account_%s' % self.rec.id]))
        self.assertIn('1,100.00', html)
        self.assertIn('Initial Balance', html)
        sheet = self.xlsx_sheet('trial_balance', dict(self.base, lines=[{'name': 'FAKE', 'columns': [999999]}]))
        rows = [[cell.value for cell in row] for row in sheet.iter_rows()]
        rec_row = next(row for row in rows if row[0] and str(row[0]).startswith(self.rec.code))
        self.assertEqual(rec_row[4], 1100)
        self.assertNotIn('FAKE', self.sheet_values(sheet))

    def test_access(self):
        """A user without accounting rights is refused; an accountant can
        open the report."""
        nobody = self.env['res.users'].create({
            'name': 'No accounting', 'login': 'kit_noacc', 'company_id': self.company.id,
            'company_ids': [(6, 0, self.company.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.dyn('trial_balance').with_user(nobody).get_report(self.base)
        accountant = self.env['res.users'].create({
            'name': 'Accountant', 'login': 'kit_acc', 'company_id': self.company.id,
            'company_ids': [(6, 0, self.company.ids)],
            'group_ids': [(6, 0, [self.env.ref('account.group_account_user').id])]})
        report = self.dyn('trial_balance').with_user(accountant).get_report(self.base)
        self.assertEqual(len(report['lines']), 3)

    # ------------------------------------------------------------------ GL
    def test_general_ledger(self):
        """General Ledger: opening balance included, P&L accounts from the
        fiscal year start, Result Brought Forward, comparison, partner and
        analytic filters, forged ids dropped."""
        report = self.dyn('general_ledger')
        result = report.get_report(dict(self.base, display_account='all'))
        self.assertEqual([col['name'] for col in result['columns']], ['Debit', 'Credit', 'Balance'])
        self.assertEqual(self.line(result, 'account', self.rec.id)['columns'], [0, 400, 1100])
        self.assertAmount(self.line(result, 'account', self.inc.id)['columns'][2], -500)
        self.assertTrue(any(line['name'].startswith(self.cye.code) and abs(line['columns'][2] + 700) < 0.005
                            for line in result['lines']))
        no_initial = report.get_report(dict(self.base, display_account='all', initial_balance=False))
        self.assertEqual(self.line(no_initial, 'account', self.rec.id)['columns'][2], -400)
        compared = report.get_report(dict(self.base, comparison={'periods': 1, 'type': 'last_year'}))
        self.assertEqual(self.line(compared, 'account', self.rec.id)['columns'][3], 1000)
        vendor = report.get_report(dict(self.base, date_from=str(self.ymd(1, 1, 1)), partner_ids=[self.vendor.id]))
        self.assertEqual({line['name'].split(' ')[0] for line in vendor['lines'] if line['id'] != 'total'},
                         {self.pay.code, self.exp.code})
        plan = self.env['account.analytic.plan'].create({'name': 'Kit plan'})
        analytic = self.env['account.analytic.account'].create({'name': 'Kit Dept', 'plan_id': plan.id})
        move = self.kit_entry(self.ymd(5, 5), [(self.exp, 70, 0), (self.bank, 0, 70)])
        move.line_ids.filtered(lambda l: l.account_id == self.exp).analytic_distribution = {str(analytic.id): 100}
        filtered = report.get_report(dict(self.base, analytic_ids=[analytic.id]))
        self.assertEqual([line['name'].split(' ')[0] for line in filtered['lines'] if line['id'] != 'total'], [self.exp.code])
        forged = report.get_report(dict(self.base, partner_ids=[99999999, 'x'], analytic_ids=[99999999]))['options']
        self.assertEqual((forged['partner_ids'], forged['analytic_ids']), ([], []))
        action = report.action_open_line(dict(self.base, partner_ids=[self.customer.id]), 'account_%s' % self.rec.id)
        self.assertIn(('partner_id', 'in', [self.customer.id]), [tuple(d) for d in action['domain']])

    # ------------------------------------------------------------------ PL
    def test_partner_ledger(self):
        """Partner Ledger: opening balance, totals, unfold, partner filter,
        currency column."""
        report = self.dyn('partner_ledger')
        result = report.get_report(self.base)
        self.assertEqual(self.line(result, 'partner', self.customer.id)['columns'], [1500, 0, 400, 1100])
        both = report.get_report(dict(self.base, result_selection='customer_supplier'))
        self.assertEqual(self.line(both, 'partner', self.vendor.id)['columns'], [-300, 0, 0, -300])
        self.assertEqual([round(x, 2) for x in both['lines'][-1]['columns']], [1200, 0, 400, 800])
        children = report.get_lines(self.base, 'partner_%s' % self.customer.id)
        self.assertTrue(children[0]['id'].startswith('init_'))
        self.assertAmount(children[-1]['columns'][3], 1100)
        only_vendor = report.get_report(dict(self.base, result_selection='customer_supplier', partner_ids=[self.vendor.id]))
        self.assertEqual([line['id'] for line in only_vendor['lines']], ['partner_%s' % self.vendor.id, 'total'])
        currency = report.get_report(dict(self.base, amount_currency=True))
        self.assertEqual(currency['columns'][-1]['name'], 'Amount Currency')

    def test_drill_down_account_name(self):
        """Partner Ledger and Day Book drill-down lines show the account
        name in the user's language, not the stored translation JSON."""
        self.env['res.lang']._activate_lang('fr_FR')
        self.rec.update_field_translations('name', {'fr_FR': 'Clients Kit FR'})
        day = 'day_%s' % self.ymd(3, 1)
        for lang, expected in (('en_US', self.rec.with_context(lang='en_US').name),
                               ('fr_FR', 'Clients Kit FR')):
            env = self.env(context=dict(self.env.context, lang=lang))
            partner = self.dyn('partner_ledger').with_env(env).get_lines(
                self.base, 'partner_%s' % self.customer.id)
            days = self.dyn('day_book').with_env(env).get_lines(self.base, day)
            for lines in (partner[1:], days):
                labels = [line['name'] for line in lines]
                self.assertTrue(labels)
                self.assertTrue(any(expected in label for label in labels), labels)
                self.assertFalse(any('{' in label or 'en_US' in label for label in labels), labels)

    # ------------------------------------------------------------------ Aged
    def test_aged(self):
        """Aged Receivable / Payable: single date, buckets by age, unfold
        into open items, period length."""
        report = self.dyn('aged')
        options = {'date_preset': 'custom', 'date_to': str(self.ymd(12, 31))}
        receivable = report.get_report(dict(options, account_type='receivable'))
        self.assertEqual(receivable['title'], 'Aged Receivable')
        self.assertEqual(receivable['date_mode'], 'single')
        self.assertEqual([col['name'] for col in receivable['columns']],
                         ['Not Due', '1-30', '31-60', '61-90', '91-120', '+120', 'Total'])
        self.assertAmount(self.line(receivable, 'partner', self.customer.id)['columns'][6], 1100)
        items = report.get_lines(options, 'partner_%s' % self.customer.id)
        self.assertEqual(len(items), 3)
        self.assertAmount(sum(item['columns'][6] for item in items), 1100)
        payable = report.get_report(dict(options, account_type='payable'))
        self.assertEqual(payable['title'], 'Aged Payable')
        self.assertAmount(self.line(payable, 'partner', self.vendor.id)['columns'][6], -300)
        fifteen = report.get_report(dict(options, period_length=15))
        self.assertEqual([col['name'] for col in fifteen['columns']][1:6], ['1-15', '16-30', '31-45', '46-60', '+60'])
        self.assertEqual(report.get_report({})['options']['date_preset'], 'today')
        self.assertEqual(report._export_filename({}),
                         'Aged Receivable as of %s' % self.today)
