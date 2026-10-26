# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from lxml import etree

from odoo.tests import HttpCase, tagged
from odoo.tools import file_open


@tagged('post_install', '-at_install')
class TestPosChatter(HttpCase):
    """Test suite for POS Chatter module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'POS Chatter Test User',
            'login': 'pos_chatter_user',
            'email': 'pos_chatter_user@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('point_of_sale.group_pos_user').id,
            ])],
        })

        cls.other_user = cls.env['res.users'].create({
            'name': 'Other User',
            'login': 'other_user',
            'email': 'other_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.channel = cls.env['discuss.channel'].create({
            'name': 'POS Test Channel',
            'channel_type': 'channel',
        })
        cls.channel._add_members(users=cls.test_user | cls.other_user)

        cls.private_channel = cls.env['discuss.channel'].create({
            'name': 'Private Channel',
            'channel_type': 'channel',
        })
        cls.private_channel._add_members(users=cls.other_user)

    def test_xml_template_structure(self):
        """Test that pos_systray_icon.xml properly extends point_of_sale.Navbar."""
        with file_open('pos_chatter/static/src/xml/pos_systray_icon.xml', 'rb') as f:
            xml_content = f.read()
        tree = etree.fromstring(xml_content)

        templates = tree.xpath("//t[@t-name='pos_chatter.Navbar']")
        self.assertTrue(templates, "Template pos_chatter.Navbar must exist.")
        template = templates[0]
        self.assertEqual(template.get('t-inherit'), 'point_of_sale.Navbar')
        self.assertEqual(template.get('t-inherit-mode'), 'extension')

        xpaths = template.xpath(".//xpath[@expr=\"//div[hasclass('status-buttons')]\"]")
        self.assertTrue(xpaths, "XPath targeting status-buttons must be present.")
        self.assertTrue(template.xpath(".//button[@id='pos_systray_chatter_icon']"))

    def test_get_data_pos_systray_and_chat(self):
        """Test fetching channels, unread counters, reading chat, and mark as read."""
        # Other user posts a message
        msg = self.channel.with_user(self.other_user).message_post(
            body='<p>Hello from colleague</p>',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        self.authenticate(self.test_user.login, self.test_user.login)

        # 1. Fetch systray channels data
        data = self.make_jsonrpc_request('/pos_systray/message_data')
        channel_data = next((c for c in data if c['id'] == self.channel.id), None)
        self.assertIsNotNone(channel_data, "Member channel should be present in systray data.")
        self.assertGreaterEqual(channel_data['count'], 1, "Unread count should be at least 1.")

        # Non-member channel should not appear
        private_data = next((c for c in data if c['id'] == self.private_channel.id), None)
        self.assertIsNone(private_data, "Non-member channel should not be listed.")

        # 2. Fetch chat messages and verify marking as read
        chat_data = self.make_jsonrpc_request('/pos_systray/chat_message', {'data': self.channel.id})
        self.assertEqual(chat_data['name'], self.channel.name)
        self.assertTrue(any('Hello from colleague' in m['body'] for m in chat_data['messages']))

        # After reading, message_data unread counter should become 0
        updated_data = self.make_jsonrpc_request('/pos_systray/message_data')
        updated_channel_data = next((c for c in updated_data if c['id'] == self.channel.id), None)
        self.assertIsNotNone(updated_channel_data)
        self.assertEqual(updated_channel_data['count'], 0, "Unread count in systray should be 0 after reading.")

    def test_send_message_escaping_and_security(self):
        """Test sending message with escaping, membership check, and message_post."""
        self.authenticate(self.test_user.login, self.test_user.login)

        # Send valid message with HTML characters
        res = self.make_jsonrpc_request(
            '/pos_chatter/send_message',
            {'data': {'res_id': self.channel.id, 'msg_body': '<script>alert("xss")</script>Test message'}}
        )
        self.assertTrue(res)

        last_message = self.channel.message_ids[0]
        self.assertNotIn('<script>', last_message.body, "Raw HTML script tags must be escaped.")
        self.assertIn('&lt;script&gt;', last_message.body, "HTML characters must be properly escaped.")
        self.assertEqual(last_message.author_id, self.test_user.partner_id)

        # Attempt to send message to a channel the user is NOT a member of
        unauthorized_res = self.make_jsonrpc_request(
            '/pos_chatter/send_message',
            {'data': {'res_id': self.private_channel.id, 'msg_body': 'Unauthorized post'}}
        )
        self.assertFalse(unauthorized_res, "Posting to non-member channel must be rejected.")
