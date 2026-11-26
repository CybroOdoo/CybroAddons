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
from odoo import Command
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestReportCompany(AccountingKitTestCommon):
    """Reports print the report company (P1.7): its name, currency and
    account codes when another company is the current one; selected
    branches are included; a notice names companies not covered."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        eur = cls.env.ref('base.EUR')
        eur.active = True
        cls.beta = cls.setup_other_company(name='Kit Beta')['company']
        cls.beta.currency_id = eur
        cls.rec_b = cls.kit_account('asset_receivable', cls.beta)
        cls.inc_b = cls.kit_account('income', cls.beta)
        cls.customer_b = cls.env['res.partner'].create({'name': 'Beta Customer'})
        cls.kit_entry(cls.ymd(2, 1), [(cls.rec_b, 1234, 0, cls.customer_b), (cls.inc_b, 0, 1234, cls.customer_b)],
                      company=cls.beta)

    def report_ab(self, name):
        """The report run while both companies are selected, A current."""
        return self.env['account.dynamic.report.' + name].with_context(
            allowed_company_ids=[self.company.id, self.beta.id])

    def html_ab(self, name, options):
        action = self.env.ref('base_accounting_kit.action_report_kit_statement')
        return action.with_context(allowed_company_ids=[self.company.id, self.beta.id])._render_qweb_html(
            action.report_name, [], data=self.report_ab(name).action_export_pdf(options)['data'])[0].decode()

    def test_other_company_printed(self):
        """Company B printed while A is current: B's name, its currency (EUR,
        € with the currency symbol option) and B's account codes, not A."""
        options = {'company_id': self.beta.id, 'unfold_all': True}
        for name in ('general_ledger', 'trial_balance', 'partner_ledger', 'day_book'):
            html = self.html_ab(name, options)
            self.assertIn(self.beta.name, html, name)
            self.assertNotIn(self.company.name, html, name)
            self.assertIn('EUR', html, name)
            self.assertIn('€', self.html_ab(name, dict(options, currency_symbol=True)), name)
        self.assertIn(self.rec_b.with_company(self.beta).code, self.html_ab('trial_balance', options))
        aged = self.report_ab('aged').get_report({'company_id': self.beta.id})
        self.assertIn('partner_%s' % self.customer_b.id, self.by_id(aged))

    def test_xlsx_currency_symbol_after(self):
        """XLSX of company B (EUR, symbol after the amount) with the currency
        symbol option: "1,000.00 €" format, negatives red; decimals of the
        currency."""
        report = self.report_ab('trial_balance')
        _data, table = report._export_table({'company_id': self.beta.id, 'currency_symbol': True})
        positive, negative = table['num_format'].split(';')
        self.assertTrue(positive.endswith('\N{NO-BREAK SPACE}€"'), positive)
        self.assertTrue(negative.startswith('[Red]-'), negative)
        self.assertIn('#,##0.00', positive)
        _data, table = report._export_table({'company_id': self.beta.id})
        self.assertNotIn('€', table['num_format'])

    def test_notice(self):
        """A notice names the selected companies the report does not cover."""
        notice = self.report_ab('general_ledger').get_report({'company_id': self.company.id})['notice']
        self.assertIn(self.beta.name, notice)
        self.assertFalse(self.dyn('general_ledger').get_report({})['notice'])

    def test_branch_included(self):
        """A selected branch is included in the parent's report; without
        it, only the parent; the branch alone shows its own figures."""
        branch = self.env['res.company'].create({'name': 'Kit Branch', 'parent_id': self.company.id})
        self.env.user.company_ids |= branch
        rec = self.kit_account('asset_receivable')
        inc = self.kit_account('income')
        self.kit_entry(self.ymd(2, 1), [(rec, 100, 0), (inc, 0, 100)])
        journal = self.env['account.journal'].create({
            'name': 'Branch Misc', 'type': 'general', 'code': 'KBRM', 'company_id': branch.id})
        self.env['account.move'].with_context(allowed_company_ids=[branch.id, self.company.id]).create({
            'move_type': 'entry', 'date': self.ymd(2, 1), 'journal_id': journal.id,
            'line_ids': [Command.create({'account_id': rec.id, 'debit': 50, 'name': 't'}),
                         Command.create({'account_id': inc.id, 'credit': 50, 'name': 't'})]}).action_post()

        def receivable(company_ids, report_company):
            report = self.env['account.dynamic.report.trial_balance'].with_context(
                allowed_company_ids=company_ids).get_report({'company_id': report_company.id})
            line = next(line for line in report['lines'] if line['id'] == 'account_%s' % rec.id)
            return line['columns'][1] - line['columns'][2]

        self.assertAmount(receivable([self.company.id, branch.id], self.company), 150)
        self.assertAmount(receivable([self.company.id], self.company), 100)
        self.assertAmount(receivable([branch.id, self.company.id], branch), 50)
        notice = self.env['account.dynamic.report.general_ledger'].with_context(
            allowed_company_ids=[self.company.id, branch.id]).get_report({})['notice']
        self.assertFalse(notice)
