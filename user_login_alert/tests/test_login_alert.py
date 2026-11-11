# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from lxml import html

from odoo.tests import HttpCase, new_test_user, tagged

CHROME_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
FIREFOX_LINUX = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0")
GROUP = 'user_login_alert.receive_login_notification'


@tagged('post_install', '-at_install')
class TestLoginAlert(HttpCase):
    """Test the login alert email sent on a successful login."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='alert_user', password='alert_user',
            email='alert_user@example.com',
            groups=f'base.group_user,{GROUP}',
        )

    def _login(self, login='alert_user', password='alert_user',
               user_agent=CHROME_WINDOWS):
        """Log in through the login page with a fresh session."""
        self.opener.cookies.clear()
        headers = {'User-Agent': user_agent}
        page = self.url_open('/web/login', headers=headers)
        csrf_token = html.fromstring(page.text).xpath(
            '//input[@name="csrf_token"]/@value')[0]
        return self.url_open('/web/login', data={
            'login': login,
            'password': password,
            'csrf_token': csrf_token,
        }, headers=headers)

    def _get_alerts(self, email='alert_user@example.com'):
        """Return the alert emails sent to the given address."""
        return self.env['mail.mail'].sudo().search(
            [('email_to', '=', email)])

    def test_first_login_sends_alert(self):
        """The first login sends an alert and stores the login details."""
        self._login()
        alerts = self._get_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertIn('Login Alert', alerts.subject)
        self.assertIn(self.user.name, alerts.body_html)
        self.assertEqual(self.user.last_logged_browser, 'Chrome')
        self.assertEqual(self.user.last_logged_os, 'Windows')
        self.assertTrue(self.user.last_logged_ip)

    def test_alert_contains_login_details(self):
        """The alert shows the operating system, browser and IP address."""
        self._login()
        body = self._get_alerts().body_html
        self.assertIn('Windows', body)
        self.assertIn('Chrome', body)
        self.assertIn(self.user.last_logged_ip, body)

    def test_same_system_does_not_send_second_alert(self):
        """A login from the same system does not send another alert."""
        self._login()
        self._login()
        self.assertEqual(len(self._get_alerts()), 1)

    def test_new_browser_sends_new_alert(self):
        """A login from a different system sends a new alert."""
        self._login()
        self._login(user_agent=FIREFOX_LINUX)
        self.assertEqual(len(self._get_alerts()), 2)
        self.assertEqual(self.user.last_logged_browser, 'Firefox')
        self.assertEqual(self.user.last_logged_os, 'Linux')

    def test_user_without_group_gets_no_alert(self):
        """Users outside the notification group get no alert."""
        new_test_user(
            self.env, login='plain_user', password='plain_user',
            email='plain_user@example.com', groups='base.group_user')
        self._login('plain_user', 'plain_user')
        self.assertFalse(self._get_alerts('plain_user@example.com'))

    def test_user_without_email_gets_no_alert(self):
        """Users whose partner has no email get no alert."""
        user = new_test_user(
            self.env, login='no_mail_user', password='no_mail_user',
            groups=f'base.group_user,{GROUP}')
        user.partner_id.email = False
        self._login('no_mail_user', 'no_mail_user')
        self.assertFalse(user.last_logged_ip)

    def test_failed_login_sends_no_alert(self):
        """A wrong password sends no alert and stores no details."""
        self._login(password='wrong password')
        self.assertFalse(self._get_alerts())
        self.assertFalse(self.user.last_logged_ip)
