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
from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon
from odoo.addons.ai_accounting_analytics.llm import LLMResult, ToolCall, Usage

from .common import AiAccountingMixin, answer, tool_call


@tagged('post_install', '-at_install')
class TestUi(AiAccountingMixin, AccountTestInvoicingHttpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ai_accounting()
        cls.env.user.sudo().ai_accounting_consent_date = False
        cls.init_invoice('out_invoice', cls.partner_a, fields.Date.today(), post=True,
                         amounts=[1800.0], taxes=[])

    def test_chat_tour(self):
        """Consent, streamed answer with a table, then a chart and KPI cards."""
        both = LLMResult(tool_calls=[
            ToolCall(id='1', name='get_kpi_overview', arguments={}),
            ToolCall(id='2', name='get_trend', arguments={'metric': 'sales', 'chart': 'bar'}),
        ], usage=Usage(input_tokens=10, output_tokens=10))
        with self.fake_llm(
            tool_call('get_top_partners', kind='customer', period='this_year'),
            answer("**%s** leads the ranking." % self.partner_a.name),
            both,
            answer("Sales are growing."),
        ):
            self.start_tour('/odoo/action-ai_accounting_analytics.ai_accounting_chat_action_client',
                            'ai_accounting_analytics_chat_tour', login=self.env.user.login)
        self.assertTrue(self.env.user.ai_accounting_consent_date)
        chat = self.env['ai.accounting.chat'].search([('user_id', '=', self.env.uid)])
        self.assertEqual(len(chat), 1)
        self.assertEqual(len(chat.message_ids), 4)
        self.assertTrue(self.env['ai.accounting.usage'].search_count([('chat_id', '=', chat.id)]))
