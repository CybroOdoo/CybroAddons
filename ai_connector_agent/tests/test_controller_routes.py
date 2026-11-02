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
from unittest.mock import MagicMock, PropertyMock, patch

from odoo.tests import tagged

from odoo.addons.ai_connector_agent.controllers.ai_connector_agent import (
    AiChatController,
)

from .common import CONTROLLER_PATH, PNG_B64, AiConnectorCommon


@tagged('post_install', '-at_install', 'ai_connector_agent')
class TestControllerRoutes(AiConnectorCommon):
    """Call the controller methods directly with a patched ``request``."""

    def setUp(self):
        super().setUp()
        self.controller = AiChatController()
        # `request` is a werkzeug LocalProxy: pass `new=` so mock does not
        # try to introspect the unbound proxy.
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        patcher = patch('%s.request' % CONTROLLER_PATH, new=self.mock_request)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Never hit the network from route tests
        ai_patcher = patch.object(
            AiChatController, '_get_ai_response', return_value='AI says hi')
        self.mock_ai = ai_patcher.start()
        self.addCleanup(ai_patcher.stop)

    def _send(self, **kw):
        kw.setdefault('message', 'Hello')
        kw.setdefault('ai_agent_id', self.provider.id)
        kw.setdefault('ai_model_id', self.model_a.id)
        return self.controller.send_message(**kw)

    # ---- send_message -----------------------------------------------------
    def test_send_message_success_creates_session_and_messages(self):
        res = self._send()
        self.assertTrue(res['success'])
        session = self.Session.browse(res['session_id'])
        self.assertEqual(len(session.message_ids), 2)
        self.assertEqual(res['user_message']['content'], 'Hello')
        self.assertEqual(res['ai_message']['content'], 'AI says hi')
        self.assertTrue(res['user_message']['timestamp'].endswith('Z'))
        self.assertEqual(res['user_message']['attachments'], [])

    def test_send_message_uses_given_session(self):
        session = self._make_session()
        res = self._send(session_id=session.id)
        self.assertEqual(res['session_id'], session.id)

    def test_send_message_unknown_session_falls_back(self):
        res = self._send(session_id=999999999)
        self.assertTrue(res['success'])

    def test_send_message_invalid_ids(self):
        res = self._send(ai_agent_id='abc')
        self.assertEqual(res, {'error': 'Invalid agent or model ID'})

    def test_send_message_missing_ids(self):
        res = self._send(ai_agent_id=0)
        self.assertEqual(res, {'error': 'Missing required parameters'})

    def test_send_message_missing_message_and_attachments(self):
        res = self._send(message='   ')
        self.assertIn('provide a message or attachment', res['error'])

    def test_send_message_access_denied_for_foreign_session(self):
        foreign = self._make_session(user=self.other_user)
        res = self._send(session_id=foreign.id)
        self.assertEqual(res, {'error': 'Access denied'})

    def test_send_message_with_attachment_only(self):
        res = self._send(message='', attachments=[
            {'name': 'pic.png', 'data': 'data:image/png;base64,%s' % PNG_B64},
        ])
        self.assertTrue(res['success'])
        atts = res['user_message']['attachments']
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]['name'], 'pic.png')
        self.assertTrue(atts[0]['url'].startswith('/web/content/'))
        attachment = self.env['ir.attachment'].browse(atts[0]['id'])
        self.assertEqual(attachment.res_model, 'ai.chat.message')
        self.assertEqual(attachment.res_id, res['user_message']['id'])

    def test_send_message_attachment_without_prefix_and_without_data(self):
        res = self._send(attachments=[
            {'name': 'raw.png', 'data': PNG_B64},
            {'name': 'empty.png'},
        ])
        self.assertTrue(res['success'])
        self.assertEqual(len(res['user_message']['attachments']), 1)

    def test_send_message_attachment_failure_is_swallowed(self):
        with patch.object(
                type(self.env['ir.attachment']), 'create',
                side_effect=Exception('disk full')):
            # message create does not use ir.attachment.create
            res = self._send(attachments=[{'name': 'a.png', 'data': PNG_B64}])
        self.assertTrue(res['success'])
        self.assertEqual(res['user_message']['attachments'], [])

    def test_send_message_unexpected_exception(self):
        self.mock_ai.side_effect = Exception('kaboom')
        res = self._send()
        self.assertEqual(res, {'error': 'kaboom'})

    def test_send_message_session_failure(self):
        with patch.object(
                type(self.Session), 'get_or_create_session',
                return_value=self.Session.browse()):
            res = self._send()
        self.assertEqual(res, {'error': 'Failed to create or find chat session'})

    # ---- get_messages -----------------------------------------------------
    def test_get_messages_missing_params(self):
        self.assertEqual(
            self.controller.get_messages(),
            {'error': 'Missing required parameters'})

    def test_get_messages_invalid_ids(self):
        res = self.controller.get_messages(ai_agent_id='x', ai_model_id='y')
        self.assertEqual(res, {'error': 'Invalid agent, model, or session ID'})

    def test_get_messages_success_with_attachment(self):
        session = self._make_session()
        msg = self._add_message(session, 'user', 'hi')
        att = self._make_attachment()
        msg.attachment_ids = [(6, 0, att.ids)]
        self._add_message(session, 'ai', 'yo')
        res = self.controller.get_messages(
            ai_agent_id=self.provider.id, ai_model_id=self.model_a.id,
            session_id=session.id)
        self.assertTrue(res['success'])
        self.assertEqual(res['session_id'], session.id)
        self.assertEqual(res['session_name'], session.name)
        self.assertEqual(len(res['messages']), 2)
        self.assertEqual(res['messages'][0]['attachments'][0]['id'], att.id)

    def test_get_messages_without_session_creates_one(self):
        res = self.controller.get_messages(
            ai_agent_id=self.provider.id, ai_model_id=self.model_a.id)
        self.assertTrue(res['success'])
        self.assertEqual(res['messages'], [])

    def test_get_messages_access_denied(self):
        foreign = self._make_session(user=self.other_user)
        res = self.controller.get_messages(
            ai_agent_id=self.provider.id, ai_model_id=self.model_a.id,
            session_id=foreign.id)
        self.assertEqual(res, {'error': 'Access denied'})

    def test_get_messages_session_not_found(self):
        with patch.object(
                type(self.Session), 'get_or_create_session',
                return_value=self.Session.browse()):
            res = self.controller.get_messages(
                ai_agent_id=self.provider.id, ai_model_id=self.model_a.id)
        self.assertEqual(res, {'error': 'Session not found'})

    # ---- get_active_provider ---------------------------------------------
    def test_get_active_provider_uses_user_preference(self):
        self.env.user.write({
            'active_ai_agent_id': self.provider.id,
            'active_ai_model_id': self.model_b.id,
        })
        res = self.controller.get_active_provider()
        self.assertTrue(res['success'])
        self.assertEqual(res['agent_id'], self.provider.id)
        self.assertEqual(res['model_id'], self.model_b.id)

    def test_get_active_provider_falls_back_to_first_provider(self):
        self.env.user.write({'active_ai_agent_id': False})
        res = self.controller.get_active_provider()
        self.assertTrue(res['success'])
        self.assertTrue(res['agent_id'])

    def test_get_active_provider_model_not_in_provider(self):
        foreign_model = self.Model.create({'model_ref_id': 'foreign'})
        self.env.user.write({
            'active_ai_agent_id': self.provider.id,
            'active_ai_model_id': foreign_model.id,
        })
        res = self.controller.get_active_provider()
        self.assertTrue(res['success'])
        self.assertIn(res['model_id'], self.provider.ai_model_ids.ids)

    def test_get_active_provider_no_provider(self):
        self.env.user.write({'active_ai_agent_id': False})
        with patch.object(
                type(self.Provider), 'search',
                return_value=self.Provider.browse()):
            res = self.controller.get_active_provider()
        self.assertEqual(
            res, {'success': False, 'error': 'No AI Provider configured'})

    def test_get_active_provider_no_models(self):
        self.provider.ai_model_ids = [(5, 0, 0)]
        self.env.user.write({
            'active_ai_agent_id': self.provider.id,
            'active_ai_model_id': False,
        })
        res = self.controller.get_active_provider()
        self.assertEqual(
            res, {'success': False, 'error': 'No models found for this provider'})

    def test_get_active_provider_exception(self):
        broken_env = MagicMock()
        type(broken_env).user = PropertyMock(side_effect=Exception('bad'))
        self.mock_request.env = broken_env
        res = self.controller.get_active_provider()
        self.assertEqual(res, {'success': False, 'error': 'bad'})

    # ---- save_active_config ----------------------------------------------
    def test_save_active_config_success(self):
        res = self.controller.save_active_config(
            ai_agent_id=str(self.provider.id), ai_model_id=self.model_a.id)
        self.assertEqual(res, {'success': True})
        self.assertEqual(self.env.user.active_ai_agent_id, self.provider)
        self.assertEqual(self.env.user.active_ai_model_id, self.model_a)

    def test_save_active_config_no_data(self):
        res = self.controller.save_active_config()
        self.assertEqual(res, {'success': False, 'error': 'No data provided'})

    def test_save_active_config_invalid(self):
        res = self.controller.save_active_config(ai_agent_id='nope')
        self.assertFalse(res['success'])

    # ---- get_all_providers -----------------------------------------------
    def test_get_all_providers(self):
        res = self.controller.get_all_providers()
        self.assertTrue(res['success'])
        entry = next(p for p in res['providers'] if p['id'] == self.provider.id)
        self.assertEqual(
            sorted(m['name'] for m in entry['models']),
            ['test-model-a', 'test-model-b'])

    def test_get_all_providers_exception(self):
        with patch.object(
                type(self.Provider), 'search', side_effect=Exception('nope')):
            res = self.controller.get_all_providers()
        self.assertEqual(res, {'success': False, 'error': 'nope'})

    # ---- get_sessions ----------------------------------------------------
    def _set_create_date(self, session, days_ago):
        self.env.cr.execute(
            "UPDATE ai_chat_session SET create_date = "
            "now() at time zone 'utc' - %s * interval '1 day' WHERE id = %s",
            (days_ago, session.id))
        session.invalidate_recordset()

    def test_get_sessions_groups_by_date(self):
        today = self._make_session()
        self._add_message(today, 'user', 'x' * 80)
        yesterday = self._make_session(model=self.model_b)
        last_week = self._make_session()
        older = self._make_session()
        self._set_create_date(yesterday, 1)
        self._set_create_date(last_week, 4)
        self._set_create_date(older, 30)

        res = self.controller.get_sessions()
        self.assertTrue(res['success'])
        groups = res['sessions']
        ids = {k: [s['id'] for s in v] for k, v in groups.items()}
        self.assertIn(today.id, ids['today'])
        self.assertIn(yesterday.id, ids['yesterday'])
        self.assertIn(last_week.id, ids['last_week'])
        self.assertIn(older.id, ids['older'])
        entry = next(s for s in groups['today'] if s['id'] == today.id)
        self.assertEqual(len(entry['preview']), 50)
        self.assertEqual(entry['ai_model_name'], 'test-model-a')

    def test_get_sessions_excludes_other_users_and_inactive(self):
        foreign = self._make_session(user=self.other_user)
        inactive = self._make_session()
        inactive.is_active = False
        res = self.controller.get_sessions()
        all_ids = [s['id'] for g in res['sessions'].values() for s in g]
        self.assertNotIn(foreign.id, all_ids)
        self.assertNotIn(inactive.id, all_ids)

    def test_get_sessions_exception(self):
        with patch.object(
                type(self.Session), 'search', side_effect=Exception('db')):
            res = self.controller.get_sessions()
        self.assertEqual(res, {'error': 'db'})

    # ---- delete_session --------------------------------------------------
    def test_delete_session_success(self):
        session = self._make_session()
        res = self.controller.delete_session(session_id=session.id)
        self.assertEqual(res, {'success': True})
        self.assertFalse(session.exists())

    def test_delete_session_missing_id(self):
        self.assertEqual(
            self.controller.delete_session(), {'error': 'Missing session_id'})

    def test_delete_session_not_found(self):
        res = self.controller.delete_session(session_id=999999999)
        self.assertEqual(res, {'error': 'Session not found'})

    def test_delete_session_access_denied(self):
        foreign = self._make_session(user=self.other_user)
        res = self.controller.delete_session(session_id=foreign.id)
        self.assertEqual(res, {'error': 'Access denied'})
        self.assertTrue(foreign.exists())

    def test_delete_session_exception(self):
        res = self.controller.delete_session(session_id='abc')
        self.assertIn('error', res)
