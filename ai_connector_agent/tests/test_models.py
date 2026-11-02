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
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import AiConnectorCommon


@tagged('post_install', '-at_install', 'ai_connector_agent')
class TestAiModels(AiConnectorCommon):

    # ---- ai.model ---------------------------------------------------------
    def test_ai_model_create_and_rec_name(self):
        model = self.Model.create({
            'model_ref_id': 'gpt-x',
            'display_label': 'GPT X',
            'version': '1',
            'owned_by': 'openai',
        })
        self.assertEqual(model.display_name, 'gpt-x')
        self.assertEqual(model.owned_by, 'openai')

    # ---- ai.provider ------------------------------------------------------
    def test_provider_create(self):
        self.assertEqual(self.provider.name, 'OpenAI Test')
        self.assertEqual(len(self.provider.ai_model_ids), 2)

    # ---- ai.chat.session --------------------------------------------------
    def test_get_or_create_session_creates_new(self):
        session = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        self.assertTrue(session.exists())
        self.assertEqual(session.user_id, self.env.user)
        self.assertTrue(session.is_active)
        self.assertIn('OpenAI Test', session.name)
        self.assertIn('test-model-a', session.name)

    def test_get_or_create_session_reuses_existing(self):
        first = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        second = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        self.assertEqual(first, second)

    def test_get_or_create_session_other_model_creates_new(self):
        first = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        second = self.Session.get_or_create_session(
            self.provider.id, self.model_b.id)
        self.assertNotEqual(first, second)

    def test_get_or_create_session_explicit_user(self):
        session = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id, user_id=self.other_user.id)
        self.assertEqual(session.user_id, self.other_user)

    def test_get_or_create_session_ignores_inactive(self):
        first = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        first.is_active = False
        second = self.Session.get_or_create_session(
            self.provider.id, self.model_a.id)
        self.assertNotEqual(first, second)

    # ---- ai.chat.message --------------------------------------------------
    def test_message_create_updates_last_message_date(self):
        session = self._make_session()
        self.assertFalse(session.last_message_date)
        ts = fields.Datetime.now() - timedelta(days=1)
        msg = self.Message.create({
            'session_id': session.id,
            'message_type': 'user',
            'content': 'hi',
            'timestamp': ts,
        })
        self.assertEqual(session.last_message_date, msg.timestamp)

    def test_message_create_multi(self):
        session = self._make_session()
        msgs = self.Message.create([
            {'session_id': session.id, 'message_type': 'user', 'content': 'a'},
            {'session_id': session.id, 'message_type': 'ai', 'content': 'b'},
        ])
        self.assertEqual(len(msgs), 2)
        self.assertEqual(len(session.message_ids), 2)
        self.assertTrue(session.last_message_date)

    def test_message_cascade_on_session_delete(self):
        session = self._make_session()
        msg = self._add_message(session)
        session.unlink()
        self.assertFalse(msg.exists())

    def test_message_defaults(self):
        msg = self._add_message(self._make_session())
        self.assertTrue(msg.timestamp)
        self.assertEqual(msg.user_id, self.env.user)

    # ---- res.users --------------------------------------------------------
    def test_user_active_ai_fields(self):
        user = self.other_user
        user.write({
            'active_ai_agent_id': self.provider.id,
            'active_ai_model_id': self.model_a.id,
        })
        self.assertEqual(user.active_ai_agent_id, self.provider)
        self.assertEqual(user.active_ai_model_id, self.model_a)
