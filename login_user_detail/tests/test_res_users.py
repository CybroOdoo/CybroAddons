# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, Mock
from odoo.addons.login_user_detail.models import res_users as res_users_module


class TestResUsers(TransactionCase):
    """ Test cases for the model res.users """

    def setUp(self):
        super(TestResUsers, self).setUp()
        self.user = self.env.ref('base.user_admin')

    def test_check_credentials_logs_details(self):
        """ Test that check_credentials creates a login.detail record """
        # Ensure no login detail exists for this IP first to make test clear
        initial_count = self.env['login.detail'].search_count([('ip_address', '=', '192.168.1.100')])

        # Manually mock request to avoid werkzeug LocalProxy RuntimeError in Python 3.12
        original_request = getattr(res_users_module, 'request', None)
        mock_request = Mock()
        mock_request.httprequest.environ = {'REMOTE_ADDR': '192.168.1.100'}
        
        try:
            res_users_module.request = mock_request
            with patch('odoo.addons.base.models.res_users.ResUsers._check_credentials', return_value=None):
                self.user._check_credentials('dummy_password', {'user_agent': 'test'})
        finally:
            if original_request:
                res_users_module.request = original_request

        final_count = self.env['login.detail'].search_count([('ip_address', '=', '192.168.1.100')])
        self.assertEqual(final_count, initial_count + 1)

        # Verify the created record
        login_record = self.env['login.detail'].search([('ip_address', '=', '192.168.1.100')], limit=1)
        self.assertTrue(login_record)
        self.assertEqual(login_record.name, self.user.name)
