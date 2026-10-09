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
"""Stopping an answer, saving it as it goes and keeping it within the
server's time limit."""
import threading
import time
from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.ai_accounting_analytics.llm import LLMError, LLMResult, ToolCall, Usage
from odoo.addons.ai_accounting_analytics.models.ai_accounting_chat import FINAL_CALL_RESERVE, MIN_CALL_TIME

from .common import AiAccountingDataCommon, answer, tool_call


@tagged('post_install', '-at_install')
class TestTurnControl(AiAccountingDataCommon):

    def start(self, question="Overview"):
        chat, message = self.Chat._ai_prepare_turn(question)
        return chat, message

    def assistant(self, chat):
        return chat.message_ids.filtered(lambda message: message.role == 'assistant')

    def test_stop_between_tools(self):
        """Stop pressed while tools run: the next tool does not run, what was
        shown is kept, and no further AI call is made."""
        two_tools = LLMResult(tool_calls=[ToolCall(id='1', name='get_kpi_overview', arguments={}),
                                          ToolCall(id='2', name='get_cash_balances', arguments={})],
                              usage=Usage(input_tokens=10, output_tokens=10))
        cancel = threading.Event()
        with self.fake_llm(two_tools) as fake:
            chat, message = self.start()
            events = []
            for event in chat._ai_run_turn(message, cancel=cancel):
                events.append(event)
                if event['type'] == 'step' and event['status'] == 'done':
                    cancel.set()
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(events[-1]['type'], 'done')
        self.assertEqual(events[-2], {'type': 'error', 'message': 'Stopped.'})
        assistant = self.assistant(chat)
        self.assertTrue(assistant.error, "A stopped answer is left out of the history")
        self.assertEqual([part['type'] for part in assistant.parts], ['kpis', 'error'])
        self.assertEqual(len(assistant.steps), 1)

    def test_stop_while_streaming(self):
        cancel = threading.Event()
        with self.fake_llm(answer("Revenue grew by")):
            chat, message = self.start()
            for event in chat._ai_run_turn(message, cancel=cancel):
                if event['type'] == 'delta':
                    cancel.set()
        assistant = self.assistant(chat)
        self.assertEqual(assistant.content, "Revenue grew by", "The text already shown is kept")
        self.assertEqual(assistant.parts[-1], {'type': 'error', 'text': 'Stopped.'})

    def test_answer_is_saved_after_every_ai_call(self):
        """If the request dies (closed page, killed worker), the answer keeps
        what the user saw up to the last AI call."""
        with self.fake_llm(tool_call('get_top_partners', kind='customer'), answer("Partner A leads.")):
            chat, message = self.start("Top customers")
            turn = chat._ai_run_turn(message)
            usages = 0
            for event in turn:
                if event['type'] == 'usage':
                    usages += 1
                    if usages == 2:
                        break
            turn.close()  # the request is gone before the end of the turn
        assistant = self.assistant(chat)
        self.assertEqual([part['type'] for part in assistant.parts], ['table', 'text'])
        self.assertEqual(assistant.content, "Partner A leads.")
        self.assertEqual(len(assistant.steps), 1)
        self.assertTrue(assistant.cost)

    def test_short_time_left_means_answer_now(self):
        """Close to the deadline, the AI is not offered another tool round."""
        deadline = time.monotonic() + FINAL_CALL_RESERVE + MIN_CALL_TIME - 3
        with self.fake_llm(answer("Quick answer.")) as fake:
            chat, message = self.start()
            list(chat._ai_run_turn(message, deadline=deadline))
        self.assertFalse(fake.calls[0]['allow_tools'])
        self.assertLessEqual(fake.calls[0]['read_timeout'], FINAL_CALL_RESERVE + MIN_CALL_TIME)
        self.assertEqual(self.assistant(chat).content, "Quick answer.")

    def test_tool_rounds_stop_before_the_deadline(self):
        """A tool round that eats the spare time makes the next call the
        concluding one."""
        original = type(self.toolkit)._ai_tool_get_kpi_overview

        def slow_tool(toolkit, arguments):
            threading.Event().wait(1.0)
            return original(toolkit, arguments)

        deadline = time.monotonic() + FINAL_CALL_RESERVE + MIN_CALL_TIME + 0.5
        with self.fake_llm(tool_call('get_kpi_overview'), answer("Done.")) as fake, \
                patch.object(type(self.toolkit), '_ai_tool_get_kpi_overview', slow_tool):
            chat, message = self.start()
            list(chat._ai_run_turn(message, deadline=deadline))
        self.assertEqual([call['allow_tools'] for call in fake.calls], [True, False])
        self.assertIn('No more tool calls', fake.calls[1]['messages'][-1]['content'])
        self.assertEqual(self.assistant(chat).content, "Done.")

    def test_deadline_passed(self):
        with self.fake_llm() as fake:
            chat, message = self.start()
            events = list(chat._ai_run_turn(message, deadline=time.monotonic() - 1))
        self.assertFalse(fake.calls)
        self.assertIn('limit_time_real', events[-2]['message'])
        self.assertTrue(self.assistant(chat).error)

    def test_no_retry_beyond_the_deadline(self):
        busy = LLMError("503: high demand", status_code=503)
        with self.fake_llm(busy) as fake:
            chat, message = self.start()
            events = list(chat._ai_run_turn(message, deadline=time.monotonic() + MIN_CALL_TIME + 1))
        fake.sleep.assert_not_called()
        self.assertNotIn('retry', [event['type'] for event in events])
        self.assertTrue(self.assistant(chat).error)

    def test_stop_during_a_retry_wait(self):
        """The wait before a retry ends as soon as Stop is pressed."""
        busy = LLMError("503: high demand", status_code=503)
        cancel = threading.Event()
        with self.fake_llm(busy) as fake:
            chat, message = self.start()
            started = time.monotonic()
            events = []
            for event in chat._ai_run_turn(message, cancel=cancel):
                events.append(event)
                if event['type'] == 'retry':
                    cancel.set()
        self.assertLess(time.monotonic() - started, 2, "No 2 s wait once stopped")
        fake.sleep.assert_not_called()
        self.assertEqual(events[-2], {'type': 'error', 'message': 'Stopped.'})
