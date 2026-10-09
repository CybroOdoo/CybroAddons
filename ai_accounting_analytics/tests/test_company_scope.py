# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""Which companies the figures cover: the selected companies and their
branches, in one currency, identically for the dedicated tools and the
generic queries."""
import json

from freezegun import freeze_time

from odoo.tests import tagged

from .common import AiAccountingDataCommon


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestCompanyScope(AiAccountingDataCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.branch = cls.env['res.company'].create({'name': 'AI Branch', 'parent_id': cls.company.id})
        cls.env.cr.precommit.run()  # load the chart of accounts
        cls.foreign = cls.setup_other_company(
            name='AI Foreign Co', currency_id=cls.env.ref('base.EUR').id)['company']
        cls.env.user.company_ids |= cls.branch + cls.foreign
        cls.branch_invoice = cls._company_invoice(cls.branch, 700.0)
        cls.foreign_invoice = cls._company_invoice(cls.foreign, 9000.0)

    @classmethod
    def _company_invoice(cls, company, amount):
        move = cls.env['account.move'].with_company(company).create({
            'move_type': 'out_invoice', 'company_id': company.id, 'partner_id': cls.partner_a.id,
            'invoice_date': '2026-10-12', 'date': '2026-10-12',
            'invoice_line_ids': [(0, 0, {'name': 'AI scope', 'price_unit': amount, 'tax_ids': []})],
        })
        move.action_post()
        return move

    def toolkit_for(self, *companies):
        return self.toolkit.with_context(allowed_company_ids=[company.id for company in companies])

    def run_tool(self, toolkit, name, arguments):
        output = toolkit._ai_run_tool(name, arguments)
        self.assertFalse(output.get('error'), output['model'])
        return output['model']

    def test_scope(self):
        if self.foreign.currency_id == self.company.currency_id:
            self.skipTest("The foreign company needs another currency")
        scope, excluded = self.toolkit_for(self.company, self.branch, self.foreign)._ai_company_scope()
        self.assertEqual(scope, self.company + self.branch)
        self.assertEqual(excluded, self.foreign)
        scope, excluded = self.toolkit_for(self.company)._ai_company_scope()
        self.assertEqual(scope, self.company, "A branch left out in the switcher stays out")

    def test_branches_are_included(self):
        """A parent company's figures include its selected branches (the
        previous code only ever read the current company)."""
        toolkit = self.toolkit_for(self.company, self.branch)
        own = 3000.0 + self.inv_b.amount_untaxed - 100.0
        model = self.run_tool(toolkit, 'get_top_partners', {'kind': 'customer', 'period': 'this_month'})
        self.assertEqual(model['total'], own + 700.0)
        self.assertEqual(model['companies'], (self.company + self.branch).mapped('name'))
        model = self.run_tool(toolkit, 'get_kpi_overview', {'period': 'this_month'})
        self.assertEqual(model['revenue'], own + 700.0)
        model = self.run_tool(toolkit, 'get_profit_and_loss', {'period': 'this_month', 'detail': 'accounts'})
        self.assertIn(own + 700.0, [row[1] for row in model['rows']], "The Kit report covers the branch too")
        model = self.run_tool(toolkit, 'get_invoices', {'kind': 'customer', 'status': 'all', 'period': 'this_month'})
        self.assertIn(self.branch_invoice.name, [row[0] for row in model['rows']])

    def test_generic_queries_cover_the_same_companies(self):
        """The same question gives the same total through both kinds of tool."""
        for companies in ((self.company,), (self.company, self.branch), (self.company, self.branch, self.foreign)):
            with self.subTest(companies=[company.name for company in companies]):
                toolkit = self.toolkit_for(*companies)
                dedicated = self.run_tool(toolkit, 'get_top_partners', {'kind': 'customer', 'period': 'this_month'})
                generic = self.run_tool(toolkit, 'query_records', {
                    'model': 'account.move', 'aggregate': 'amount_untaxed_signed:sum', 'group_by': ['move_type'],
                    'domain': json.dumps([['state', '=', 'posted'], ['move_type', 'in', ['out_invoice', 'out_refund']],
                                          ['invoice_date', '>=', '2026-10-01'], ['invoice_date', '<=', '2026-10-31']])})
                self.assertAlmostEqual(sum(row[1] for row in generic['rows']), dedicated['total'])

    def test_other_currency_is_left_out_and_said(self):
        if self.foreign.currency_id == self.company.currency_id:
            self.skipTest("The foreign company needs another currency")
        toolkit = self.toolkit_for(self.company, self.branch, self.foreign)
        model = self.run_tool(toolkit, 'get_top_partners', {'kind': 'customer', 'period': 'this_month'})
        self.assertNotIn(9000.0, [row[2] for row in model['rows']])
        self.assertIn('AI Foreign Co', model['excluded_companies'])
        model = self.run_tool(toolkit, 'query_records', {
            'model': 'account.move', 'domain': json.dumps([['id', '=', self.foreign_invoice.id]])})
        self.assertEqual(model['count'], 0)

    def test_foreign_company_alone(self):
        """Selecting only the other company answers in its own currency."""
        toolkit = self.toolkit_for(self.foreign)
        model = self.run_tool(toolkit, 'get_top_partners', {'kind': 'customer', 'period': 'this_month'})
        self.assertEqual(model['total'], 9000.0)
        self.assertNotIn('excluded_companies', model)

    def test_system_prompt_names_the_companies(self):
        companies = (self.company + self.branch).ids
        chat, _message = self.Chat.with_context(allowed_company_ids=companies)._ai_prepare_turn("Hi")
        prompt = chat.with_context(allowed_company_ids=companies)._ai_system_prompt()
        self.assertIn('AI Branch', prompt)
        self.assertIn(self.company.name, prompt)
