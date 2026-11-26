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
"""Day Book, Cash Book, Bank Book, Tax Report and Journals Audit: dynamic
reports on the kit computations of ``report/``."""
from odoo import _, fields, models

from .report_company import get_report_branches, get_report_journal_domain


def _label(*values):
    return ' - '.join(str(v) for v in values if v)


class DynamicDayBook(models.AbstractModel):
    """Day Book: one line per day, from ``day_book._get_day_entries``."""
    _name = 'account.dynamic.report.day_book'
    _inherit = 'account.dynamic.report'
    _description = 'Day Book'

    _filters = ('date', 'target_move', 'journals', 'accounts')

    def _report_title(self):
        return _("Day Book")

    def _columns(self, options):
        return [{'name': _("Debit"), 'type': 'monetary'},
                {'name': _("Credit"), 'type': 'monetary'},
                {'name': _("Balance"), 'type': 'monetary'}]

    def _days(self, options, day=None):
        accounts = self.env['account.account'].browse(options['account_ids']) \
            or self.env['account.account'].search(
                self.env['account.account']._check_company_domain(
                    self.env.company))
        ctx = self._report_context(options, day, day) if day \
            else self._report_context(options)
        return self.env['report.base_accounting_kit.day_book_report_template']\
            .with_context(**ctx)._get_day_entries(accounts)

    def _lines(self, options):
        lines, totals = [], [0.0, 0.0, 0.0]
        for day in self._days(options):
            columns = [day['debit'], day['credit'], day['balance']]
            totals = [t + c for t, c in zip(totals, columns)]
            lines.append({'id': 'day_%s' % day['date'],
                          'name': fields.Date.to_string(day['date']),
                          'level': 0, 'columns': columns, 'unfoldable': True})
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'class': 'total', 'columns': totals})
        return lines

    def _child_lines(self, options, line_id):
        if not line_id.startswith('day_'):
            return []
        day = fields.Date.to_date(line_id[4:])
        return [{
            'id': 'aml_%s' % item['lid'],
            'name': _label(item['lcode'], item['move_name'], item['accname'],
                           item['partner_name'], item['lname']),
            'level': 1, 'parent_id': line_id,
            'columns': [item['debit'], item['credit'], item['balance']],
        } for days in [self._days(options, day)] for d in days
            for item in d['child_lines']]


class DynamicCashBook(models.AbstractModel):
    """Cash Book: the company's cash accounts (or the selected ones), from
    ``report_cash_book._get_account_move_entry``."""
    _name = 'account.dynamic.report.cash_book'
    _inherit = 'account.dynamic.report'
    _description = 'Cash Book'

    _filters = ('date', 'target_move', 'journals', 'accounts')
    _computation = 'report.base_accounting_kit.report_cash_book'

    def _report_title(self):
        return _("Cash Book")

    def _account_domain(self):
        return [('account_type', '=', 'asset_cash')]

    def _option_defs(self):
        return [
            {'key': 'initial_balance', 'label': _("Include Initial Balances"),
             'type': 'bool', 'default': True},
            {'key': 'sortby', 'label': _("Sort by"), 'type': 'select',
             'default': 'sort_date',
             'values': {'sort_date': _("Date"),
                        'sort_journal_partner': _("Journal & Partner")}},
            {'key': 'display_account', 'label': _("Display Accounts"),
             'type': 'select', 'default': 'movement',
             'values': {'movement': _("With movements"),
                        'all': _("All accounts"),
                        'not_zero': _("With balance not equal to 0")}},
        ]

    def _columns(self, options):
        return [{'name': _("Debit"), 'type': 'monetary'},
                {'name': _("Credit"), 'type': 'monetary'},
                {'name': _("Balance"), 'type': 'monetary'}]

    def _entries(self, options, accounts=None):
        book = self.env[self._computation].with_context(
            **self._report_context(options))
        if accounts is None:
            accounts = self.env['account.account'].browse(
                options['account_ids']) or book._get_journal_accounts()
        if not accounts:
            return []
        return book._get_account_move_entry(
            accounts, options['initial_balance'], options['sortby'],
            options['display_account'])

    def _lines(self, options):
        lines, totals = [], [0.0, 0.0, 0.0]
        for row in self._entries(options):
            totals = [totals[0] + row['debit'], totals[1] + row['credit'],
                      totals[2] + row['balance']]
            lines.append({'id': 'account_%s' % row['id'],
                          'name': _label(row['code'], row['name']),
                          'level': 0, 'unfoldable': True,
                          'columns': [row['debit'], row['credit'],
                                      row['balance']]})
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'class': 'total',
                      'columns': totals})
        return lines

    def _missing_accounts_notice(self):
        return _("No cash journal for %s: choose the accounts in the Accounts "
                 "filter.", self.env.company.name)

    def _report_notice(self, options):
        """Without selected accounts and without journal accounts, the
        report is empty and says why."""
        if options['account_ids'] or self.env[self._computation].with_context(
                **self._report_context(options))._get_journal_accounts():
            return False
        return self._missing_accounts_notice()

    def _child_lines(self, options, line_id):
        if not line_id.startswith('account_'):
            return []
        account = self.env['account.account'].browse(
            int(line_id.split('_')[1])).exists()
        rows = self._entries(dict(options, display_account='all'), account) \
            if account else []
        return [{
            'id': 'aml_%s' % item['lid'] if item.get('lid')
            else 'init_%s' % account.id,
            'name': _label(item.get('ldate'), item.get('lcode'),
                           item.get('move_name'), item.get('partner_name'),
                           item.get('lname')) or _("Initial Balance"),
            'level': 1, 'parent_id': line_id,
            'columns': [item['debit'], item['credit'], item['balance']],
        } for row in rows for item in row['move_lines']]


