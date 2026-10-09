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
"""The streaming endpoint: events relayed from the answer thread,
keep-alive pings, the time budget and stopping when the page goes away."""
import json
import queue
import threading
import time
from unittest.mock import patch

from odoo.tests import BaseCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon
from odoo.addons.ai_accounting_analytics.controllers import chat as chat_controller

from .common import AiAccountingMixin, answer, tool_call

URL = '/ai_accounting_analytics/chat/stream'


@tagged('post_install', '-at_install')
class TestChatStream(AiAccountingMixin, AccountTestInvoicingHttpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ai_accounting()

    def post(self, question="Top customers"):
        self.authenticate(self.env.user.login, self.env.user.login)
        response = self.url_open(URL, data={'question': question, 'csrf_token': self.csrf_token()}, timeout=60)
        self.assertEqual(response.status_code, 200)
        return [json.loads(line) for line in response.text.splitlines() if line.strip()]

    def test_events_are_streamed_and_stored(self):
        with self.fake_llm(tool_call('get_top_partners', kind='customer'), answer("Partner A leads.")):
            events = self.post()
        types = [event['type'] for event in events]
        self.assertEqual(types[0], 'start')
        self.assertEqual(types[-1], 'done')
        self.assertIn('block', types)
        chat = self.env['ai.accounting.chat'].browse(events[0]['chat']['id'])
        self.assertEqual(chat.message_ids.mapped('role'), ['user', 'assistant'])
        self.assertEqual(chat.message_ids[1].content, "Partner A leads.")

    def test_pings_while_the_provider_is_silent(self):
        with patch.object(chat_controller, 'HEARTBEAT_SECONDS', 0.1), \
                self.fake_llm(('slow', 0.6, answer("Finally."))):
            events = self.post("Hello")
        types = [event['type'] for event in events]
        self.assertIn('ping', types)
        self.assertEqual(types[-1], 'done')

    def test_error_before_the_answer(self):
        self.env.user.sudo().ai_accounting_consent_date = False
        events = self.post("Hello")
        self.assertEqual([event['type'] for event in events], ['error'])
        self.assertIn('data sharing notice', events[0]['message'])

    def test_answer_gets_the_time_budget(self):
        captured = {}

        def fake_run(dbname, uid, context, chat_id, message_id, events, cancel, deadline):
            captured['deadline'] = deadline
            events.put(None)

        with patch.object(chat_controller, 'run_answer', fake_run), \
                patch.object(chat_controller, 'config', {'limit_time_real': 120}):
            before = time.monotonic()
            self.post("Hello")
        self.assertAlmostEqual(captured['deadline'] - before, 120 - chat_controller.TIME_LIMIT_MARGIN, delta=5)


@tagged('-at_install', 'post_install')
class TestRelay(BaseCase):

    def test_closed_page_stops_the_answer(self):
        """The response generator is closed when the browser goes away: the
        answer thread is told to stop."""
        events, cancel = queue.Queue(), threading.Event()

        def answer_thread():
            events.put({'type': 'start'})
            cancel.wait(5)
            events.put(None)

        relay = chat_controller.relay_events(threading.Thread(target=answer_thread, daemon=True), events, cancel)
        self.assertEqual(json.loads(next(relay)), {'type': 'start'})
        self.assertFalse(cancel.is_set())
        relay.close()  # what the server does when writing to the browser fails
        self.assertTrue(cancel.is_set())

    def test_pings_and_end(self):
        events, cancel = queue.Queue(), threading.Event()

        def answer_thread():
            threading.Event().wait(0.35)
            events.put({'type': 'done'})
            events.put(None)

        with patch.object(chat_controller, 'HEARTBEAT_SECONDS', 0.1):
            lines = [json.loads(line) for line in chat_controller.relay_events(
                threading.Thread(target=answer_thread, daemon=True), events, cancel)]
        self.assertIn({'type': 'ping'}, lines)
        self.assertEqual(lines[-1], {'type': 'done'})
        self.assertTrue(cancel.is_set())
