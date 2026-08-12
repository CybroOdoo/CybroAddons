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


class TestTokenSession(TransactionCase):
    """Test suite for token.session model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TokenSession = cls.env['token.session']

    def test_token_session_create(self):
        """Test creating a token session generates reference number."""
        session = self.TokenSession.create({
            'name': 'Morning Session'
        })
        self.assertEqual(session.name, 'Morning Session')
        self.assertTrue(session.reference_no)
        self.assertEqual(session.opened_by, self.env.user)
