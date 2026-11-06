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
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import AccessDenied
from odoo.tests.common import HttpCase, TransactionCase, tagged

from odoo.addons.restrict_logins.models.res_users import AlreadyLoggedIn

USERS_MODULE = 'odoo.addons.restrict_logins.models.res_users'
PASSWORD = 'Test@1234!Strong'
ENV = {'interactive': True}


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Tests of the session handling of 'res.users'."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Session User',
            'login': 'session_user',
            'password': PASSWORD,
        })
        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time', '30')

    @staticmethod
    def _request(sid='sid-1'):
        request = MagicMock()
        request.session.sid = sid
        request.httprequest.environ = {'REMOTE_ADDR': '127.0.0.1'}
        request.cookies = {}
        return request

    def _credential(self, password=PASSWORD):
        return {'login': self.user.login, 'password': password,
                'type': 'password'}

    def test_new_user_has_no_session(self):
        self.assertFalse(self.user.sid)
        self.assertFalse(self.user.exp_date)
        self.assertFalse(self.user.logged_in)
        self.assertFalse(self.user.last_update)

    def test_session_fields_are_not_copied(self):
        self.user.write({'sid': 'abc', 'logged_in': True})
        copy = self.user.copy({'login': 'copied_user'})
        self.assertFalse(copy.sid)
        self.assertFalse(copy.logged_in)

    def test_expire_minutes_configured(self):
        self.assertEqual(self.env['res.users']._get_session_expire_minutes(),
                         30)

    def test_expire_minutes_fallback(self):
        params = self.env['ir.config_parameter'].sudo()
        for value in (False, 'abc', '0', '-5'):
            params.set_param('restrict_logins.session_expire_time', value)
            self.assertEqual(
                self.env['res.users']._get_session_expire_minutes(), 10,
                "Invalid value %r must fall back to 10 minutes" % value)

    def test_save_session(self):
        before = fields.Datetime.now()
        with patch(USERS_MODULE + '.request', self._request('sid-save')):
            self.user._save_session()
        user = self.user.sudo()
        self.assertEqual(user.sid, 'sid-save')
        self.assertTrue(user.logged_in)
        self.assertTrue(user.last_update)
        self.assertGreaterEqual(user.exp_date, before + timedelta(minutes=29))
        self.assertLessEqual(user.exp_date,
                             fields.Datetime.now() + timedelta(minutes=30))

    def test_clear_session(self):
        self.user.write({'sid': 'sid', 'logged_in': True,
                         'exp_date': fields.Datetime.now()})
        self.user._clear_session()
        self.assertFalse(self.user.sid)
        self.assertFalse(self.user.exp_date)
        self.assertFalse(self.user.logged_in)
        self.assertTrue(self.user.last_update)

    def test_clear_session_on_clean_user(self):
        self.user._clear_session()
        self.assertFalse(self.user.logged_in)

    def test_check_password_login(self):
        users = self.env['res.users']
        self.assertEqual(
            users._check_password_login(self.user.login, PASSWORD),
            self.user)
        with self.assertRaises(AccessDenied):
            users._check_password_login(self.user.login, 'wrong')
        with self.assertRaises(AccessDenied):
            users._check_password_login('nobody', PASSWORD)

    def test_validate_sessions_clears_expired(self):
        self.user.write({
            'sid': 'expired-sid', 'logged_in': True,
            'exp_date': fields.Datetime.now() - timedelta(minutes=1)})
        with patch(USERS_MODULE + '.clear_session_history',
                   return_value=True) as clear:
            self.env['res.users']._validate_sessions()
        clear.assert_called_with('expired-sid')
        self.assertFalse(self.user.sid)
        self.assertFalse(self.user.logged_in)

    def test_validate_sessions_keeps_active(self):
        self.user.write({
            'sid': 'active-sid', 'logged_in': True,
            'exp_date': fields.Datetime.now() + timedelta(minutes=10)})
        with patch(USERS_MODULE + '.clear_session_history') as clear:
            self.env['res.users']._validate_sessions()
        clear.assert_not_called()
        self.assertEqual(self.user.sid, 'active-sid')
        self.assertTrue(self.user.logged_in)

    def test_validate_sessions_keeps_user_when_file_not_removed(self):
        self.user.write({
            'sid': 'stuck-sid', 'logged_in': True,
            'exp_date': fields.Datetime.now() - timedelta(minutes=1)})
        with patch(USERS_MODULE + '.clear_session_history',
                   return_value=False):
            self.env['res.users']._validate_sessions()
        self.assertEqual(self.user.sid, 'stuck-sid')

    def test_cron_runs_validation(self):
        cron = self.env.ref('restrict_logins.validate_user_sessions')
        self.user.write({
            'sid': 'cron-sid', 'logged_in': True,
            'exp_date': fields.Datetime.now() - timedelta(minutes=1)})
        with patch(USERS_MODULE + '.clear_session_history',
                   return_value=True):
            cron.method_direct_trigger()
        self.assertFalse(self.user.logged_in)


