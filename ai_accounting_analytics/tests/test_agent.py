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
import json

from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.ai_accounting_analytics.llm import LLMError, LLMResult, ToolCall, Usage

from .common import AiAccountingCommon, answer, tool_call


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestAgent(AiAccountingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.init_invoice('out_invoice', cls.partner_a, '2026-10-05', post=True,
                         amounts=[2500.0], taxes=[])

    def test_tool_round_trip(self):
        with self.fake_llm(tool_call('get_top_partners', kind='customer', period='this_month'),
                           answer("**Partner A** leads.")) as fake:
            chat, events = self.ask("Top customers this month")
        types = [event['type'] for event in events]
        self.assertEqual(types, ['usage', 'step', 'step', 'block', 'delta', 'usage', 'done'])
        # Second call carries the tool result, compact JSON.
        second = fake.calls[1]['messages']
        self.assertEqual(second[-1]['role'], 'tool')
        payload = json.loads(second[-1]['results'][0]['content'])
        self.assertEqual(payload['rows'][0][2], 2500.0)
        self.assertNotIn(' ', second[-1]['results'][0]['content'].split('"')[0])

        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertEqual(message.content, "**Partner A** leads.")
        self.assertEqual([part['type'] for part in message.parts], ['table', 'text'])
        self.assertEqual(len(message.steps), 1)
        self.assertIn('[data]', message.history_digest)
        self.assertEqual(chat.name, "Top customers this month")

    def test_general_question_without_tools(self):
        """Questions outside the books are answered from the model's own
        knowledge in a single call, with no tool step."""
        with self.fake_llm(answer("Accrual accounting records revenue when earned.")) as fake:
            chat, events = self.ask("What is accrual accounting?")
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("own knowledge", fake.calls[0]['system'])
        self.assertNotIn('step', [event['type'] for event in events])
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertEqual(message.content, "Accrual accounting records revenue when earned.")
        self.assertFalse(message.steps)
        self.assertFalse(message.error)

    def test_usage_and_cost_tracking(self):
        with self.fake_llm(tool_call('get_kpi_overview'),
                           answer("Fine.", input_tokens=1000, output_tokens=100, cached_tokens=1000)):
            chat, _events = self.ask("How are we doing?")
        usages = self.env['ai.accounting.usage'].search([('chat_id', '=', chat.id)], order='step')
        self.assertEqual(usages.mapped('step'), [1, 2])
        self.assertEqual(usages[1].total_tokens, 2100)
        # gemini-3.5-flash-lite seed prices: 0.30 in, 0.03 cached, 2.50 out per million.
        expected = (1000 * 0.30 + 1000 * 0.03 + 100 * 2.50) / 1_000_000
        self.assertAlmostEqual(usages[1].cost, expected, places=9)
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertAlmostEqual(message.cost, sum(usages.mapped('cost')), places=9)
        self.assertAlmostEqual(chat.total_cost, message.cost, places=9)

    def test_provider_reported_cost_wins(self):
        result = answer("Hi.")
        result.usage.cost = 0.42
        with self.fake_llm(result):
            chat, _events = self.ask("Hello")
        self.assertAlmostEqual(chat.total_cost, 0.42)

    def test_history_uses_digests_not_raw_tool_data(self):
        with self.fake_llm(tool_call('get_top_partners', kind='customer'), answer("A leads.")):
            chat, _events = self.ask("Top customers")
        with self.fake_llm(answer("Yes.")) as fake:
            self.ask("Is that good?", chat=chat)
        messages = fake.calls[0]['messages']
        self.assertEqual([m['role'] for m in messages], ['user', 'assistant', 'user'])
        self.assertIn('A leads.', messages[1]['content'])
        self.assertIn('[data]', messages[1]['content'])
        self.assertNotIn('tool_calls', messages[1])

    def test_history_turns_setting(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.history_turns', 0)
        with self.fake_llm(answer("One.")):
            chat, _events = self.ask("First")
        with self.fake_llm(answer("Two.")) as fake:
            self.ask("Second", chat=chat)
        self.assertEqual(len(fake.calls[0]['messages']), 1)

    def test_last_step_forces_an_answer(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.max_steps', 2)
        with self.fake_llm(tool_call('get_kpi_overview'), answer("Done.")) as fake:
            self.ask("Overview")
        self.assertEqual([call['allow_tools'] for call in fake.calls], [True, False])
        self.assertTrue(fake.calls[1]['tools'], "Tools stay declared to keep the cached prefix")

    def test_thinking_aloud_is_kept_out_of_the_answer(self):
        planning = tool_call('get_kpi_overview')
        planning.text = "Let me check the figures first."
        with self.fake_llm(planning, answer("All good.")):
            chat, events = self.ask("How are we doing?")
        self.assertIn('rewind', [event['type'] for event in events])
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertEqual(message.content, "All good.")
        self.assertEqual(message.steps[0]['note'], "Let me check the figures first.")

    def test_last_step_is_told_to_conclude(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.max_steps', 2)
        with self.fake_llm(tool_call('get_kpi_overview'), answer("Done.")) as fake:
            self.ask("Overview")
        self.assertNotIn('No more tool calls', str(fake.calls[0]['messages']))
        last = fake.calls[1]['messages'][-1]
        self.assertEqual(last['role'], 'user')
        self.assertIn('No more tool calls', last['content'])

    def test_answer_is_completed_when_model_stops_after_tools(self):
        with self.fake_llm(tool_call('get_kpi_overview'), answer(""), answer("Here is the summary.")) as fake:
            chat, _events = self.ask("Overview")
        self.assertEqual(len(fake.calls), 3)
        self.assertFalse(fake.calls[2]['allow_tools'])
        self.assertIn('own knowledge', fake.calls[2]['messages'][-1]['content'])
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertEqual(message.content, "Here is the summary.")
        self.assertEqual(self.env['ai.accounting.usage'].search_count([('chat_id', '=', chat.id)]), 3)

    def test_tool_failure_is_completed_with_ai_help(self):
        """A failing tool is reported to the model, which then answers with
        what it has and its own knowledge (prompted to do so)."""
        with self.fake_llm(tool_call('query_records', model='res.users'),
                           answer("Users cannot be queried here; open Settings > Users.")) as fake:
            chat, _events = self.ask("How many users?")
        self.assertIn('do not stop at the error', fake.calls[0]['system'])
        tool_result = fake.calls[1]['messages'][-1]['results'][0]
        self.assertTrue(tool_result['is_error'])
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertFalse(message.error)
        self.assertIn('Settings', message.content)

    def test_failed_step_keeps_its_error(self):
        with self.fake_llm(tool_call('query_records', model='res.users'), answer("Not possible.")):
            chat, _events = self.ask("List users")
        step = chat.message_ids.filtered(lambda m: m.role == 'assistant').steps[0]
        self.assertFalse(step['ok'])
        self.assertTrue(step['error'])

    def test_parallel_tool_calls_in_one_step(self):
        result = LLMResult(tool_calls=[
            ToolCall(id='1', name='get_kpi_overview', arguments={}),
            ToolCall(id='2', name='get_cash_balances', arguments={}),
        ], usage=Usage(input_tokens=10, output_tokens=10))
        with self.fake_llm(result, answer("Both.")) as fake:
            chat, _events = self.ask("KPIs and cash")
        self.assertEqual(len(fake.calls[1]['messages'][-1]['results']), 2)
        self.assertEqual(len(chat.message_ids.filtered(lambda m: m.role == 'assistant').steps), 2)

    def test_invalid_tool_arguments(self):
        result = LLMResult(tool_calls=[ToolCall(id='1', name='get_kpi_overview',
                                                invalid_arguments=True)],
                           usage=Usage())
        with self.fake_llm(result, answer("Sorry.")) as fake:
            self.ask("KPIs")
        tool_result = fake.calls[1]['messages'][-1]['results'][0]
        self.assertTrue(tool_result['is_error'])

    def test_provider_error_is_reported(self):
        with self.fake_llm(LLMError("401: API key not valid", status_code=401)):
            chat, events = self.ask("Hello")
        self.assertEqual(events[-2], {'type': 'error', 'message': '401: API key not valid'})
        self.assertEqual(events[-1]['type'], 'done')
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertTrue(message.error)

    def test_busy_provider_is_retried(self):
        busy = LLMError("503: high demand", status_code=503)
        with self.fake_llm(busy, answer("Done.")) as fake:
            chat, events = self.ask("Hello")
        types = [event['type'] for event in events]
        self.assertIn('retry', types)
        self.assertNotIn('error', types)
        fake.sleep.assert_called_once_with(2)
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertFalse(message.error)
        self.assertEqual(message.content, "Done.")

    def test_retry_after_header_is_honoured(self):
        busy = LLMError("429: slow down", status_code=429, retry_after=7.0)
        with self.fake_llm(busy, answer("Done.")) as fake:
            self.ask("Hello")
        fake.sleep.assert_called_once_with(7.0)

    def test_mid_stream_failure_rewinds_partial_text(self):
        busy = LLMError("503: high demand", status_code=503)
        with self.fake_llm(tool_call('get_top_partners', kind='customer'),
                           ('partial', "Acme heavily", busy),
                           answer("Acme leads.")):
            chat, events = self.ask("Top customers")
        rewind = next(event for event in events if event['type'] == 'rewind')
        self.assertEqual([part['type'] for part in rewind['parts']], ['table'])
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        self.assertEqual(message.content, "Acme leads.")
        self.assertEqual([part['type'] for part in message.parts], ['table', 'text'])

    def test_permanent_errors_are_not_retried(self):
        with self.fake_llm(LLMError("400: bad request", status_code=400)) as fake:
            _chat, events = self.ask("Hello")
        self.assertNotIn('retry', [event['type'] for event in events])
        fake.sleep.assert_not_called()

    def test_retries_exhausted(self):
        busy = LLMError("503: high demand", status_code=503)
        with self.fake_llm(busy, busy, busy) as fake:
            _chat, events = self.ask("Hello")
        self.assertEqual(fake.sleep.call_count, 2)
        self.assertIn('switch to another model', events[-2]['message'])

    def test_retired_model_hint(self):
        with self.fake_llm(LLMError("404: model not found", status_code=404)):
            _chat, events = self.ask("Hello")
        self.assertIn('Fetch Models', events[-2]['message'])
        self.assertIn('gemini-3.5-flash-lite', events[-2]['message'])

    def test_export_report_from_stored_message(self):
        with self.fake_llm(tool_call('get_profit_and_loss', period='this_month'), answer("Profit.")):
            chat, _events = self.ask("P&L this month")
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        index = next(i for i, part in enumerate(message.parts) if part.get('export'))
        action = chat.ai_export(message.id, index, 'xlsx')
        self.assertEqual(action['report_type'], 'xlsx')
        action = chat.ai_export(message.id, index, 'pdf')
        self.assertEqual(action['type'], 'ir.actions.report')

    def test_bootstrap(self):
        data = self.Chat.ai_get_bootstrap()
        self.assertTrue(data['consent'])
        self.assertEqual(data['default_model_id'], self.ai_model.id)
        gemini = next(model for model in data['models'] if model['id'] == self.ai_model.id)
        self.assertTrue(gemini['has_key'])

    def test_model_picker_lists_only_usable_models(self):
        """Only models of providers the user has an API key for are offered."""
        gemini_models = self.env['ai.accounting.model'].search([('provider_id', '=', self.provider.id)])
        data = self.Chat.ai_get_bootstrap()
        self.assertEqual({model['id'] for model in data['models']}, set(gemini_models.ids))
        self.assertTrue(all(model['has_key'] for model in data['models']))

        # A key for another provider adds its models.
        openai = self.env.ref('ai_accounting_analytics.provider_openai')
        self.env['ai.accounting.api.key'].create({'provider_id': openai.id, 'new_api_key': 'sk-test-1234567890'})
        data = self.Chat.ai_get_bootstrap()
        self.assertEqual({model['id'] for model in data['models']},
                         set((gemini_models | openai.model_ids).ids))

        # Archived models are not offered.
        archived = openai.model_ids[:1]
        archived.active = False
        self.assertNotIn(archived.id, [model['id'] for model in self.Chat.ai_get_bootstrap()['models']])

    def test_model_picker_without_any_key(self):
        """Without a key, only the default model is shown (with the prompt
        to add a key)."""
        self.env['ai.accounting.api.key'].search([('user_id', '=', self.env.uid)]).unlink()
        data = self.Chat.ai_get_bootstrap()
        self.assertEqual([model['id'] for model in data['models']], [data['default_model_id']])
        self.assertFalse(data['models'][0]['has_key'])
