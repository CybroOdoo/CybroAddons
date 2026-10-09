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
"""Figures of the AI Usage & Cost dashboard."""
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged

from .common import AiAccountingCommon, answer, tool_call


@tagged('post_install', '-at_install')
class TestUsageDashboard(AiAccountingCommon):

    def ask_scripted(self, question, *script, user=None):
        chat_model = self.Chat.with_user(user) if user else self.Chat
        with self.fake_llm(*script):
            chat, message = chat_model._ai_prepare_turn(question)
            list(chat._ai_run_turn(message))
        return chat

    def dashboard(self, period='this_month', user=None):
        Usage = self.env['ai.accounting.usage']
        return (Usage.with_user(user) if user else Usage).ai_get_dashboard(period)

    def test_figures(self):
        self.ask_scripted("Top customers", tool_call('get_top_partners', kind='customer'),
                          answer("A leads.", input_tokens=1000, output_tokens=100, cached_tokens=4000))
        self.ask_scripted("Hello", answer("Hi.", input_tokens=500, output_tokens=50))
        data = self.dashboard()
        usages = self.env['ai.accounting.usage'].search([])
        kpis = {key: value['value'] for key, value in data['kpis'].items()}
        self.assertTrue(data['has_data'])
        self.assertAlmostEqual(kpis['cost'], sum(usages.mapped('cost')), places=9)
        self.assertEqual(kpis['tokens'], sum(usages.mapped('total_tokens')))
        self.assertEqual(kpis['answers'], 2)
        self.assertEqual(kpis['calls'], 3)
        self.assertAlmostEqual(kpis['cost_per_answer'], kpis['cost'] / 2, places=9)
        # gemini-3.5-flash-lite seed: 0.30 input, 0.03 cached per million tokens.
        self.assertAlmostEqual(kpis['cache_savings'], 4000 * (0.30 - 0.03) / 1_000_000, places=9)
        self.assertEqual(kpis['cache_rate'], round(4000 / (1000 + 1000 + 500 + 4000) * 100, 1))
        self.assertIsNone(data['kpis']['cost']['delta'], "Nothing to compare with")

        timeline = data['timeline']
        self.assertEqual(timeline['granularity'], 'day')
        self.assertEqual(len(timeline['labels']), len(timeline['cost']))
        self.assertAlmostEqual(sum(timeline['cost']), kpis['cost'], places=6)
        self.assertEqual(sum(timeline['tokens']), kpis['tokens'])

        self.assertEqual([row['name'] for row in data['by_model']], [self.ai_model.name])
        self.assertEqual(data['by_model'][0]['share'], 100.0)
        self.assertEqual(data['by_model'][0]['answers'], 2)
        mix = {item['key']: item['value'] for item in data['token_mix']}
        self.assertEqual(mix['cached_tokens'], 4000)

        recent = data['recent']
        self.assertEqual([item['question'] for item in recent], ["Hello", "Top customers"])
        self.assertEqual(recent[1]['steps'], 1)
        self.assertTrue(recent[0]['chat_id'])

    def test_comparison_with_the_previous_period(self):
        self.ask_scripted("Now", answer("Now.", input_tokens=2000, output_tokens=0))
        self.ask_scripted("Before", answer("Before.", input_tokens=1000, output_tokens=0))
        before = self.env['ai.accounting.usage'].search([], order='id desc', limit=1)
        moment = fields.Datetime.now() - relativedelta(months=1)
        self.env.cr.execute("UPDATE ai_accounting_usage SET create_date = %s WHERE id = %s", [moment, before.id])
        self.env.invalidate_all()
        data = self.dashboard('last_30_days')
        self.assertEqual(data['kpis']['tokens']['value'], 2000)
        self.assertEqual(data['kpis']['tokens']['delta'], 100.0)
        self.assertEqual(self.dashboard('all_time')['kpis']['tokens']['value'], 3000)
        self.assertIsNone(self.dashboard('all_time')['kpis']['tokens']['delta'])

    def test_every_period(self):
        self.ask_scripted("Hello", answer("Hi."))
        for period in ('this_month', 'last_month', 'last_30_days', 'this_year', 'all_time'):
            with self.subTest(period=period):
                data = self.dashboard(period)
                self.assertEqual(len(data['timeline']['labels']), len(data['timeline']['tokens']))
                self.assertLessEqual(len(data['timeline']['labels']), 400)
        with self.assertRaises(UserError):
            self.dashboard('forever')

    def test_everyone_sees_their_own_usage_admins_see_all(self):
        colleague = new_test_user(self.env, login='ai_colleague', groups='base.group_user,base_accounting_kit.group_account_chief')
        colleague.sudo().ai_accounting_consent_date = fields.Datetime.now()
        self.env['ai.accounting.api.key'].with_user(colleague).create({
            'provider_id': self.provider.id, 'new_api_key': 'AIza-colleague-123456'})
        self.ask_scripted("Mine", answer("Mine."))
        self.ask_scripted("Theirs", answer("Theirs."), user=colleague)
        data = self.dashboard(user=colleague)
        self.assertEqual(data['kpis']['answers']['value'], 1)
        self.assertEqual([row['name'] for row in data['by_user']], [colleague.name])
        self.assertEqual([item['question'] for item in data['recent']], ["Theirs"])
        admin = new_test_user(self.env, login='ai_admin', groups='base.group_system,base_accounting_kit.group_account_chief',
                              company_id=self.env.company.id, company_ids=[(6, 0, self.env.company.ids)])
        data = self.dashboard(user=admin)
        self.assertEqual(len(data['by_user']), 2, "Administrators see everyone's usage")
        self.assertEqual(data['recent'], [], "...but only their own questions")

    def test_no_usage_yet(self):
        data = self.dashboard()
        self.assertFalse(data['has_data'])
        self.assertEqual(data['kpis']['cost']['value'], 0.0)
        self.assertEqual(data['by_model'], [])