@tagged('post_install', '-at_install')
class TestResUsersLogin(HttpCase):
    """Tests of the login restriction (it needs its own cursor)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Login User',
            'login': 'login_user',
            'password': PASSWORD,
        })

    _request = staticmethod(TestResUsers._request)

    def _user(self):
        """The user, read again from the database."""
        self.user.invalidate_recordset()
        return self.user.sudo()

    def _credential(self, password=PASSWORD):
        return {'login': self.user.login, 'password': password,
                'type': 'password'}

    def test_login_saves_session(self):
        with patch(USERS_MODULE + '.request', self._request('sid-login')):
            auth_info = self.env['res.users']._login(
                self.env.cr.dbname, self._credential(), ENV)
        self.assertEqual(auth_info['uid'], self.user.id)
        self.assertEqual(self._user().sid, 'sid-login')
        self.assertTrue(self._user().logged_in)

    def test_login_without_request_does_not_track_session(self):
        auth_info = self.env['res.users']._login(
            self.env.cr.dbname, self._credential(), ENV)
        self.assertEqual(auth_info['uid'], self.user.id)
        self.assertFalse(self._user().logged_in)

    def test_second_login_is_refused(self):
        users = self.env['res.users']
        with patch(USERS_MODULE + '.request', self._request('sid-first')):
            users._login(self.env.cr.dbname, self._credential(), ENV)
        with patch(USERS_MODULE + '.request', self._request('sid-second')):
            with self.assertRaises(AlreadyLoggedIn) as caught:
                users._login(self.env.cr.dbname, self._credential(), ENV)
        self.assertEqual(caught.exception.args[0], AlreadyLoggedIn.KEY)
        self.assertEqual(self._user().sid, 'sid-first')

    def test_login_allowed_again_after_clear(self):
        users = self.env['res.users']
        with patch(USERS_MODULE + '.request', self._request('sid-first')):
            users._login(self.env.cr.dbname, self._credential(), ENV)
        self._user()._clear_session()
        self.env.flush_all()
        with patch(USERS_MODULE + '.request', self._request('sid-again')):
            users._login(self.env.cr.dbname, self._credential(), ENV)
        self.assertEqual(self._user().sid, 'sid-again')

    def test_login_wrong_password(self):
        with patch(USERS_MODULE + '.request', self._request()):
            with self.assertRaises(AccessDenied) as caught:
                self.env['res.users']._login(
                    self.env.cr.dbname, self._credential('wrong'), ENV)
        self.assertNotIsInstance(caught.exception, AlreadyLoggedIn)
        self.assertFalse(self._user().logged_in)

    def test_login_unknown_user(self):
        credential = {'login': 'nobody', 'password': 'x', 'type': 'password'}
        with patch(USERS_MODULE + '.request', self._request()):
            with self.assertRaises(AccessDenied):
                self.env['res.users']._login(
                    self.env.cr.dbname, credential, ENV)

    def test_wrong_password_on_logged_in_user_is_not_revealed(self):
        """The 'already logged in' answer needs the right password."""
        users = self.env['res.users']
        with patch(USERS_MODULE + '.request', self._request('sid-first')):
            users._login(self.env.cr.dbname, self._credential(), ENV)
            with self.assertRaises(AccessDenied) as caught:
                users._login(
                    self.env.cr.dbname, self._credential('wrong'), ENV)
        self.assertNotIsInstance(caught.exception, AlreadyLoggedIn)
