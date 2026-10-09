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
"""The agent loop under everything a provider or a model can throw at it:
odd tool names and arguments, repeated calls, floods of calls, empty or
truncated answers, cut streams, failing tools and every provider error.

Whatever happens, a turn must end with a ``done`` event, a stored message
and either an answer or a clear error, never an exception."""
import json
from unittest.mock import patch

from freezegun import freeze_time

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.ai_accounting_analytics.llm import LLMError, LLMResult, ToolCall, Usage

from .common import AiAccountingDataCommon, answer, tool_call

TOOLKIT_LOGGER = 'odoo.addons.ai_accounting_analytics.models.ai_accounting_toolkit'


def calls(*items, text=''):
    """One AI step calling several tools: ``(name, arguments)`` pairs."""
    return LLMResult(text=text, usage=Usage(input_tokens=100, output_tokens=20), tool_calls=[
        ToolCall(id='call_%s' % index, name=name, arguments=arguments)
        for index, (name, arguments) in enumerate(items)])


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestAgentRobustness(AiAccountingDataCommon):

    def assistant(self, chat):
        return chat.message_ids.filtered(lambda message: message.role == 'assistant')[-1:]

    def assert_turn_completed(self, chat, events):
        self.assertEqual(events[-1]['type'], 'done', "A turn always ends with done")
        self.assertEqual([event['type'] for event in events].count('done'), 1)
        message = self.assistant(chat)
        self.assertTrue(message)
        self.assertTrue(message.content or message.error or any(
            part['type'] != 'text' for part in message.parts or []), "Answer, data or an error")
        json.dumps(events, default=str)
        return message

    def tool_results(self, fake, call_index):
        """Tool results sent back to the model with AI call ``call_index``."""
        return [json.loads(result['content']) | {'is_error': result['is_error']}
                for result in fake.calls[call_index]['messages'][-1]['results']]

    # Tool calls -----------------------------------------------------------
    def test_prefixed_tool_name(self):
        with self.fake_llm(calls(('default_api.get_kpi_overview', {'period': 'this_month'})),
                           answer("Fine.")) as fake:
            chat, events = self.ask("KPIs")
        message = self.assert_turn_completed(chat, events)
        self.assertTrue(message.steps[0]['ok'])
        self.assertEqual(message.steps[0]['name'], 'get_kpi_overview')
        self.assertFalse(self.tool_results(fake, 1)[0]['is_error'])

    def test_unknown_tool(self):
        with self.fake_llm(calls(('get_weather', {'city': 'Kochi'})), answer("I can't check the weather.")) as fake:
            chat, events = self.ask("Weather?")
        message = self.assert_turn_completed(chat, events)
        result = self.tool_results(fake, 1)[0]
        self.assertTrue(result['is_error'])
        self.assertIn('get_kpi_overview', result['error'])
        self.assertFalse(message.error)

    def test_garbage_arguments(self):
        for arguments in ([1, 2], 'not json', 42, None, {'period': {'deep': [1]}}):
            with self.subTest(arguments=arguments):
                with self.fake_llm(calls(('get_kpi_overview', arguments)), answer("Sorry.")) as fake:
                    chat, events = self.ask("KPIs")
                self.assert_turn_completed(chat, events)
                result = self.tool_results(fake, 1)[0]
                if arguments is None:
                    self.assertFalse(result['is_error'])
                else:
                    self.assertTrue(result['is_error'])

    def test_gpt_style_empty_arguments_through_the_agent(self):
        """The production failure, end to end: the step succeeds."""
        arguments = {"chart": "none", "limit": 10, "model": "product.product", "order": "",
                     "domain": '[["create_date",">=","2026-10-01"],["create_date","<=","2026-10-31"]]',
                     "fields": ["id"], "display": False, "group_by": [], "aggregate": "count",
                     "related": {"mode": "without", "field": "", "model": "", "domain": ""}}
        with self.fake_llm(calls(('query_records', arguments)), answer("12 products.")) as fake:
            chat, events = self.ask("How many products were created in October?")
        message = self.assert_turn_completed(chat, events)
        self.assertTrue(message.steps[0]['ok'], message.steps[0].get('error'))
        self.assertIn('count', self.tool_results(fake, 1)[0])

    def test_repeated_call_is_answered_from_the_first_one(self):
        arguments = {'kind': 'customer', 'period': 'this_year'}
        with self.fake_llm(calls(('get_top_partners', arguments)), calls(('get_top_partners', dict(arguments))),
                           answer("Done.")) as fake, \
                patch.object(type(self.toolkit), '_ai_tool_get_top_partners', autospec=True,
                             side_effect=type(self.toolkit)._ai_tool_get_top_partners) as tool:
            chat, events = self.ask("Top customers")
        message = self.assert_turn_completed(chat, events)
        self.assertEqual(tool.call_count, 1, "The repeated call does not run again")
        self.assertEqual([part['type'] for part in message.parts].count('table'), 1, "Its table is not repeated")
        self.assertIn('Same call', self.tool_results(fake, 2)[0]['note'])

    def test_repeated_failing_call_tells_the_model_to_change(self):
        with self.fake_llm(calls(('query_records', {'model': 'nope'})), calls(('query_records', {'model': 'nope'})),
                           answer("Not possible.")) as fake:
            chat, events = self.ask("Query")
        self.assert_turn_completed(chat, events)
        self.assertIn('already failed', self.tool_results(fake, 2)[0]['note'])

    def test_flood_of_parallel_calls(self):
        flood = calls(*[('get_kpi_overview', {'period': period}) for period in (
            'today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month', 'this_quarter',
            'last_quarter', 'this_year', 'last_year', 'last_30_days', 'last_90_days')])
        with self.fake_llm(flood, answer("Summary.")) as fake:
            chat, events = self.ask("Everything")
        message = self.assert_turn_completed(chat, events)
        results = self.tool_results(fake, 1)
        self.assertEqual(len(results), 12, "Every call gets a result")
        self.assertEqual(sum(not result['is_error'] for result in results), 8)
        self.assertIn('Too many tool calls', results[-1]['error'])
        self.assertEqual(len(message.steps), 12)

    def test_tool_crash_does_not_end_the_turn(self):
        with self.fake_llm(calls(('get_kpi_overview', {}), ('get_cash_balances', {})), answer("Cash is fine.")) as fake, \
                patch.object(type(self.toolkit), '_ai_tool_get_kpi_overview', side_effect=ZeroDivisionError,
                             autospec=True), mute_logger(TOOLKIT_LOGGER):
            chat, events = self.ask("KPIs and cash")
        message = self.assert_turn_completed(chat, events)
        first, second = self.tool_results(fake, 1)
        self.assertTrue(first['is_error'])
        self.assertFalse(second['is_error'])
        self.assertEqual(message.content, "Cash is fine.")
        self.assertFalse(message.error)

    # Model answers ----------------------------------------------------------
    def test_empty_first_answer_is_retried(self):
        with self.fake_llm(answer(""), answer("Hello!")) as fake:
            chat, events = self.ask("Hi")
        message = self.assert_turn_completed(chat, events)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(message.content, "Hello!")
        self.assertFalse(message.error)

    def test_empty_answers_end_with_a_clear_error(self):
        empty = answer("")
        empty.stop_reason = 'SAFETY'
        with self.fake_llm(answer(""), empty):
            chat, events = self.ask("Hi")
        message = self.assert_turn_completed(chat, events)
        self.assertTrue(message.error)
        self.assertIn('empty answer (SAFETY)', events[-2]['message'])

    def test_data_without_comment_is_not_an_error(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.max_steps', 2)
        with self.fake_llm(tool_call('get_kpi_overview'), answer("")):
            chat, events = self.ask("KPIs")
        message = self.assert_turn_completed(chat, events)
        self.assertFalse(message.error)
        self.assertEqual([part['type'] for part in message.parts], ['kpis'])

    def test_truncated_answer_is_flagged(self):
        for reason in ('length', 'max_tokens', 'MAX_TOKENS'):
            with self.subTest(reason=reason):
                cut = answer("Revenue grew because")
                cut.stop_reason = reason
                with self.fake_llm(cut):
                    chat, events = self.ask("Why?")
                message = self.assert_turn_completed(chat, events)
                self.assertIn('output token limit', message.content)

    def test_stream_cut_before_the_end_is_retried(self):
        with self.fake_llm(('nodone', "Partial"), answer("Complete answer.")) as fake:
            chat, events = self.ask("Hi")
        message = self.assert_turn_completed(chat, events)
        self.assertEqual(message.content, "Complete answer.")
        self.assertIn('rewind', [event['type'] for event in events])
        fake.sleep.assert_called_once()

    def test_thinking_aloud_with_every_step(self):
        with self.fake_llm(calls(('get_kpi_overview', {}), text="Checking KPIs."),
                           calls(('get_cash_balances', {}), text="Now cash."),
                           answer("All good.")):
            chat, events = self.ask("Health check")
        message = self.assert_turn_completed(chat, events)
        self.assertEqual(message.content, "All good.")
        self.assertEqual([step.get('note') for step in message.steps], ["Checking KPIs.", "Now cash."])

    def test_model_keeps_calling_tools_until_the_step_limit(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.max_steps', 3)
        with self.fake_llm(tool_call('get_kpi_overview'), tool_call('get_cash_balances'),
                           answer("Concluded.")) as fake:
            chat, events = self.ask("Loop")
        message = self.assert_turn_completed(chat, events)
        self.assertEqual([call['allow_tools'] for call in fake.calls], [True, True, False])
        self.assertEqual(message.content, "Concluded.")

    # Provider errors ----------------------------------------------------------
    def test_every_provider_error(self):
        cases = [
            (400, False, '400'), (401, False, '401'), (403, False, '403'), (404, False, 'Fetch Models'),
            (413, False, '413'), (422, False, '422'), (408, True, 'still busy'), (409, True, 'still busy'),
            (429, True, 'still busy'), (500, True, 'still busy'), (502, True, 'still busy'),
            (503, True, 'still busy'), (504, True, 'still busy'), (529, True, 'still busy'),
            (None, True, 'still busy'),
        ]
        for status, retried, fragment in cases:
            with self.subTest(status=status):
                error = LLMError('%s: provider says no' % status, status_code=status)
                script = [error] * (3 if retried else 1)
                with self.fake_llm(*script) as fake:
                    chat, events = self.ask("Hello")
                message = self.assert_turn_completed(chat, events)
                self.assertTrue(message.error)
                self.assertEqual(fake.sleep.call_count, 2 if retried else 0)
                self.assertEqual(events[-2]['type'], 'error')
                self.assertIn(fragment, events[-2]['message'])

    def test_provider_error_after_tools_keeps_the_data(self):
        with self.fake_llm(tool_call('get_kpi_overview'), LLMError('401: key revoked', status_code=401)):
            chat, events = self.ask("KPIs")
        message = self.assert_turn_completed(chat, events)
        self.assertTrue(message.error)
        self.assertEqual([part['type'] for part in message.parts], ['kpis', 'error'])
        self.assertTrue(self.env['ai.accounting.usage'].search_count([('chat_id', '=', chat.id)]))

    def test_unexpected_exception_in_the_loop(self):
        with self.fake_llm(RuntimeError("adapter bug")), \
                mute_logger('odoo.addons.ai_accounting_analytics.models.ai_accounting_chat'):
            chat, events = self.ask("Hello")
        message = self.assert_turn_completed(chat, events)
        self.assertTrue(message.error)
        self.assertNotIn('adapter bug', events[-2]['message'], "Internal details stay in the log")

    # Conversations ----------------------------------------------------------------
    def test_follow_up_after_a_failed_turn(self):
        with self.fake_llm(LLMError('400: bad', status_code=400)):
            chat, _events = self.ask("First")
        with self.fake_llm(answer("Second answer.")) as fake:
            chat, events = self.ask("Second", chat=chat)
        self.assert_turn_completed(chat, events)
        roles = [message['role'] for message in fake.calls[0]['messages']]
        self.assertEqual(roles[-1], 'user')
        self.assertNotIn('', [message.get('content') for message in fake.calls[0]['messages']
                              if message['role'] == 'assistant'], "No empty assistant turn is sent")

    def test_unusual_questions(self):
        for question in ("💰 revenue?", "Quel est mon chiffre d'affaires ?", "ما هو صافي الربح", "x" * 4000,
                         "<script>alert(1)</script>", "'; DROP TABLE account_move; --"):
            with self.subTest(question=question[:20]):
                with self.fake_llm(answer("OK.")):
                    chat, events = self.ask(question)
                self.assert_turn_completed(chat, events)
                self.assertEqual(chat.message_ids.filtered(lambda m: m.role == 'user').content, question)
