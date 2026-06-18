# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test suite for res.users inheritance in user_login_alert module"""

    def setUp(self):
        super(TestResUsers, self).setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_alert',
            'email': 'test_user@example.com',
        })

    def test_user_login_fields(self):
        """Verify that newly added login fields can be set and retrieved"""
        self.test_user.write({
            'last_logged_ip': '127.0.0.1',
            'last_logged_browser': 'Chrome',
            'last_logged_os': 'Linux',
        })
        self.assertEqual(self.test_user.last_logged_ip, '127.0.0.1')
        self.assertEqual(self.test_user.last_logged_browser, 'Chrome')
        self.assertEqual(self.test_user.last_logged_os, 'Linux')
