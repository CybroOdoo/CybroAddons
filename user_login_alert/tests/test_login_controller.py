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
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger
import re


@tagged('post_install', '-at_install')
class TestLoginController(HttpCase):
    """Test suite for the custom web_login controller"""

    def extract_csrf_token(self, html):
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def setUp(self):
        super(TestLoginController, self).setUp()
        self.notification_group = self.env.ref('user_login_alert.receive_login_notification')
        self.test_user = self.env['res.users'].create({
            'name': 'Alert Test User',
            'login': 'alert_test_user',
            'password': 'password123',
            'email': 'alert_test@example.com',
            'groups_id': [(6, 0, [self.notification_group.id, self.env.ref('base.group_user').id])]
        })

    def test_01_login_notification(self):
        """Verify that login triggers field update and email notification"""
        # Clear existing mails for this user
        self.env['mail.mail'].search([('email_to', '=', 'alert_test@example.com')]).unlink()

        # Simulate login
        # We use authenticate to set up the session, but we also want to trigger the controller logic.
        # The controller logic is triggered on POST to /web/login.
        
        url = self.base_url() + '/web/login'
        
        # Get CSRF token first
        res = self.url_open('/web/login')
        csrf_token = self.extract_csrf_token(res.text)

        payload = {
            'login': 'alert_test_user',
            'password': 'password123',
            'csrf_token': csrf_token,
            'db': self.env.cr.dbname,
        }
        
        # Perform login POST
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        with mute_logger('odoo.addons.base.models.res_users'):
            response = self.url_open(url, data=payload, headers=headers, allow_redirects=False)
            self.assertEqual(response.status_code, 303, "Should redirect on successful login")

        # Check if fields were updated
        self.test_user.invalidate_recordset()
        self.assertTrue(self.test_user.last_logged_ip, "IP should be recorded")
        self.assertTrue(self.test_user.last_logged_browser, "Browser should be recorded")
        self.assertTrue(self.test_user.last_logged_os, "OS should be recorded")

        # Check if email was created
        mail = self.env['mail.mail'].search([('email_to', '=', 'alert_test@example.com')], limit=1)
        self.assertTrue(mail, "Email notification should have been created")
        self.assertIn("Login Alert", mail.subject)
        self.assertIn("Your account has been accessed successfully", mail.body_html)

    def test_02_login_no_notification_group(self):
        """Verify that notification is NOT sent if user is not in the group"""
        self.test_user.write({'groups_id': [(3, self.notification_group.id)]})
        self.test_user.write({
            'last_logged_ip': False,
            'last_logged_browser': False,
            'last_logged_os': False
        })
        
        self.env['mail.mail'].search([('email_to', '=', 'alert_test@example.com')]).unlink()

        res = self.url_open('/web/login')
        csrf_token = self.extract_csrf_token(res.text)

        payload = {
            'login': 'alert_test_user',
            'password': 'password123',
            'csrf_token': csrf_token,
            'db': self.env.cr.dbname,
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        self.url_open('/web/login', data=payload, headers=headers, allow_redirects=False)

        # Check if fields were NOT updated
        self.test_user.invalidate_recordset()
        
        self.assertFalse(self.test_user.last_logged_ip, "IP should NOT be recorded if not in group")

        mail = self.env['mail.mail'].search([('email_to', '=', 'alert_test@example.com')], limit=1)
        self.assertFalse(mail, "Email notification should NOT have been created")
