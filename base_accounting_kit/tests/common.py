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
"""Shared base of the kit's tests, on top of core's accounting test base
(company with a chart of accounts, partners, products, taxes, an
accounting user)."""
import io
import json
from datetime import date

import openpyxl

from odoo import Command, fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class AccountingKitTestCommon(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.today = fields.Date.context_today(cls.env.user)
        cls.year = cls.today.year

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    @classmethod
    def kit_account(cls, account_type, company=None):
        """An account of the type in the company, created when the chart
        of accounts has none."""
        company = company or cls.company
        Account = cls.env['account.account']
        account = Account.search([('company_ids', 'in', company.id),
                                  ('account_type', '=', account_type)], limit=1)
        if not account:
            account = Account.with_company(company).create({
                'name': 'Kit %s' % account_type,
                'code': 'KIT%s' % (abs(hash(account_type)) % 99999),
                'account_type': account_type,
                'company_ids': [Command.set(company.ids)],
            })
        return account

    @classmethod
    def kit_journal(cls, journal_type, company=None):
        company = company or cls.company
        return cls.env['account.journal'].search(
            [('company_id', '=', company.id), ('type', '=', journal_type)],
            limit=1)

    @classmethod
    def kit_entry(cls, day, lines, post=True, journal=None, company=None):
        """A journal entry; ``lines``: ``(account, debit, credit[, partner])``."""
        company = company or cls.company
        journal = journal or cls.kit_journal('general', company)
        move = cls.env['account.move'].with_company(company).create({
            'move_type': 'entry',
            'date': day,
            'journal_id': journal.id,
            'line_ids': [Command.create({
                'account_id': line[0].id,
                'debit': line[1],
                'credit': line[2],
                'partner_id': line[3].id if len(line) > 3 and line[3] else False,
                'name': 'kit test',
            }) for line in lines],
        })
        if post:
            move.action_post()
        return move

    @classmethod
    def ymd(cls, month, day, years_back=0):
        return date(cls.year - years_back, month, day)

    # ------------------------------------------------------------------
    # Dynamic reports
    # ------------------------------------------------------------------
    def dyn(self, name, company=None):
        """The dynamic report ``account.dynamic.report.<name>``, run as the
        test user in ``company``."""
        company = company or self.company
        return self.env['account.dynamic.report.' + name].with_context(
            allowed_company_ids=[company.id])

    @staticmethod
    def by_id(report):
        return {line['id']: line for line in report['lines']}

    def assertAmount(self, value, expected, msg=None):
        self.assertAlmostEqual(value or 0.0, expected, places=2, msg=msg)

    def pdf_html(self, name, options, company=None):
        """HTML of the report PDF (the PDF is rendered from it)."""
        report = self.dyn(name, company)
        action = self.env.ref('base_accounting_kit.action_report_kit_statement')
        return action.with_context(allowed_company_ids=[(company or self.company).id])\
            ._render_qweb_html(action.report_name, [],
                               data=report.action_export_pdf(options)['data'])[0].decode()

    def xlsx_sheet(self, name, options, company=None):
        """Active sheet of the report XLSX, as built by the export."""
        report = self.dyn(name, company)
        stream = io.BytesIO()
        response = type('Response', (), {'stream': stream})()
        data = report.action_export_xlsx(options)['data']
        report.get_xlsx_report(json.loads(data['options']), response)
        return openpyxl.load_workbook(io.BytesIO(stream.getvalue())).active

    @staticmethod
    def sheet_values(sheet):
        return [cell.value for row in sheet.iter_rows() for cell in row]
