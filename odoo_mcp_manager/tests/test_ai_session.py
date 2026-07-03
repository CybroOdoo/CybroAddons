# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestAiSession(TransactionCase):

    def setUp(self):
        super(TestAiSession, self).setUp()
        self.user = self.env.user
        self.session = self.env['ai.session'].create({
            'user_id': self.user.id,
            'mcp_source': 'mcp',
        })

    def test_01_session_creation(self):
        """Test simple session creation and default values."""
        self.assertEqual(self.session.state, 'not_initialized')
        self.assertTrue(self.session.session_id)
        self.assertTrue(self.session.active)

    def test_02_transition_to(self):
        """Test session state transitions."""
        # Allowed transition: not_initialized -> initializing
        self.session.transition_to('initializing')
        self.assertEqual(self.session.state, 'initializing')

        # Forbidden transition: initializing -> terminated (not in _VALID_TRANSITIONS)
        self.session.transition_to('terminated')
        self.assertEqual(self.session.state, 'initializing')

        # Allowed transition: initializing -> initialized
        self.session.transition_to('initialized')
        self.assertEqual(self.session.state, 'initialized')

    def test_03_terminate(self):
        """Test session termination."""
        self.session.terminate()
        self.assertEqual(self.session.state, 'terminated')
        self.assertFalse(self.session.active)

    def test_04_create_new_session(self):
        """Test create_new_session model method."""
        new_session = self.env['ai.session'].create_new_session(self.user.id)
        self.assertEqual(new_session.user_id, self.user)
        self.assertEqual(new_session.state, 'not_initialized')