class DynamicBankBook(models.AbstractModel):
    """Bank Book: as the Cash Book, on the bank journals' accounts."""
    _name = 'account.dynamic.report.bank_book'
    _inherit = 'account.dynamic.report.cash_book'
    _description = 'Bank Book'

    _computation = 'report.base_accounting_kit.report_bank_book'

    def _report_title(self):
        return _("Bank Book")

    def _missing_accounts_notice(self):
        return _("No bank journal for %s: choose the accounts in the Accounts "
                 "filter.", self.env.company.name)


class DynamicTaxReport(models.AbstractModel):
    """Tax Report: Sales and Purchases (and Withholding) sections from
    ``report_tax.get_lines`` (P1.5 signs and totals, taxes based on payment
    counted when paid); comparison of the tax amounts."""
    _name = 'account.dynamic.report.tax'
    _inherit = 'account.dynamic.report'
    _description = 'Tax Report'

    _filters = ('date', 'comparison', 'target_move', 'journals')
    _comparison = True

    def _report_title(self):
        return _("Tax Report")

    def _columns(self, options):
        periods = self._comparison_periods(self.env.company, options)
        columns = [{'name': _("Net"), 'type': 'monetary'},
                   {'name': _("Tax"), 'type': 'monetary'}]
        columns += [{'name': label, 'type': 'monetary'}
                    for _from, _to, label in periods]
        if periods:
            columns.append({'name': _("Variance"), 'type': 'monetary'})
        return columns

    def _groups(self, options, date_from=None, date_to=None):
        return self.env['report.base_accounting_kit.report_tax'].get_lines(
            {'used_context': self._report_context(options, date_from,
                                                  date_to)})

    def _lines(self, options):
        groups = self._groups(options)
        previous = [self._groups(options, date_from, date_to)
                    for date_from, date_to, _label in self._comparison_periods(
                        self.env.company, options)]

        def columns(net, tax, key):
            values = [net, tax]
            if previous:
                prev = [p['totals'][key[1]]['tax'] if key[0] == 'section'
                        else next((t['tax'] for t in p[key[2]]
                                   if t['key'] == key[1]), 0.0)
                        for p in previous]
                values += prev + [tax - prev[0]]
            return values
        lines = []
        sections = {'sale': _("Sales"), 'purchase': _("Purchases")}
        if groups['has_withholding']:
            sections['withholding'] = _("Withholding")
        for section, label in sections.items():
            total = groups['totals'][section]
            lines.append({'id': 'section_%s' % section, 'name': label,
                          'level': 0, 'class': 'total',
                          'columns': columns(total['net'], total['tax'],
                                             ('section', section))})
            for tax in groups[section]:
                # a child of a group of taxes: tax_<child>_<group>
                line_id = 'tax_%s_%s' % (tax['id'], tax['group_id']) \
                    if tax.get('group_id') else 'tax_%s' % tax['id']
                lines.append({'id': line_id, 'name': tax['name'],
                              'level': tax['level'],
                              'columns': columns(tax['net'], tax['tax'],
                                                 ('tax', tax['key'], section))})
        return lines

    def _line_action(self, options, line_id):
        if not line_id.startswith('tax_'):
            return False
        parts = line_id.split('_')
        tax = self.env['account.tax'].browse(int(parts[1]))
        if len(parts) > 2:
            # child of a group: the group's base lines and the child's tax lines
            base, tax_lines = [int(parts[2])], tax.ids
        elif tax.amount_type == 'group':
            base, tax_lines = tax.ids, tax.children_tax_ids.ids
        else:
            base, tax_lines = tax.ids, tax.ids
        domain = [
            '|', ('tax_ids', 'in', base), ('tax_line_id', 'in', tax_lines),
            # as the figures: taxes based on payment when paid (P2.4-a)
            *self.env['account.move.line']._get_tax_exigible_domain(),
            ('date', '>=', fields.Date.to_string(options['date_from'])),
            ('date', '<=', fields.Date.to_string(options['date_to'])),
            ('company_id', 'in', get_report_branches(self.env.company).ids),
            ('parent_state', 'in', self._states(options)),
        ] + self._kit_filter_domain(options, ('journal_ids',))
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_account_moves_all')
        action.update({'domain': domain,
                       'context': {'search_default_posted': 0}})
        return action


