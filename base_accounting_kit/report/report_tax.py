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
from datetime import datetime

from odoo import api, models

from ..models.report_company import get_report_branches, get_report_company


class ReportTax(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_tax'
    _description = 'Tax Report'

    def _sql_from_amls_one(self):
        # tax lines per tax and per originating group of taxes (core
        # ``group_tax_id``), so a child tax shared by two groups is split
        sql = """SELECT "account_move_line".tax_line_id, "account_move_line".group_tax_id,
                        COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                    FROM %s
                    WHERE %s  GROUP BY "account_move_line".tax_line_id, "account_move_line".group_tax_id"""
        return sql

    def _sql_from_amls_two(self):
        sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                 FROM %s
                 INNER JOIN account_move_line_account_tax_rel r ON ("account_move_line".id = r.account_move_line_id)
                 INNER JOIN account_tax t ON (r.account_tax_id = t.id)
                 WHERE %s GROUP BY r.account_tax_id"""
        return sql

    def _compute_from_amls(self, options, taxes):
        """Fill the tax and net amounts (debit - credit) of ``taxes`` using
        the filters of the context (dates, journals, state, company)."""
        # compute the tax amount (cancelled entries are always excluded by
        # ``_query_get``)
        sql = self._sql_from_amls_one()
        # Taxes based on payment count when paid (core cash basis entries),
        # not on the invoice: core's exigible domain (P2.4-a).
        Line = self.env['account.move.line']
        tables, where_clause, where_params = Line._query_get(
            list(Line._get_tax_exigible_domain()))

        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        for tax_id, group_id, amount in self.env.cr.fetchall():
            key = '%s-%s' % (group_id, tax_id) if group_id else str(tax_id)
            if key in taxes:
                taxes[key]['tax'] += amount

        # compute the net amount
        sql2 = self._sql_from_amls_two()
        query = sql2 % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        for tax_id, amount in self.env.cr.fetchall():
            if str(tax_id) in taxes:
                taxes[str(tax_id)]['net'] = amount

    @api.model
    def get_lines(self, options):
        """Return the tax lines grouped by tax type, with a total per group.

        Customer documents are booked on the credit side, so sales amounts
        are shown as -(debit - credit) and purchases as (debit - credit):
        refunds reduce the totals and can make them negative.

        Withholding taxes (core ``l10n_account_withholding_tax``, when
        installed) get their own ``withholding`` group.
        """
        used_context = dict(options.get('used_context') or {})
        company = get_report_company(self.env, options)
        used_context['company_id'] = company.id
        used_context['strict_range'] = True
        if not used_context.get('date_to'):
            used_context['date_to'] = str(datetime.today().date())

        # One entry per tax; a group of taxes (e.g. CGST + SGST) is listed
        # with its children under it: base lines carry the group, tax lines
        # the child taxes.
        taxes = {}
        withholding = 'is_withholding_tax' in self.env['account.tax']._fields
        for tax in self.env['account.tax'].with_context(
                active_test=False).search([
                    ('type_tax_use', '!=', 'none'),
                    *self.env['account.tax']._check_company_domain(
                        get_report_branches(company))]):
            taxes[str(tax.id)] = {'id': tax.id, 'key': str(tax.id), 'tax': 0, 'net': 0, 'name': tax.name,
                                  'type': tax.type_tax_use, 'level': 1, 'children': [],
                                  'section': 'withholding' if withholding and tax.is_withholding_tax
                                  else tax.type_tax_use}
            if tax.amount_type == 'group':
                for child in tax.children_tax_ids.filtered(lambda t: t.type_tax_use == 'none'):
                    key = '%s-%s' % (tax.id, child.id)
                    taxes[key] = {'id': child.id, 'key': key, 'group_id': tax.id, 'tax': 0, 'net': 0,
                                  'name': child.name, 'type': tax.type_tax_use, 'level': 2,
                                  'section': taxes[str(tax.id)]['section']}
                    taxes[str(tax.id)]['children'].append(key)
        self.with_context(**used_context)._compute_from_amls(options, taxes)
        for group in [t for t in taxes.values() if t.get('children')]:
            group['tax'] = sum(taxes[key]['tax'] for key in group['children'])
            for key in group['children']:
                taxes[key]['net'] = group['net']

        currency = company.currency_id
        groups = dict((tp, []) for tp in ['sale', 'purchase', 'withholding'])
        totals = dict((tp, {'net': 0.0, 'tax': 0.0}) for tp in groups)
        for tax in taxes.values():
            sign = -1 if tax['type'] == 'sale' else 1
            tax['net'] = sign * tax['net']
            tax['tax'] = sign * tax['tax']
        for tax in taxes.values():
            if tax['level'] == 2:
                continue  # listed under its group
            if currency.is_zero(tax['tax']) and currency.is_zero(tax['net']):
                continue
            section = tax['section']
            groups[section].append(tax)
            groups[section] += [taxes[key] for key in tax.get('children', [])]
            # each base counted once: on the group, not on its children
            totals[section]['net'] += tax['net']
            totals[section]['tax'] += tax['tax']
        groups['totals'] = totals
        groups['has_withholding'] = withholding
        return groups
