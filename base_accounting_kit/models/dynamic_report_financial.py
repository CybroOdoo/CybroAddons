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
from odoo import _, models


class DynamicFinancialReport(models.AbstractModel):
    """Profit and Loss, Balance Sheet and the other root reports of the
    configurable ``account.financial.report`` tree. Figures from
    ``report_financial.get_account_lines`` (P1.3); comparison periods by
    calling it once per period."""
    _name = 'account.dynamic.report.financial'
    _inherit = 'account.dynamic.report'
    _description = 'Financial Report'

    _filters = ('date', 'comparison', 'target_move', 'journals')
    _comparison = True
    _columns_by = True
    # Abstract model holding the kit computation.
    _computation = 'report.base_accounting_kit.report_financial'

    def _root_reports(self):
        cash_flow = self.env.ref(
            'base_accounting_kit.account_financial_report_cash_flow0',
            raise_if_not_found=False)
        return self.env['account.financial.report'].search(
            [('parent_id', '=', False)]) - cash_flow

    def _option_defs(self):
        roots = self._root_reports()
        return [
            {'key': 'account_report_id', 'label': _("Report"),
             'type': 'select', 'default': roots[:1].id,
             'values': [(r.id, r.name) for r in roots]},
            {'key': 'debit_credit', 'label': _("Display Debit/Credit Columns"),
             'type': 'bool', 'default': False},
        ]

    def _company_env(self, options):
        return super()._company_env(options).with_context(
            financial_report_id=options['account_report_id'])

    def _report_title(self):
        report = self.env['account.financial.report'].browse(
            self.env.context.get('financial_report_id')).exists()
        return report.name or self._description

    def _report_context(self, options, date_from=None, date_to=None):
        # As the financial report wizard: no strict range, so balance sheet
        # accounts cumulate up to the end date.
        ctx = super()._report_context(options, date_from, date_to)
        ctx['strict_range'] = False
        return ctx

    # ------------------------------------------------------------------
    def _structure(self, options, date_from=None, date_to=None):
        """Kit lines of one period: report lines in order, and the account
        lines of each report: ``(reports, {report_id: [account lines]})``."""
        data = {
            'account_report_id': [options['account_report_id']],
            'used_context': self._report_context(options, date_from,
                                                 date_to),
            'enable_filter': False,
            'debit_credit': options['debit_credit'],
        }
        reports, accounts, report_id = [], {}, None
        for line in self.env[self._computation].get_account_lines(data):
            if line['type'] == 'report':
                report_id = line['r_id']
                reports.append(line)
            else:
                accounts.setdefault(report_id, []).append(line)
        return reports, accounts

    def _periods(self, options):
        """Current structure and the balances of the earlier periods."""
        current = self._structure(options)
        previous = []
        for date_from, date_to, _label in self._kit_extra_periods(options):
            reports, accounts = self._structure(options, date_from, date_to)
            balances = {('report', r['r_id']): r['balance'] for r in reports}
            for report_id, lines in accounts.items():
                balances.update({('account', report_id, a['account']):
                                 a['balance'] for a in lines})
            previous.append(balances)
        return current, previous

    def _kit_heading(self, options, company):
        # A balance sheet is stated at a date: "As of <end date>".
        heading = super()._kit_heading(options, company)
        balance_sheet = self.env.ref(
            'base_accounting_kit.account_financial_report_balancesheet0',
            raise_if_not_found=False)
        if balance_sheet and options['account_report_id'] == balance_sheet.id \
                and options['date_from']:
            heading = super()._kit_heading(dict(options, date_from=False), company)
        return heading

    def _kit_extra_periods(self, options):
        """The periods computed besides the report period: the columns by
        period (RI 3.2), else the comparison periods."""
        return self._kit_period_columns(self.env.company, options) or \
            self._comparison_periods(self.env.company, options)

    def _show_debit_credit(self, options):
        return options['debit_credit'] and not options['comparison']['periods'] \
            and not options['columns_by']

    def _columns(self, options):
        if options['columns_by']:
            # one column per period, then the whole period (for the balance
            # sheet: the balance at its end, the same as the last period)
            return self._kit_period_column_defs(
                self._kit_period_columns(self.env.company, options)) + [
                {'name': _("Total"), 'type': 'monetary'}]
        columns = []
        if self._show_debit_credit(options):
            columns += [{'name': _("Debit"), 'type': 'monetary'},
                        {'name': _("Credit"), 'type': 'monetary'}]
        columns.append({'name': _("Balance"), 'type': 'monetary'})
        periods = self._comparison_periods(self.env.company, options)
        columns += [{'name': label, 'type': 'monetary'}
                    for _from, _to, label in periods]
        if periods:
            columns.append({'name': _("Variance"), 'type': 'monetary'})
        return columns

    def _line_columns(self, options, line, key, previous):
        if options['columns_by']:
            return [p.get(key, 0.0) for p in previous] + [line['balance']]
        columns = []
        if self._show_debit_credit(options):
            columns += [line.get('debit', 0.0), line.get('credit', 0.0)]
        columns.append(line['balance'])
        if previous:
            values = [p.get(key, 0.0) for p in previous]
            columns += values + [line['balance'] - values[0]]
        return columns

    def _tree_levels(self, reports):
        """Depth of the report lines in the tree, the root being 0 (the
        computation's own ``level`` follows the style setting)."""
        records = self.env['account.financial.report'].browse(
            [r['r_id'] for r in reports])
        base = min(records.mapped('level') or [0])
        return {r.id: r.level - base for r in records}

    def _levels(self, reports):
        """Indentation: the depth under the root report (the root itself
        is the last line, level 0)."""
        return {key: max(level - 1, 0)
                for key, level in self._tree_levels(reports).items()}

    def _total_label(self, report):
        """Name of the last line, the result of the root report."""
        labels = {
            'base_accounting_kit.account_financial_report_profitandloss0':
                _("Net Profit"),
            'base_accounting_kit.account_financial_report_cash_flow0':
                _("Net Cash Flow"),
        }
        for xmlid, label in labels.items():
            record = self.env.ref(xmlid, raise_if_not_found=False)
            if record and record.id == report['r_id']:
                return label
        return _("Total %s", report['name'])

    def _lines(self, options):
        """Report lines as a statement reads: a line adding up other lines
        shows its name above them and its total below them; the root report
        is the last line."""
        (reports, accounts), previous = self._periods(options)
        levels = self._levels(reports)
        depth = {r['r_id']: i for i, r in enumerate(reports)}
        tree_level = self._tree_levels(reports)
        lines, open_sums = [], []

        def total(report, root=False):
            # The root has no heading: its total keeps the report line id.
            return {
                'id': ('report_%s' if root else 'total_%s') % report['r_id'],
                'name': self._total_label(report) if root
                else _("Total %s", report['name']),
                'level': levels.get(report['r_id'], 0),
                'columns': self._line_columns(
                    options, report, ('report', report['r_id']), previous),
                'class': 'total' if root else 'section',
            }
        for index, report in enumerate(reports):
            while open_sums and tree_level[open_sums[-1]['r_id']] >= \
                    tree_level[report['r_id']]:
                closing = open_sums.pop()
                lines.append(total(closing, depth[closing['r_id']] == 0))
            has_children = index + 1 < len(reports) and \
                tree_level[reports[index + 1]['r_id']] > \
                tree_level[report['r_id']]
            if has_children:
                open_sums.append(report)
                if index:
                    # A line with its own accounts (e.g. a cash flow
                    # section) unfolds them under its heading.
                    lines.append({
                        'id': 'report_%s' % report['r_id'],
                        'name': report['name'],
                        'level': levels.get(report['r_id'], 0),
                        'columns': [''] * len(self._columns(options)),
                        'unfoldable': bool(accounts.get(report['r_id'])),
                        # main sections (Income, Expenses...) highlighted
                        'class': 'main' if not levels.get(report['r_id'])
                        else 'section',
                    })
            else:
                lines.append({
                    'id': 'report_%s' % report['r_id'],
                    'name': report['name'],
                    'level': levels.get(report['r_id'], 0),
                    'columns': self._line_columns(
                        options, report, ('report', report['r_id']),
                        previous),
                    'unfoldable': bool(accounts.get(report['r_id'])),
                })
        while open_sums:
            closing = open_sums.pop()
            lines.append(total(closing, depth[closing['r_id']] == 0))
        # "Financial Report Style" of a report line sets its font (its
        # heading and its total for a line adding up others).
        styles = {r.id: r.style_overwrite for r in self.env[
            'account.financial.report'].browse(list(depth))
            if r.style_overwrite not in (False, '0')}
        for line in lines:
            style = styles.get(int(line['id'].split('_')[1]))
            if style:
                line['style'] = style
        return lines

    def _child_lines(self, options, line_id):
        if not line_id.startswith('report_'):
            return []
        report_id = int(line_id.split('_')[1])
        (reports, accounts), previous = self._periods(options)
        level = self._levels(reports).get(report_id, 0) + 1
        return [{
            'id': 'account_%s_%s' % (report_id, line['account']),
            'name': line['name'],
            'level': level,
            'parent_id': line_id,
            'columns': self._line_columns(
                options, line, ('account', report_id, line['account']),
                previous),
        } for line in accounts.get(report_id, [])]

    def _line_action(self, options, line_id):
        """An account opens the General Ledger of that account, unfolded,
        for the same period, journals and posted / all entries."""
        if not line_id.startswith('account_'):
            return False
        account = self.env['account.account'].browse(
            int(line_id.split('_')[2])).exists()
        if not account:
            return False
        return self._kit_ledger_action(
            options, account, self._ledger_initial_balance(account))

    def _ledger_initial_balance(self, account):
        """Opening balance in the General Ledger: balance sheet accounts
        (their figure is the balance at the end date), not profit and loss
        accounts (their figure is the period's)."""
        return account.include_initial_balance


class DynamicCashFlow(models.AbstractModel):
    """Cash Flow Statement: the Cash Flow tree, figures from
    ``report_cash_flow.get_account_lines`` (P1.4)."""
    _name = 'account.dynamic.report.cash_flow'
    _inherit = 'account.dynamic.report.financial'
    _description = 'Cash Flow Statement'

    _computation = 'report.base_accounting_kit.report_cash_flow'
    _columns_by = False

    def _option_defs(self):
        return [{'key': 'debit_credit',
                 'label': _("Display Debit/Credit Columns"),
                 'type': 'bool', 'default': False}]

    def _normalize_report_options(self, options):
        res = super()._normalize_report_options(options)
        res['account_report_id'] = self.env.ref(
            'base_accounting_kit.account_financial_report_cash_flow0').id
        return res

    def _report_title(self):
        return _("Cash Flow Statement")

    def _report_context(self, options, date_from=None, date_to=None):
        # As the cash flow wizard: the period only (strict range).
        return super(DynamicFinancialReport, self)._report_context(
            options, date_from, date_to)

    def _ledger_initial_balance(self, account):
        # Cash flows are the period's movements only.
        return False
