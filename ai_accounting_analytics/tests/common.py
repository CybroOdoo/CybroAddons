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
"""Shared fixtures: an accounting company (``AccountTestInvoicingCommon``)
whose test user is a Chief Accountant, plus a scripted fake LLM adapter so the
agent loop runs without network access."""
import json
import threading
from contextlib import contextmanager
from unittest.mock import patch

from odoo import fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.ai_accounting_analytics.llm import ADAPTERS, LLMResult, ToolCall, Usage


class FakeAdapter:
    """Replays ``script``: a list of LLMResult (or Exception) per call and
    records every request it receives."""
    script = []
    calls = []

    def __init__(self, api_key, model, base_url=None, max_tokens=1024, extra_params=None):
        self.api_key = api_key
        self.model = model

    def stream(self, system, messages, tools, allow_tools=True):
        FakeAdapter.calls.append({
            'system': system, 'messages': [dict(m) for m in messages],
            'tools': tools, 'allow_tools': allow_tools,
            'read_timeout': getattr(self, 'read_timeout', None),
        })
        result = FakeAdapter.script.pop(0)
        if isinstance(result, tuple) and result[0] == 'slow':  # ('slow', seconds, result)
            threading.Event().wait(result[1])
            result = result[2]
        if isinstance(result, tuple) and result[0] == 'nodone':  # stream cut without a result
            if result[1]:
                yield 'text', result[1]
            return
        if isinstance(result, tuple):  # ('partial', text, error): fails mid-stream
            _kind, text, error = result
            yield 'text', text
            raise error
        if isinstance(result, Exception):
            raise result
        if result.text:
            yield 'text', result.text
        yield 'done', result

    def list_models(self):
        return [{'technical_name': 'fake-model', 'name': 'Fake', 'price_input': 1.0,
                 'price_output': 2.0, 'price_cached': None}]


def tool_call(name, **arguments):
    return LLMResult(tool_calls=[ToolCall(id='call_%s' % name, name=name, arguments=arguments)],
                     usage=Usage(input_tokens=1000, output_tokens=50))


def answer(text, input_tokens=1200, output_tokens=80, cached_tokens=0):
    return LLMResult(text=text, usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens,
                                            cached_tokens=cached_tokens))


class AiAccountingMixin:

    @classmethod
    def _setup_ai_accounting(cls):
        cls.chief_group = cls.env.ref('base_accounting_kit.group_account_chief')
        cls.env.user.group_ids |= cls.chief_group
        cls.provider = cls.env.ref('ai_accounting_analytics.provider_gemini')
        cls.ai_model = cls.env.ref('ai_accounting_analytics.model_gemini_flash_lite')
        cls.env['ai.accounting.api.key'].create({
            'provider_id': cls.provider.id, 'new_api_key': 'AIza-test-key-123456',
        })
        cls.env.user.sudo().ai_accounting_consent_date = fields.Datetime.now()
        cls.Chat = cls.env['ai.accounting.chat']
        cls.toolkit = cls.env['ai.accounting.toolkit']

    @contextmanager
    def fake_llm(self, *script):
        FakeAdapter.script = list(script)
        FakeAdapter.calls = []
        with patch.dict(ADAPTERS, {'gemini': FakeAdapter}), \
                patch('odoo.addons.ai_accounting_analytics.models.ai_accounting_chat.time.sleep') as sleep:
            FakeAdapter.sleep = sleep
            yield FakeAdapter
        self.assertFalse(FakeAdapter.script, "Every scripted AI call should be consumed")

    def ask(self, question, chat=None):
        chat, message = self.Chat._ai_prepare_turn(question, chat_id=chat.id if chat else None)
        events = list(chat._ai_run_turn(message))
        return chat, events


