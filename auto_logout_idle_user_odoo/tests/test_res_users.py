# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tools import mute_logger
from psycopg2.errors import CheckViolation
import psycopg2

class TestResUsers(TransactionCase):

    def setUp(self):
        super(TestResUsers, self).setUp()
        self.User = self.env['res.users']

    def test_update_user_valid_idle_time(self):
        """Test updating a user with a valid idle time"""
        user = self.env.user
        user.write({
            'enable_idle': True,
            'idle_time': 15,
        })
        self.env.flush_all()
        self.assertEqual(user.idle_time, 15, "Idle time should be set correctly.")
        self.assertTrue(user.enable_idle, "Enable idle should be True.")

    @mute_logger('odoo.sql_db')
    def test_update_user_invalid_idle_time(self):
        """Test updating a user with an invalid idle time (< 1)"""
        user = self.env.user
        with self.assertRaises(Exception):
            user.write({
                'enable_idle': True,
                'idle_time': 0,
            })
            self.env.flush_all()

    @mute_logger('odoo.sql_db')
    def test_update_user_negative_idle_time(self):
        """Test updating a user with a negative idle time"""
        user = self.env.user
        with self.assertRaises(Exception):
            user.write({
                'enable_idle': True,
                'idle_time': -5,
            })
            self.env.flush_all()
