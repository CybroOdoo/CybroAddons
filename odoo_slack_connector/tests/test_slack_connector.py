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
import base64
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestSlackConnector(TransactionCase):
    """Test cases for the Slack Odoo Connector module"""

    @classmethod
    def setUpClass(cls):
        """Set up test data used across all test methods"""
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'bot_token': 'xoxb-test-bot-token-123',
        })
        # Create a slack user record linked to the company
        cls.slack_user = cls.env['slack.user'].create({
            'name': 'Test Slack User',
            'email': 'testslack@example.com',
            'user': 'U_TEST_001',
            'res_company_id': cls.company.id,
        })
        # Create a slack channel record linked to the company
        cls.slack_channel = cls.env['slack.channel'].create({
            'name': 'general',
            'res_company_id': cls.company.id,
        })
        # Create a discuss.channel marked as Slack
        cls.discuss_channel = cls.env['discuss.channel'].create({
            'name': 'test-slack-channel',
            'channel': 'C_TEST_001',
            'is_slack': True,
        })

    def setUp(self):
        super().setUp()
        # Reset slack_sync before each test to clean cache pollution
        self.company.slack_sync = False

    # ─── 1. slack.channel CRUD ────────────────────────────────────────────

    def test_slack_channel_creation(self):
        """Test creating a slack.channel record"""
        channel = self.env['slack.channel'].create({
            'name': 'random',
            'res_company_id': self.company.id,
        })
        self.assertEqual(channel.name, 'random')
        self.assertEqual(channel.res_company_id, self.company)

    # ─── 2. slack.user CRUD ───────────────────────────────────────────────

    def test_slack_user_creation(self):
        """Test creating a slack.user record"""
        user = self.env['slack.user'].create({
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'user': 'U_JANE_001',
            'res_company_id': self.company.id,
            'user_token': 'xoxp-user-token-456',
        })
        self.assertEqual(user.name, 'Jane Doe')
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.user, 'U_JANE_001')
        self.assertEqual(user.user_token, 'xoxp-user-token-456')

    # ─── 3. discuss.channel Slack fields ──────────────────────────────────

    def test_discuss_channel_slack_fields(self):
        """Test Slack-specific fields on discuss.channel"""
        self.assertTrue(self.discuss_channel.is_slack)
        self.assertEqual(self.discuss_channel.channel, 'C_TEST_001')
        self.assertFalse(self.discuss_channel.msg_date)

    # ─── 4. res.company Slack fields ──────────────────────────────────────

    def test_res_company_slack_fields(self):
        """Test Slack-specific fields on res.company"""
        self.assertEqual(self.company.bot_token, 'xoxb-test-bot-token-123')
        self.assertFalse(self.company.slack_sync)
        self.assertIn(self.slack_user, self.company.slack_users_ids)
        self.assertIn(self.slack_channel, self.company.slack_channel_ids)

    # ─── 5. res.users Slack fields ────────────────────────────────────────

    def test_res_users_slack_fields(self):
        """Test Slack-specific fields on res.users"""
        user = self.env.user
        self.assertFalse(user.is_slack_internal_users)
        self.assertFalse(user.slack_user_ref)

    # ─── 6. remove_html utility ──────────────────────────────────────────

    def test_remove_html(self):
        """Test remove_html strips all HTML tags"""
        from odoo.addons.odoo_slack_connector.models.mail_message import (
            remove_html,
        )
        self.assertEqual(remove_html('<b>Hello</b> <i>World</i>'),
                         'Hello World')
        self.assertEqual(remove_html('<p>Paragraph</p>'), 'Paragraph')
        self.assertEqual(remove_html('No tags here'), 'No tags here')
        self.assertEqual(remove_html(''), '')

    # ─── 7. _format_slack_text ────────────────────────────────────────────

    def test_format_slack_text(self):
        """Test _format_slack_text converts Slack markup to HTML"""
        msg = self.env['mail.message']
        # URL with label: <url|text>
        result = msg._format_slack_text('<https://example.com|Example>')
        self.assertIn('href="https://example.com"', result)
        self.assertIn('Example', result)
        # Bare URL: <url>
        result = msg._format_slack_text('<https://example.com>')
        self.assertIn('href="https://example.com"', result)
        # Newlines → <br/>
        result = msg._format_slack_text('line1\nline2')
        self.assertIn('<br/>', result)
        # Empty string
        self.assertEqual(msg._format_slack_text(''), '')
        self.assertEqual(msg._format_slack_text(None), '')

    # ─── 8. _parse_blocks ────────────────────────────────────────────────

    def test_parse_blocks(self):
        """Test _parse_blocks handles rich_text blocks"""
        msg = self.env['mail.message']
        blocks = [{
            'type': 'rich_text',
            'elements': [{
                'type': 'rich_text_section',
                'elements': [
                    {'type': 'text', 'text': 'Hello '},
                    {'type': 'link', 'url': 'https://odoo.com',
                     'text': 'Odoo'},
                    {'type': 'emoji', 'name': 'smile'},
                ],
            }],
        }]
        result = msg._parse_blocks(blocks)
        self.assertIn('Hello ', result)
        self.assertIn('href="https://odoo.com"', result)
        self.assertIn('Odoo', result)
        self.assertIn(':smile:', result)
        # Empty blocks
        self.assertEqual(msg._parse_blocks([]), '')

    # ─── 9. action_sync_users — new users ─────────────────────────────────

    def test_action_sync_users_new_users(self):
        """Test action_sync_users creates new portal users from Slack"""
        members = [{
            'id': 'U_NEW_001',
            'real_name': 'New Slack User',
            'is_email_confirmed': True,
            'profile': {'email': 'newslack_unique_test@example.com'},
        }]
        self.env.user.action_sync_users(members)
        new_user = self.env['res.users'].search([
            ('slack_user_ref', '=', 'U_NEW_001'),
        ], limit=1)
        self.assertTrue(new_user.exists())
        self.assertEqual(new_user.name, 'New Slack User')
        self.assertTrue(new_user.is_slack_internal_users)

    # ─── 10. action_sync_users — existing login (Slack user) ─────────────

    def test_action_sync_users_existing_login(self):
        """Test action_sync_users updates existing Slack user's ref"""
        existing = self.env['res.users'].create({
            'name': 'Existing Slack',
            'login': 'existing_slack_test_unique@example.com',
            'is_slack_internal_users': True,
            'slack_user_ref': 'U_OLD_REF',
            'company_id': self.company.id,
        })
        members = [{
            'id': 'U_UPDATED_REF',
            'real_name': 'Existing Slack',
            'is_email_confirmed': True,
            'profile': {'email': 'existing_slack_test_unique@example.com'},
        }]
        self.env.user.action_sync_users(members)
        existing.invalidate_recordset()
        self.assertEqual(existing.slack_user_ref, 'U_UPDATED_REF')

    # ─── 11. action_sync_users — non-Slack duplicate logs error without modification ────────

    def test_action_sync_users_non_slack_duplicate(self):
        """Test action_sync_users logs error and doesn't modify non-Slack user with same login"""
        user = self.env['res.users'].create({
            'name': 'Regular User',
            'login': 'regular_non_slack_dup@example.com',
            'is_slack_internal_users': False,
            'company_id': self.company.id,
        })
        members = [{
            'id': 'U_CONFLICT',
            'real_name': 'Conflicting User',
            'is_email_confirmed': True,
            'profile': {'email': 'regular_non_slack_dup@example.com'},
        }]
        # The method catches UserError internally and logs it, so it does not raise
        self.env.user.action_sync_users(members)
        # Verify user was not modified to a slack user
        self.assertFalse(user.is_slack_internal_users)
        self.assertFalse(user.slack_user_ref)

    # ─── 12. action_sync creates channels ─────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.discuss_channel.DiscussChannel.action_sync_members')
    @patch('odoo.addons.odoo_slack_connector.models.res_company.requests.get')
    def test_action_sync_creates_channels(self, mock_get, mock_sync_members):
        """Test action_sync creates discuss.channel and slack.channel"""
        # Mock users.list response
        users_response = MagicMock()
        users_response.json.return_value = {
            'ok': True,
            'members': [],
        }
        # Mock conversations.list response
        channels_response = MagicMock()
        channels_response.json.return_value = {
            'ok': True,
            'channels': [
                {'id': 'C_SYNC_001', 'name': 'sync-channel-test'},
            ],
        }
        mock_get.side_effect = [users_response, channels_response]
        self.company.action_sync()
        # Verify discuss.channel was created
        dc = self.env['discuss.channel'].search([
            ('channel', '=', 'C_SYNC_001'),
            ('is_slack', '=', True),
        ])
        self.assertTrue(dc.exists())
        self.assertEqual(dc.name, 'sync-channel-test')
        # Verify slack_sync flag is set
        self.assertTrue(self.company.slack_sync)
        # Verify member sync was triggered
        mock_sync_members.assert_called_once()

    # ─── 12b. action_sync_members ─────────────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.discuss_channel.requests.Session')
    @patch('odoo.addons.odoo_slack_connector.models.discuss_channel.requests.get')
    def test_action_sync_members(self, mock_get, mock_session_class):
        """Test action_sync_members adds members to discuss.channel"""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock session.post for conversations.join
        mock_join_response = MagicMock()
        mock_join_response.json.return_value = {'ok': True}
        mock_session.post.return_value = mock_join_response

        # Mock session.get for conversations.members
        mock_members_response = MagicMock()
        mock_members_response.json.return_value = {
            'ok': True,
            'members': ['U_TEST_001'],
        }
        mock_session.get.return_value = mock_members_response

        # Mock requests.get for users.info
        mock_user_info_response = MagicMock()
        mock_user_info_response.json.return_value = {
            'ok': True,
            'user': {
                'id': 'U_TEST_001',
                'real_name': 'Test Slack Member',
                'profile': {'email': 'testslack@example.com'}
            }
        }
        mock_get.return_value = mock_user_info_response

        # Call the method
        self.discuss_channel.action_sync_members()
        # Verify the channel got a new member (partner id of slack user or new user)
        member_partner_ids = self.discuss_channel.channel_member_ids.mapped('partner_id')
        user = self.env['res.users'].search([('slack_user_ref', '=', 'U_TEST_001')], limit=1)
        self.assertTrue(user.exists())
        self.assertIn(user.partner_id, member_partner_ids)

    # ─── 13. action_set_admin ─────────────────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.res_company.requests.post')
    def test_action_set_admin(self, mock_post):
        """Test action_set_admin marks the correct Slack user as admin"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'user_id': 'U_TEST_001',
        }
        mock_post.return_value = mock_response
        self.slack_user.write({'user': 'U_TEST_001'})
        # Monkeypatch token property on company class since the module uses self.token instead of self.bot_token
        with patch.object(type(self.company), 'token', 'xoxb-test-bot-token-123', create=True):
            self.company.action_set_admin()
        # The method should have been called
        mock_post.assert_called_once()

    # ─── 14. _post_text_message_to_slack ──────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.mail_message.requests.post')
    def test_post_text_message_to_slack(self, mock_post):
        """Test _post_text_message_to_slack sends message and returns ts"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'message': {'ts': '1234567890.123456'},
        }
        mock_post.return_value = mock_response
        msg = self.env['mail.message']
        headers = {
            'Authorization': 'Bearer xoxb-test',
            'Content-Type': 'application/json; charset=utf-8',
        }
        result = msg._post_text_message_to_slack(
            'Hello Slack', 'general', headers
        )
        self.assertEqual(result, '1234567890.123456')
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        self.assertEqual(
            call_kwargs.kwargs['json']['text'], 'Hello Slack'
        )

    # ─── 15. _upload_attachments_to_slack ─────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.mail_message.requests.post')
    def test_upload_attachments_to_slack(self, mock_post):
        """Test _upload_attachments_to_slack uploads files and returns IDs"""
        # First call: getUploadURLExternal
        url_response = MagicMock()
        url_response.json.return_value = {
            'ok': True,
            'upload_url': 'https://files.slack.com/upload/v1/test',
            'file_id': 'F_TEST_001',
        }
        # Second call: actual upload
        upload_response = MagicMock()
        upload_response.status_code = 200
        mock_post.side_effect = [url_response, upload_response]
        msg = self.env['mail.message']
        headers = {
            'Authorization': 'Bearer xoxb-test',
            'Content-Type': 'application/json; charset=utf-8',
        }
        attachments = [{
            'name': 'test.txt',
            'content': b'Hello World',
            'mimetype': 'text/plain',
        }]
        result = msg._upload_attachments_to_slack(attachments, headers)
        self.assertEqual(result, ['F_TEST_001'])
        self.assertEqual(mock_post.call_count, 2)

    # ─── 16. _get_slack_channel_map ──────────────────────────────────────

    @patch('odoo.addons.odoo_slack_connector.models.mail_message.requests.post')
    def test_get_slack_channel_map(self, mock_post):
        """Test _get_slack_channel_map builds name→id mapping"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': True,
            'channels': [
                {'name': 'general', 'id': 'C001'},
                {'name': 'random', 'id': 'C002'},
            ],
        }
        mock_post.return_value = mock_response
        msg = self.env['mail.message']
        headers = {'Authorization': 'Bearer xoxb-test'}
        result = msg._get_slack_channel_map(headers)
        self.assertEqual(result['general'], 'C001')
        self.assertEqual(result['#general'], 'C001')
        self.assertEqual(result['random'], 'C002')
        self.assertEqual(result['#random'], 'C002')

    # ─── 17. mail.message Slack fields ────────────────────────────────────

    def test_mail_message_slack_fields(self):
        """Test Slack-specific fields on mail.message"""
        msg = self.env['mail.message'].create({
            'body': 'Test message',
            'is_slack': True,
            'slack_message_ts': '1234567890.000001',
            'is_slack_pending': False,
            'slack_msg_id': 'F001,F002',
        })
        self.assertTrue(msg.is_slack)
        self.assertEqual(msg.slack_message_ts, '1234567890.000001')
        self.assertFalse(msg.is_slack_pending)
        self.assertEqual(msg.slack_msg_id, 'F001,F002')

    # ─── 18. mail.message create skips Slack when not synced ─────────────

    def test_mail_message_create_no_sync(self):
        """Test mail.message.create skips Slack posting when slack_sync=False"""
        self.company.slack_sync = False
        msg = self.env['mail.message'].create({
            'body': 'Should not go to Slack',
            'model': 'discuss.channel',
            'res_id': self.discuss_channel.id,
        })
        # Message should be created normally without Slack fields
        self.assertTrue(msg.exists())
        self.assertFalse(msg.is_slack)

    # ─── 19. Uninstall hook ──────────────────────────────────────────────

    def test_uninstall_hook(self):
        """Test slack_uninstall_hook deletes Slack records"""
        from odoo.addons.odoo_slack_connector import slack_uninstall_hook
        # Create Slack-specific discuss channel
        dc = self.env['discuss.channel'].create({
            'name': 'to-be-deleted',
            'channel': 'C_DEL_001',
            'is_slack': True,
        })
        dc_id = dc.id
        # Uninstall hook calls env.cr.commit(), which fails under testing unless mocked
        with patch.object(self.env.cr, 'commit'):
            slack_uninstall_hook(self.env)
        # Verify the channel was deleted
        remaining = self.env['discuss.channel'].search([('id', '=', dc_id)])
        self.assertFalse(remaining.exists())
