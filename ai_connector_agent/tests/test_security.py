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
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.ai_connector_agent.controllers.ai_connector_agent import (
    AiChatController,
)

from .common import CONTROLLER_PATH, AiConnectorCommon, make_response


@tagged('post_install', '-at_install', 'ai_connector_agent')
class TestSecurity(AiConnectorCommon):
    """Run as a plain internal user to exercise ACLs and record rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref('base.user_admin')
        cls.own_session = cls._make_own_session(cls.other_user)
        cls.admin_session = cls._make_own_session(cls.admin)

    @classmethod
    def _make_own_session(cls, user):
        return cls.Session.create({
            'name': 'Session of %s' % user.login,
            'ai_agent_id': cls.provider.id,
            'ai_model_id': cls.model_a.id,
            'user_id': user.id,
        })

    # ---- api key / provider access ---------------------------------------
    def test_internal_user_cannot_read_api_key(self):
        provider = self.provider.with_user(self.other_user)
        with self.assertRaises(AccessError):
            provider.read(['api_key'])

    def test_internal_user_can_read_provider_name(self):
        provider = self.provider.with_user(self.other_user)
        self.assertEqual(provider.name, 'OpenAI Test')

    def test_admin_can_read_api_key(self):
        provider = self.provider.with_user(self.admin)
        self.assertEqual(provider.api_key, 'sk-test')

    def test_internal_user_cannot_write_or_create_provider(self):
        provider = self.provider.with_user(self.other_user)
        with self.assertRaises(AccessError):
            provider.write({'name': 'Hacked'})
        with self.assertRaises(AccessError):
            self.Provider.with_user(self.other_user).create({
                'name': 'X', 'api_key': 'k', 'api_base_url': 'https://x.com'})

    def test_internal_user_cannot_write_model(self):
        with self.assertRaises(AccessError):
            self.model_a.with_user(self.other_user).write({'version': '9'})

    # ---- record rules -----------------------------------------------------
    def test_user_only_searches_own_sessions(self):
        found = self.Session.with_user(self.other_user).search([])
        self.assertIn(self.own_session, found)
        self.assertNotIn(self.admin_session, found)

    def test_user_cannot_read_foreign_session(self):
        foreign = self.admin_session.with_user(self.other_user)
        with self.assertRaises(AccessError):
            foreign.read(['name'])

    def test_user_cannot_delete_foreign_session(self):
        foreign = self.admin_session.with_user(self.other_user)
        with self.assertRaises(AccessError):
            foreign.unlink()

    def test_user_only_sees_messages_of_own_sessions(self):
        own_msg = self._add_message(self.own_session, 'user', 'mine')
        foreign_msg = self._add_message(self.admin_session, 'user', 'theirs')
        found = self.Message.with_user(self.other_user).search([])
        self.assertIn(own_msg, found)
        self.assertNotIn(foreign_msg, found)

    def test_user_can_create_message_in_own_session_only(self):
        Message = self.Message.with_user(self.other_user)
        msg = Message.create({
            'session_id': self.own_session.id,
            'message_type': 'user',
            'content': 'ok',
        })
        self.assertTrue(msg.exists())
        with self.assertRaises(AccessError):
            Message.create({
                'session_id': self.admin_session.id,
                'message_type': 'user',
                'content': 'not ok',
            })

    # ---- controller works for a non-admin user ---------------------------
    def test_ai_call_reads_api_key_as_internal_user(self):
        """The key is read with sudo, so normal users can still chat."""
        controller = AiChatController()
        session = self.own_session.with_user(self.other_user)
        model = self.model_a.with_user(self.other_user)
        ok = make_response(200, {'choices': [{'message': {'content': 'hi'}}]})
        with patch('%s.requests.post' % CONTROLLER_PATH, return_value=ok) as post:
            res = controller._call_openai_api('hello', model, session)
        self.assertEqual(res, 'hi')
        self.assertEqual(
            post.call_args.kwargs['headers']['Authorization'], 'Bearer sk-test')
