# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import Mock, patch
from odoo.exceptions import AccessError
from odoo.http import request_var, Response
from odoo.http.session import Session
from odoo.tests.common import TransactionCase, tagged, new_test_user
from odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip import Home
from odoo.addons.access_restriction_by_ip.controllers.session import AccessRestrict


@tagged('post_install', '-at_install')
class TestAccessRestrictionByIP(TransactionCase):
    """Test suite for validating IP address access restrictions during web login and session authentication."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a standard user without IP restrictions
        cls.user_unrestricted = new_test_user(
            cls.env,
            login='unrestricted_user',
            password='Password123!',
            name='Unrestricted User',
            groups='base.group_user',
        )

        # Create a user with IP restrictions
        cls.user_restricted = new_test_user(
            cls.env,
            login='restricted_user',
            password='Password123!',
            name='Restricted User',
            groups='base.group_user',
        )

        # Configure allowed IPs for restricted user
        cls.allowed_ip_1 = cls.env['allowed.ips'].create({
            'user_ip_id': cls.user_restricted.id,
            'ip_address': '192.168.1.100',
        })
        cls.allowed_ip_2 = cls.env['allowed.ips'].create({
            'user_ip_id': cls.user_restricted.id,
            'ip_address': '10.0.0.50',
        })

    def _setup_mock_request(self, client_ip, params=None, method='POST'):
        rendered_context = {}

        def mock_render(template, values=None):
            rendered_context.update(values or {})
            return Response("<html>Login Page</html>", status=200)

        def mock_redirect(url):
            return Response("Redirect", status=303, headers={'Location': url})

        fake_req = Mock(
            httprequest=Mock(
                environ={'REMOTE_ADDR': client_ip},
                method=method,
                url_root='http://localhost:8069/',
                url='http://localhost:8069/web/login',
            ),
            params=params or {},
            session=Session({'uid': None}, 'test_session_id'),
            env=self.env,
            db=self.env.cr.dbname,
            render=Mock(side_effect=mock_render),
            redirect=Mock(side_effect=mock_redirect),
            update_env=Mock(),
            _rendered_context=rendered_context,
        )
        request_reset = request_var.set(fake_req)
        self.addCleanup(request_var.reset, request_reset)
        return fake_req

    def test_01_models_and_relations(self):
        """Test model creation, relations, and cascade delete."""
        self.assertEqual(len(self.user_restricted.allowed_ip_ids), 2)
        self.assertIn('192.168.1.100', self.user_restricted.allowed_ip_ids.mapped('ip_address'))
        self.assertIn('10.0.0.50', self.user_restricted.allowed_ip_ids.mapped('ip_address'))

        # Unrestricted user has no IP records
        self.assertEqual(len(self.user_unrestricted.allowed_ip_ids), 0)

        # Adding a new IP
        new_ip = self.env['allowed.ips'].create({
            'user_ip_id': self.user_restricted.id,
            'ip_address': '172.16.0.1',
        })
        self.assertEqual(new_ip.user_ip_id, self.user_restricted)
        self.assertIn('172.16.0.1', self.user_restricted.allowed_ip_ids.mapped('ip_address'))

        # Deleting the record
        new_ip.unlink()
        self.assertNotIn('172.16.0.1', self.user_restricted.allowed_ip_ids.mapped('ip_address'))

    def test_02_web_login_unrestricted_user(self):
        """Unrestricted user can log in from any IP address."""
        fake_req = self._setup_mock_request(
            client_ip='203.0.113.195',
            params={'login': 'unrestricted_user', 'password': 'Password123!'},
        )
        home_ctrl = Home()
        func = getattr(Home.web_login, 'original_endpoint', Home.web_login)
        with patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.authenticate') as mock_auth, \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.ensure_db'), \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.db_list', return_value=['test_db']):
            mock_auth.return_value = {'uid': self.user_unrestricted.id}
            func(home_ctrl)
            mock_auth.assert_called_once()
            self.assertTrue(fake_req.params.get('login_success'))

    def test_03_web_login_restricted_user_allowed_ip(self):
        """Restricted user logging in from configured allowed IP succeeds."""
        # 1st allowed IP
        fake_req = self._setup_mock_request(
            client_ip='192.168.1.100',
            params={'login': 'restricted_user', 'password': 'Password123!'},
        )
        home_ctrl = Home()
        func = getattr(Home.web_login, 'original_endpoint', Home.web_login)
        with patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.authenticate') as mock_auth, \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.ensure_db'), \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.db_list', return_value=['test_db']):
            mock_auth.return_value = {'uid': self.user_restricted.id}
            func(home_ctrl)
            mock_auth.assert_called_once()
            self.assertTrue(fake_req.params.get('login_success'))

        # 2nd allowed IP
        fake_req2 = self._setup_mock_request(
            client_ip='10.0.0.50',
            params={'login': 'restricted_user', 'password': 'Password123!'},
        )
        with patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.authenticate') as mock_auth2, \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.ensure_db'), \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.db_list', return_value=['test_db']):
            mock_auth2.return_value = {'uid': self.user_restricted.id}
            func(home_ctrl)
            mock_auth2.assert_called_once()
            self.assertTrue(fake_req2.params.get('login_success'))

    def test_04_web_login_restricted_user_blocked_ip(self):
        """Restricted user logging in from an unauthorized IP is blocked."""
        fake_req = self._setup_mock_request(
            client_ip='198.51.100.22',
            params={'login': 'restricted_user', 'password': 'Password123!'},
        )
        home_ctrl = Home()
        func = getattr(Home.web_login, 'original_endpoint', Home.web_login)
        with patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.authenticate') as mock_auth, \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.ensure_db'), \
             patch('odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip.db_list', return_value=['test_db']):
            func(home_ctrl)
            # authenticate should NOT have been called because IP check blocked beforehand
            mock_auth.assert_not_called()
            self.assertFalse(fake_req.params.get('login_success'))
            # Check error message in rendered context
            self.assertEqual(fake_req._rendered_context.get('error'), 'Not allowed to login from this IP.')

    def test_05_session_authenticate_allowed_ip(self):
        """Session authenticate succeeds when IP is allowed."""
        fake_req = self._setup_mock_request(
            client_ip='192.168.1.100',
        )
        fake_req.session.uid = self.user_restricted.id
        session_ctrl = AccessRestrict()
        func = getattr(AccessRestrict.authenticate, 'original_endpoint', AccessRestrict.authenticate)
        with patch('odoo.addons.access_restriction_by_ip.controllers.session.authenticate') as mock_auth, \
             patch('odoo.addons.access_restriction_by_ip.controllers.session.db_filter', return_value=True), \
             patch('odoo.addons.access_restriction_by_ip.controllers.session.save_session'):
            mock_auth.return_value = {'uid': self.user_restricted.id}
            mock_http = Mock(session_info=Mock(return_value={'uid': self.user_restricted.id}))
            with patch.dict(self.env.registry.models, {'ir.http': mock_http}, clear=False):
                with patch.object(self.env['ir.http'], 'with_user', return_value=mock_http):
                    info = func(session_ctrl, db=self.env.cr.dbname, login='restricted_user', password='Password123!')
                    self.assertEqual(info['uid'], self.user_restricted.id)

    def test_06_session_authenticate_disallowed_ip(self):
        """Session authenticate raises AccessError when IP is not allowed."""
        fake_req = self._setup_mock_request(
            client_ip='198.51.100.99',
        )
        fake_req.session.uid = self.user_restricted.id
        session_ctrl = AccessRestrict()
        func = getattr(AccessRestrict.authenticate, 'original_endpoint', AccessRestrict.authenticate)
        with patch('odoo.addons.access_restriction_by_ip.controllers.session.authenticate') as mock_auth, \
             patch('odoo.addons.access_restriction_by_ip.controllers.session.db_filter', return_value=True), \
             patch('odoo.addons.access_restriction_by_ip.controllers.session.save_session'):
            mock_auth.return_value = {'uid': self.user_restricted.id}
            with self.assertRaises(AccessError) as cm:
                func(session_ctrl, db=self.env.cr.dbname, login='restricted_user', password='Password123!')
            self.assertIn('Not allowed to login from this IP', str(cm.exception))


    _CTRL = 'odoo.addons.access_restriction_by_ip.controllers.access_restriction_by_ip'

    def _call_login(self, fake_req, **kwargs):
        func = getattr(Home.web_login, 'original_endpoint', Home.web_login)
        with patch(f'{self._CTRL}.ensure_db'), \
                patch(f'{self._CTRL}.db_list', return_value=['test_db']), \
                patch(f'{self._CTRL}.og_title_from_path', return_value='Title'):
            return func(Home(), **kwargs)

    def test_07_login_get_with_session_redirects(self):
        """A logged-in GET request with a redirect target is redirected."""
        fake_req = self._setup_mock_request('127.0.0.1', method='GET')
        fake_req.session.uid = self.user_unrestricted.id
        response = self._call_login(fake_req, redirect='/odoo')
        self.assertEqual(response.status_code, 303)

    def test_08_login_wrong_password_and_custom_denied_message(self):
        """AccessDenied from authenticate is turned into an error message."""
        from odoo.exceptions import AccessDenied
        params = {'login': 'unrestricted_user', 'password': 'bad'}
        fake_req = self._setup_mock_request('127.0.0.1', params=params)
        with patch(f'{self._CTRL}.authenticate', side_effect=AccessDenied()):
            self._call_login(fake_req)
        self.assertEqual(fake_req._rendered_context['error'], 'Wrong login/password')

        fake_req = self._setup_mock_request('127.0.0.1', params=params)
        with patch(f'{self._CTRL}.authenticate', side_effect=AccessDenied('Custom denial')):
            self._call_login(fake_req)
        self.assertEqual(fake_req._rendered_context['error'], 'Custom denial')

    def test_09_login_get_error_access_and_opengraph(self):
        """GET with error=access and an /odoo redirect fills error and og values."""
        fake_req = self._setup_mock_request('127.0.0.1', params={'error': 'access'}, method='GET')
        fake_req.session['auth_login'] = 'saved_login'
        self._call_login(fake_req, redirect='/odoo/contacts')
        ctx = fake_req._rendered_context
        self.assertIn('Only employees', ctx['error'])
        self.assertEqual(ctx['login'], 'saved_login')
        self.assertTrue(ctx['disable_opengraph'])
        self.assertEqual(ctx['og_title'], 'Title')

    def test_10_login_opengraph_invalid_url_root(self):
        """An invalid url_root falls back to the request url for og_url."""
        fake_req = self._setup_mock_request('127.0.0.1', method='GET')
        with patch(f'{self._CTRL}.urljoin', side_effect=[ValueError('bad'), 'http://x/img']):
            self._call_login(fake_req, redirect='/odoo/contacts')
        self.assertEqual(fake_req._rendered_context['og_url'], 'http://localhost:8069/web/login')

    def test_11_login_db_list_access_denied(self):
        """A forbidden database list is reported as None."""
        from odoo.exceptions import AccessDenied
        fake_req = self._setup_mock_request('127.0.0.1', method='GET')
        func = getattr(Home.web_login, 'original_endpoint', Home.web_login)
        with patch(f'{self._CTRL}.ensure_db'), patch(f'{self._CTRL}.db_list', side_effect=AccessDenied()):
            func(Home())
        self.assertIsNone(fake_req._rendered_context['databases'])

    def test_12_session_authenticate_unknown_database(self):
        """Unknown databases are refused."""
        self._setup_mock_request('127.0.0.1')
        func = getattr(AccessRestrict.authenticate, 'original_endpoint', AccessRestrict.authenticate)
        with patch('odoo.addons.access_restriction_by_ip.controllers.session.db_filter', return_value=[]):
            with self.assertRaises(AccessError):
                func(AccessRestrict(), db='nope', login='x', password='y')

    def test_13_session_authenticate_uid_mismatch(self):
        """A renewed session for another uid returns an empty uid."""
        fake_req = self._setup_mock_request('192.168.1.100')
        fake_req.session.uid = None
        func = getattr(AccessRestrict.authenticate, 'original_endpoint', AccessRestrict.authenticate)
        with patch('odoo.addons.access_restriction_by_ip.controllers.session.authenticate',
                   return_value={'uid': self.user_restricted.id}), \
                patch('odoo.addons.access_restriction_by_ip.controllers.session.db_filter', return_value=True):
            res = func(AccessRestrict(), db=self.env.cr.dbname, login='restricted_user', password='Password123!')
        self.assertEqual(res, {'uid': None})

    def test_14_ip_address_validation(self):
        """Only valid IPv4 / IPv6 addresses can be saved."""
        from odoo.exceptions import ValidationError
        from odoo.tools import mute_logger
        for valid in ('192.168.0.1', '2001:db8::1'):
            self.env['allowed.ips'].create({'user_ip_id': self.user_unrestricted.id, 'ip_address': valid})
        for invalid in ('not-an-ip', '999.1.1.1', '1.2.3'):
            with self.assertRaises(ValidationError):
                self.env['allowed.ips'].create({'user_ip_id': self.user_unrestricted.id, 'ip_address': invalid})
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception), self.env.cr.savepoint():
            self.env['allowed.ips'].create({'user_ip_id': self.user_unrestricted.id, 'ip_address': False})

    def test_15_duplicate_ip_and_cascade_delete(self):
        """An IP can be listed once per user and goes away with its user."""
        from odoo.tools import mute_logger
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception), self.env.cr.savepoint():
            self.env['allowed.ips'].create({'user_ip_id': self.user_restricted.id, 'ip_address': '192.168.1.100'})
        ip_ids = self.user_restricted.allowed_ip_ids.ids
        self.user_restricted.unlink()
        self.assertFalse(self.env['allowed.ips'].browse(ip_ids).exists())

    def test_16_only_administrators_manage_ips(self):
        """Regular users cannot read, add or delete allowed IP rows."""
        from odoo.exceptions import AccessError
        as_user = self.env['allowed.ips'].with_user(self.user_restricted)
        with self.assertRaises(AccessError):
            as_user.search([])
        with self.assertRaises(AccessError):
            as_user.create({'user_ip_id': self.user_unrestricted.id, 'ip_address': '10.1.1.1'})
        with self.assertRaises(AccessError):
            self.allowed_ip_1.with_user(self.user_restricted).unlink()
        admin = new_test_user(self.env, login='ip_admin', groups='base.group_system')
        self.assertTrue(self.env['allowed.ips'].with_user(admin).search([]))
