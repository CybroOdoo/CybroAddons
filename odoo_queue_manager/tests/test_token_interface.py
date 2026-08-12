# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase


class TestTokenInterface(TransactionCase):
    """Test suite for token.interface model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TokenInterface = cls.env['token.interface']
        cls.TokenSession = cls.env['token.session']
        cls.interface = cls.TokenInterface.create({
            'name': 'Interface 1'
        })

    def test_action_start_new_session(self):
        """Test starting a new session creates session record and returns action."""
        res = self.interface.action_start_new_session()
        self.assertTrue(self.interface.is_start_session)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('url'), '/generate/token')

        session = self.TokenSession.search([
            ('name', '=', 'Interface 1')
        ], limit=1)
        self.assertTrue(session.exists())

    def test_action_resume_session(self):
        """Test resuming session returns expected act_url dict."""
        res = self.interface.action_resume_session()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('url'), '/generate/token')

    def test_action_close_session(self):
        """Test closing session sets is_start_session to False."""
        self.interface.is_start_session = True
        self.interface.action_close_session()
        self.assertFalse(self.interface.is_start_session)