class AiAccountingCommon(AiAccountingMixin, AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_ai_accounting()


NUMERIC_COLUMNS = ('monetary', 'number', 'percent')
COLUMN_TYPES = ('text', 'date', *NUMERIC_COLUMNS)


class AiAccountingDataCommon(AiAccountingCommon):
    """A small but complete set of books (frozen at 2026-10-15): customer
    invoices over two months (one overdue), a credit note, a vendor bill, a
    customer payment and an unreconciled bank line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.partner_a + cls.partner_b).customer_rank = 1
        cls.partner_b.supplier_rank = 1
        cls.partner_a.country_id = cls.env.ref('base.be')
        cls.partner_b.country_id = cls.env.ref('base.us')
        cls.inv_a = cls._invoice('out_invoice', cls.partner_a, '2026-10-05', '2026-10-10', amount=3000.0)
        cls.inv_b = cls._invoice('out_invoice', cls.partner_b, '2026-10-06', '2026-11-30',
                                 products=cls.product_a)
        cls.inv_sep = cls._invoice('out_invoice', cls.partner_a, '2026-09-10', '2026-09-10', amount=500.0)
        cls.refund = cls._invoice('out_refund', cls.partner_a, '2026-10-08', '2026-10-08', amount=100.0)
        cls.bill = cls._invoice('in_invoice', cls.partner_b, '2026-10-07', '2026-11-30', amount=400.0)
        cls.payment = cls.env['account.payment'].create({
            'payment_type': 'inbound', 'partner_type': 'customer', 'partner_id': cls.partner_b.id,
            'amount': 200.0, 'date': '2026-10-09',
            'journal_id': cls.company_data['default_journal_bank'].id})
        cls.payment.action_post()
        cls.env['account.bank.statement.line'].create({
            'journal_id': cls.company_data['default_journal_bank'].id, 'date': '2026-10-10',
            'payment_ref': 'Transfer X', 'amount': 250.0})

    @classmethod
    def _invoice(cls, move_type, partner, invoice_date, due_date, amount=None, products=None):
        move = cls.init_invoice(move_type, partner, invoice_date, taxes=[],
                                amounts=[amount] if amount else None, products=products)
        move.write({'invoice_payment_term_id': False, 'invoice_date_due': due_date})
        move.invoice_line_ids.tax_ids = False
        move.action_post()
        return move

    # ------------------------------------------------------------------
    # Output contract
    # ------------------------------------------------------------------
    def assert_tool_contract(self, output, context=''):
        """What every tool output must look like, whatever the arguments:
        the client and the agent loop rely on it."""
        self.assertIsInstance(output, dict, context)
        for key in ('model', 'blocks', 'digest', 'label', 'ms'):
            self.assertIn(key, output, context)
        self.assertFalse(output.get('internal'), "Unexpected tool failure: %s %s" % (context, output['model']))
        payload = self.toolkit._ai_dump(output['model'])
        json.loads(payload)
        self.assertLess(len(payload), 20000, "Tool payloads must stay compact: %s" % context)
        self.assertIsInstance(output['label'], str, context)
        self.assertIsInstance(output['digest'], str, context)
        if output.get('error'):
            message = output['model']['error']
            self.assertIsInstance(message, str, context)
            self.assertTrue(message.strip(), context)
            self.assertLess(len(message), 1500, context)
            self.assertNotIn('Traceback', message, context)
            self.assertEqual(output['blocks'], [], context)
            return
        for block in output['blocks']:
            self.assert_block_contract(block, context)
        json.loads(self.toolkit._ai_dump(output['blocks']))

    def assert_block_contract(self, block, context=''):
        self.assertIn(block['type'], ('table', 'chart', 'kpis'), context)
        if block['type'] == 'table':
            self.assertTrue(all(column['type'] in COLUMN_TYPES for column in block['columns']), context)
            for row in block['rows']:
                self.assertEqual(len(row['cells']), len(block['columns']), "%s %s" % (context, row))
                for cell, column in zip(row['cells'], block['columns']):
                    if column['type'] in NUMERIC_COLUMNS:
                        self.assertTrue(cell is None or cell == '' or isinstance(cell, (int, float)),
                                        "%s: %r in a %s column" % (context, cell, column['type']))
        elif block['type'] == 'chart':
            self.assertIn(block['chart_type'], ('bar', 'line', 'pie'), context)
            self.assertTrue(all(isinstance(label, str) for label in block['labels']), context)
            for dataset in block['datasets']:
                self.assertEqual(len(dataset['data']), len(block['labels']), context)
        else:
            for item in block['items']:
                self.assertTrue(item['value'] is None or isinstance(item['value'], (int, float)), context)
