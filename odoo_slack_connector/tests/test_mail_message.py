# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import time
from datetime import datetime, timedelta, UTC
from unittest.mock import patch, MagicMock
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailMessage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMailMessage, cls).setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.write({
            'bot_token': 'xoxb-test-token',
            'slack_sync': True,
        })
        cls.channel = cls.env['discuss.channel'].create({
            'name': 'general',
            'is_slack': True,
            'channel': 'C123',
            'msg_date': fields.Datetime.now() - timedelta(hours=2),
        })
        cls.slack_user = cls.env['res.users'].create({
            'name': 'Slack User',
            'login': 'slack_user@example.com',
            'slack_user_ref': 'U123',
            'is_slack_internal_users': True,
        })

    def test_slack_text_formatting(self):
        """Test _format_slack_text and _parse_blocks formatting helper methods"""
        mail_msg_model = self.env['mail.message']
        
        formatted_text = mail_msg_model._format_slack_text("<https://odoo.com|Odoo>")
        self.assertIn('<a href="https://odoo.com"', formatted_text)
        self.assertIn('>Odoo</a>', formatted_text)
        
        blocks = [
            {
                'type': 'rich_text',
                'elements': [{
                    'elements': [
                        {'type': 'text', 'text': 'Hello '},
                        {'type': 'link', 'url': 'https://google.com', 'text': 'Google'}
                    ]
                }]
            }
        ]
        parsed_blocks = mail_msg_model._parse_blocks(blocks)
        self.assertEqual(parsed_blocks, 'Hello <a href="https://google.com">Google</a><br/>')

    def test_action_synchronization_slack(self):
        """Test action_synchronization_slack schedules history sync, pulls messages and registers them in Odoo"""
        
        sync_timestamp = str((datetime.now() - timedelta(hours=1)).timestamp())
        
        def mock_get(url, *args, **kwargs):
            mock_resp = MagicMock()
            if "conversations.history" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'messages': [{
                        'user': 'U123',
                        'text': 'Hello from Slack!',
                        'ts': sync_timestamp
                    }]
                }
            elif "users.list" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'members': [{
                        'id': 'U123',
                        'real_name': 'Slack User',
                        'is_email_confirmed': True,
                        'profile': {'email': 'slack_user@example.com'}
                    }]
                }
            return mock_resp

        with patch('requests.get', side_effect=mock_get):
            messages_before = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', self.channel.id)
            ])
            
            self.env['mail.message'].action_synchronization_slack()

            messages_after = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', self.channel.id)
            ])
            
            new_messages = messages_after - messages_before
            self.assertEqual(len(new_messages), 1)
            self.assertTrue(new_messages.is_slack)
            self.assertEqual(new_messages.slack_message_ts, sync_timestamp)
            self.assertIn('Hello from Slack!', new_messages.body)
