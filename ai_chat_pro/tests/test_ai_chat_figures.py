# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant, _keywords
from odoo.addons.ai_chat_pro.tests.test_ai_chat_pro import mock_decisions


@tagged('post_install', '-at_install')
class TestAiChatFigures(TransactionCase):
    """ Accounting figures, computed from posted journal items, in a company of their own. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.has_accounting = 'account.move' in cls.env
        if not cls.has_accounting:
            return
        cls.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        cls.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.use_olg', False)
        cls.company = cls.env['res.company'].create({'name': "Figures Co"})
        cls.accountant = new_test_user(
            cls.env, login='ai_chat_accountant',
            groups='base.group_user,account.group_account_manager,ai_chat_pro.group_ai_chat_user',
            company_id=cls.company.id, company_ids=[cls.company.id],
        )
        Account = cls.env['account.account'].with_company(cls.company)

        def account(code, account_type):
            return Account.create({'name': f"AI {code}", 'code': code, 'account_type': account_type,
                                   'company_ids': [cls.company.id]})

        cls.income = account('AI400', 'income')
        cls.cost = account('AI500', 'expense_direct_cost')
        cls.expense = account('AI600', 'expense')
        cls.receivable = account('AI110', 'asset_receivable')
        cls.bank = account('AI100', 'asset_cash')
        journal = cls.env['account.journal'].create({
            'name': "AI Misc", 'code': 'AIMSC', 'type': 'general', 'company_id': cls.company.id,
        })
        today = fields.Date.context_today(cls.accountant)

        def entry(lines, date=today, post=True):
            move = cls.env['account.move'].with_company(cls.company).create({
                'journal_id': journal.id, 'date': date, 'company_id': cls.company.id,
                'line_ids': [(0, 0, {'account_id': acc.id, 'debit': max(amount, 0), 'credit': max(-amount, 0),
                                     'name': "AI"}) for acc, amount in lines],
            })
            if post:
                move.action_post()
            return move

        entry([(cls.receivable, 1000), (cls.income, -1000)])
        entry([(cls.cost, 250), (cls.bank, -250)])
        entry([(cls.expense, 300), (cls.bank, -300)])
        entry([(cls.bank, 1000), (cls.receivable, -1000)])
        # neither drafts, nor other fiscal years count in this year's profit
        entry([(cls.expense, 5000), (cls.bank, -5000)], post=False)
        entry([(cls.receivable, 700), (cls.income, -700)], date=today - timedelta(days=800))

    def setUp(self):
        super().setUp()
        if not self.has_accounting:
            self.skipTest("The accounting app is not installed.")

    def _ask(self, question, **decisions):
        calls, mock = mock_decisions(**decisions)
        Conversation = self.env['ai.chat.conversation'].with_user(self.accountant).with_context(
            allowed_company_ids=[self.company.id],
        )
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: []):
            message = Conversation.ask_question(False, question)['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        return message, calls

    def test_figures_are_offered_for_accounting_words(self):
        Assistant = self.env['ai.chat.assistant'].with_user(self.accountant)
        self.assertTrue(Assistant._get_figure_candidate(_keywords("what is my profit this month")))
        self.assertTrue(Assistant._get_figure_candidate(_keywords("how much cash in bank")))
        self.assertIsNone(Assistant._get_figure_candidate(_keywords("list my top 10 sale orders")))
        # words no figure bears ("turnover"): offered when the agent read that accounting figures are asked
        self.assertIsNone(Assistant._get_figure_candidate(_keywords("our turnover")))
        intent = Assistant._clean_intent({'intent': 'query', 'figures': True}, "our turnover")
        self.assertTrue(Assistant.with_context(ai_chat_intent=intent)._get_figure_candidate(_keywords("our turnover")))
        catalog = Assistant._get_figure_catalog()
        self.assertIn('type:asset_cash', catalog, "the figures are built from the account types of Odoo")
        self.assertEqual(catalog['net_profit']['scope'], 'period')
        self.assertEqual(catalog['type:asset_cash']['scope'], 'balance')

    def test_net_profit_of_the_fiscal_year(self):
        message, calls = self._ask("what is my profit", figure='net_profit', period='default', breakdown='none')
        result = message['result']
        self.assertEqual(result['type'], 'value')
        self.assertEqual([column['label'] for column in result['columns']],
                         ["Net Profit", "Total Income", "Total Expenses"])
        self.assertEqual(result['rows'][0]['raw'], [450.0, 1000.0, 550.0])
        self.assertEqual(result['model'], 'account.move.line')

    def test_figures_rather_than_report_records(self):
        """ The records of accounting reports are their definitions: the decision model
        is offered the computed figures next to them. """
        report = {'model': 'account.report', 'label': "Accounting Report", 'score': 5,
                  'path': 'Invoicing/Reporting/Tax Report', 'domain': ''}
        calls, mock = mock_decisions(data='option_1', figure='net_profit', period='last_fiscal_year',
                                     breakdown='none')
        Conversation = self.env['ai.chat.conversation'].with_user(self.accountant).with_context(
            allowed_company_ids=[self.company.id],
        )
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [report]), \
                patch.object(AiChatAssistant, '_get_total_candidates', lambda self_, *args: []):
            message = Conversation.ask_question(False, "profit of last year")['messages'][1]
        options = calls[0][1]['data']['criteria']
        self.assertIn("Accounting Report [account.report] records themselves", options["option_0"])
        self.assertIn("Accounting figures computed from the posted journal items", options['option_1'])
        self.assertEqual(message['result']['heading'], "Net Profit")
        self.assertEqual(message['result']['rows'][0]['raw'][0], 0.0, "nothing was posted last fiscal year")

    def test_gross_profit_and_all_time_income(self):
        message, _calls = self._ask("gross profit", figure='gross_profit', period='default', breakdown='none')
        self.assertEqual(message['result']['rows'][0]['raw'][0], 750.0)
        message, _calls = self._ask("revenue since the beginning", figure='group:income', period='all_time',
                                    breakdown='none')
        self.assertEqual(message['result']['rows'][0]['raw'][0], 1700.0)

    def test_balance_figures(self):
        message, _calls = self._ask("cash in bank", figure='type:asset_cash', period='this_month', breakdown='none')
        # a balance: everything up to the end of the period, whatever its start
        self.assertEqual(message['result']['rows'][0]['raw'][0], 450.0)
        self.assertIn("Balance at", message['result']['tags'][0])
        message, _calls = self._ask("receivables", figure='type:asset_receivable', period='default',
                                    breakdown='none')
        self.assertEqual(message['result']['rows'][0]['raw'][0], 700.0)

    def test_breakdown_per_account(self):
        message, _calls = self._ask("expenses per account", figure='group:expense', period='default',
                                    breakdown='account')
        result = message['result']
        self.assertEqual(result['row_model'], 'account.account')
        self.assertEqual([(row['id'], row['raw'][1]) for row in result['rows']],
                         [(self.expense.id, 300.0), (self.cost.id, 250.0)])
        self.assertEqual(result['chart']['type'], 'bar')

    def test_no_figures_without_accounting_access(self):
        employee = new_test_user(
            self.env, login='ai_chat_employee', groups='base.group_user,ai_chat_pro.group_ai_chat_user',
            company_id=self.company.id, company_ids=[self.company.id],
        )
        Assistant = self.env['ai.chat.assistant'].with_user(employee)
        if self.env['account.move.line'].with_user(employee).has_access('read'):
            self.skipTest("Employees can read journal items in this database.")
        self.assertIsNone(Assistant._get_figure_candidate(_keywords("what is my profit")))
