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
class TestDiscussChannel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDiscussChannel, cls).setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.write({
            'bot_token': 'xoxb-test-token',
        })
        cls.channel = cls.env['discuss.channel'].create({
            'name': 'general',
            'is_slack': True,
            'channel': 'C123',
        })
        cls.channel.channel_member_ids.unlink()

    def test_action_sync_members(self):
        """Test action_sync_members successfully syncs channel members with mocked requests"""
        def mock_get(url, *args, **kwargs):
            mock_resp = MagicMock()
            if "conversations.members" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'members': ['U123']
                }
            elif "users.info" in url:
                mock_resp.json.return_value = {
                    'ok': True,
                    'user': {
                        'id': 'U123',
                        'real_name': 'Slack Member 1',
                        'profile': {'email': 'member1@example.com'}
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

            self.assertEqual(len(self.channel.channel_member_ids), 0)

            self.channel.action_sync_members()

            user = self.env['res.users'].search([('slack_user_ref', '=', 'U123')])
            self.assertTrue(user.exists())
            self.assertEqual(user.name, 'Slack Member 1')

            self.assertEqual(len(self.channel.channel_member_ids), 1)
            self.assertEqual(self.channel.channel_member_ids.mapped('partner_id'), user.partner_id)
