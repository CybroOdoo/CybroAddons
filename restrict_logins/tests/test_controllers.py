# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
import re
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import HttpCase, tagged

PASSWORD = 'Test@1234!Strong'
CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
SESSION_MODULE = 'odoo.addons.restrict_logins.controllers.session'


@tagged('post_install', '-at_install')
class TestControllers(HttpCase):
    """Tests of the login and logout flows through the HTTP controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Flow User',
            'login': 'flow_user',
            'password': PASSWORD,
            'groups_id': [(4, cls.env.ref('base.group_user').id)],
        })

    def _csrf(self):
        page = self.url_open('/web/login')
        return CSRF_RE.search(page.text).group(1)

    def _post_login(self, password=PASSWORD):
        return self.url_open('/web/login', data={
            'login': self.user.login, 'password': password,
            'csrf_token': self._csrf()}, allow_redirects=False)

    def _logged_in_user(self):
        """Log the user in and make the first authenticated request."""
        response = self._post_login()
        self.assertEqual(response.status_code, 303)
        self.url_open('/odoo')
        self.user.invalidate_recordset()
        return response

    def _new_device(self):
        """Forget the cookies, as a login from another device would."""
        self.opener.cookies.clear()

    def test_login_stores_current_session(self):
        self._logged_in_user()
        self.assertTrue(self.user.logged_in)
        self.assertEqual(
            self.user.sid, self.opener.cookies.get('session_id'))
        self.assertTrue(self.user.exp_date)

    def test_wrong_password_shows_standard_error(self):
        response = self._post_login('wrong')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Wrong login/password', response.text)
        self.assertNotIn('Log out from other devices', response.text)
        self.assertFalse(self.user.logged_in)

    def test_second_device_is_refused(self):
        self._logged_in_user()
        self._new_device()
        response = self._post_login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('already logged in', response.text)
        self.assertIn('Log out from other devices', response.text)

    def test_logout_from_other_devices(self):
        self._logged_in_user()
        self._new_device()
        response = self.url_open('/clear_all_sessions', data={
            'login': self.user.login, 'password': PASSWORD,
            'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login?login=flow_user',
                      response.headers['Location'])
        self.user.invalidate_recordset()
        self.assertFalse(self.user.logged_in)
        self.assertFalse(self.user.sid)
        self.assertEqual(self._post_login().status_code, 303)

    def test_logout_from_other_devices_needs_the_password(self):
        self._logged_in_user()
        self._new_device()
        response = self.url_open('/clear_all_sessions', data={
            'login': self.user.login, 'password': 'wrong',
            'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=denied', response.headers['Location'])
        self.user.invalidate_recordset()
        self.assertTrue(self.user.logged_in)

    def test_logout_from_other_devices_is_refused_when_file_stays(self):
        self._logged_in_user()
        self._new_device()
        with patch(SESSION_MODULE + '.clear_session_history',
                   return_value=False):
            response = self.url_open('/clear_all_sessions', data={
                'login': self.user.login, 'password': PASSWORD,
                'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertIn('error=denied', response.headers['Location'])
        self.user.invalidate_recordset()
        self.assertTrue(self.user.logged_in)

    def test_logout_from_other_devices_rejects_get(self):
        response = self.url_open(
            '/clear_all_sessions?login=flow_user&password=' + PASSWORD)
        self.assertEqual(response.status_code, 405)

    def test_logout_clears_session_details(self):
        self._logged_in_user()
        response = self.url_open('/web/session/logout',
                                 allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.user.invalidate_recordset()
        self.assertFalse(self.user.logged_in)
        self.assertFalse(self.user.sid)

    def test_logout_without_session(self):
        response = self.url_open('/web/session/logout',
                                 allow_redirects=False)
        self.assertEqual(response.status_code, 303)

    def test_super_logout_all_needs_a_login(self):
        response = self.url_open('/super/logout_all', data={
            'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertIn('/web/login', response.headers['Location'])

    def test_super_logout_all_refused_to_non_admin(self):
        self._logged_in_user()
        with patch(SESSION_MODULE + '.clear_all_session_files') as clear:
            response = self.url_open('/super/logout_all', data={
                'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertEqual(response.status_code, 403)
        clear.assert_not_called()
        self.user.invalidate_recordset()
        self.assertTrue(self.user.logged_in)

    def test_super_logout_all_by_admin(self):
        self.user.write({'sid': 'other-sid', 'logged_in': True})
        self.authenticate('admin', 'admin')
        with patch(SESSION_MODULE + '.clear_all_session_files',
                   return_value=1) as clear:
            response = self.url_open('/super/logout_all', data={
                'csrf_token': self._csrf()}, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        clear.assert_called_once()
        self.user.invalidate_recordset()
        self.assertFalse(self.user.logged_in)
        self.assertFalse(self.user.sid)

    def test_session_refresh_error_does_not_break_requests(self):
        ir_http = type(self.env['ir.http'])
        with patch.object(ir_http, '_refresh_user_session',
                          side_effect=ValueError('boom')):
            response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)

    def test_session_is_refreshed_on_read_only_route(self):
        """Read only routes run on a read only cursor, the session details
        must still be refreshed."""
        self._logged_in_user()
        old = fields.Datetime.now() - timedelta(minutes=5)
        self.user.write({'last_update': old, 'exp_date': old})
        self.env.flush_all()
        response = self.url_open('/web/manifest.webmanifest')
        self.assertEqual(response.status_code, 200)
        self.user.invalidate_recordset()
        self.assertGreater(self.user.last_update, old)
        self.assertGreater(self.user.exp_date, fields.Datetime.now())