class DynamicJournalAudit(models.AbstractModel):
    """Journals Audit: debit and credit per journal, its journal items and
    tax summary, from ``report_journal_audit``."""
    _name = 'account.dynamic.report.journal_audit'
    _inherit = 'account.dynamic.report'
    _description = 'Journals Audit'

    _filters = ('date', 'target_move', 'journals')

    def _report_title(self):
        return _("Journals Audit")

    def _option_defs(self):
        return [{'key': 'sort_selection', 'label': _("Entries Sorted by"),
                 'type': 'select', 'default': 'move_name',
                 'values': {'date': _("Date"),
                            'move_name': _("Journal Entry Number")}}]

    def _columns(self, options):
        return [{'name': _("Debit"), 'type': 'monetary'},
                {'name': _("Credit"), 'type': 'monetary'}]

    def _data(self, options):
        return {'form': {'target_move': options['target_move'],
                         'used_context': self._report_context(options)}}

    def _journals(self, options):
        return self.env['account.journal'].browse(options['journal_ids']) \
            or self.env['account.journal'].search(
                get_report_journal_domain(self.env.company))

    def _lines(self, options):
        audit = self.env['report.base_accounting_kit.report_journal_audit']
        data = self._data(options)
        lines, totals = [], [0.0, 0.0]
        for journal in self._journals(options):
            debit = audit._sum_debit(data, journal)
            credit = audit._sum_credit(data, journal)
            if not debit and not credit:
                continue
            totals = [totals[0] + debit, totals[1] + credit]
            lines.append({'id': 'journal_%s' % journal.id,
                          'name': _label(journal.code, journal.name),
                          'level': 0, 'unfoldable': True,
                          'columns': [debit, credit]})
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'class': 'total', 'columns': totals})
        return lines

    def _child_lines(self, options, line_id):
        if not line_id.startswith('journal_'):
            return []
        journal = self.env['account.journal'].browse(
            int(line_id.split('_')[1])).exists()
        if not journal:
            return []
        audit = self.env['report.base_accounting_kit.report_journal_audit']
        data = self._data(options)
        currency = self.env.company.currency_id
        lines = [{
            'id': 'aml_%s' % line.id,
            'name': _label(fields.Date.to_string(line.date),
                           line.move_id.name, line.account_id.code,
                           line.partner_id.name, line.name),
            'level': 1, 'parent_id': line_id,
            'columns': [line.debit, line.credit],
        } for line in audit.lines(options['target_move'], journal.id,
                                  options['sort_selection'], data)]
        for tax, values in audit._get_taxes(data, journal).items():
            lines.append({
                'id': 'taxsum_%s_%s' % (journal.id, tax.id),
                'name': _("Tax %(tax)s: base %(base)s, tax %(amount)s",
                          tax=tax.name,
                          base=currency.round(values['base_amount']),
                          amount=currency.round(values['tax_amount'])),
                'level': 1, 'parent_id': line_id, 'columns': ['', '']})
        return lines
