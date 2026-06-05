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
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResCompany, cls).setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.write({
            'bot_token': 'xoxb-test-token',
        })

    def test_action_sync(self):
        """Test action_sync retrieves channels and users successfully with mocked GET and POST requests"""
        def mock_get(url, *args, **kwargs):
            mock_resp = MagicMock()
            if "users.list" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'members': [{
                        'id': 'U123',
                        'real_name': 'Slack User 1',
                        'is_email_confirmed': True,
                        'profile': {'email': 'slack1@example.com'}
                    }]
                }
            elif "conversations.list" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'channels': [{
                        'id': 'C123',
                        'name': 'random'
                    }]
                }
            elif "conversations.members" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'members': ['U123']
                }
            elif "users.info" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'user': {
                        'id': 'U123',
                        'real_name': 'Slack User 1',
                        'profile': {'email': 'slack1@example.com'}
                    }
                }
            return mock_resp

        def mock_post(url, *args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.json.return_value = {'ok': True}
            return mock_resp

        with patch('requests.get', side_effect=mock_get), \
             patch('requests.post', side_effect=mock_post), \
             patch('requests.Session.get', side_effect=mock_get), \
             patch('requests.Session.post', side_effect=mock_post):
             
            self.assertFalse(self.company.slack_sync)

            self.company.action_sync()

            channel = self.env['discuss.channel'].search([('channel', '=', 'C123')])
            self.assertTrue(channel.exists())
            self.assertEqual(channel.name, 'random')
            self.assertTrue(channel.is_slack)

            slack_user = self.company.slack_users_ids.filtered(lambda u: u.user == 'U123')
            self.assertTrue(slack_user.exists())
            self.assertEqual(slack_user.name, 'Slack User 1')

            slack_channel = self.company.slack_channel_ids.filtered(lambda c: c.name == 'random')
            self.assertTrue(slack_channel.exists())

            self.assertTrue(self.company.slack_sync)
