# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
from unittest.mock import patch
from odoo.exceptions import UserError
from odoo.tests import HttpCase, new_test_user, tagged
from .common import create_account

EXCHANGE_PATH = ('odoo.addons.google_drive_odoo_connector.models.'
                 'google_drive_account.GoogleDriveAccount.'
                 'exchange_authorization_code')
CONTROLLER_LOGGER = 'odoo.addons.google_drive_odoo_connector.controllers.main'


@tagged('post_install', '-at_install')
class TestGoogleDriveController(HttpCase):
    """Test cases for the routes defined in
    google_drive_odoo_connector/controllers/main.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = new_test_user(cls.env, login='gdrive_test_admin',
                                  groups='base.group_system')
        cls.env['google.drive.account'].search([]).write({'state': 'draft'})
        cls.account = create_account(cls.env)

    def setUp(self):
        super().setUp()
        self.authenticate(self.admin.login, self.admin.login)

    def _callback_url(self, code='abc', state=None):
        return '/google_drive/oauth/callback?code=%s&state=%s' % (
            code, state or self.account._get_oauth_state())

    def test_oauth_callback_requires_login(self):
        """The callback is not available to anonymous users."""
        self.authenticate(None, None)
        with patch(EXCHANGE_PATH) as exchange:
            self.url_open(self._callback_url(), allow_redirects=False)
        exchange.assert_not_called()

    def test_oauth_callback_error(self):
        """An error from Google is displayed as-is."""
        response = self.url_open(
            '/google_drive/oauth/callback?error=access_denied')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'access_denied')

    def test_oauth_callback_missing_code(self):
        """A callback without code is rejected."""
        response = self.url_open('/google_drive/oauth/callback?state=1')
        self.assertEqual(response.text, 'Authorization code missing.')

    def test_oauth_callback_missing_state(self):
        """A callback without state is rejected."""
        response = self.url_open('/google_drive/oauth/callback?code=abc')
        self.assertEqual(response.text, 'State missing.')

    def test_oauth_callback_invalid_state(self):
        """An unsigned or forged state is rejected."""
        for state in (str(self.account.id), '%s:forged' % self.account.id,
                      'not-a-number'):
            with patch(EXCHANGE_PATH) as exchange:
                response = self.url_open(self._callback_url(state=state))
            exchange.assert_not_called()
            self.assertEqual(response.status_code, 400)

    def test_oauth_callback_exchanges_code(self):
        """A valid callback exchanges the code and redirects to the account."""
        with patch(EXCHANGE_PATH, autospec=True) as exchange:
            response = self.url_open(self._callback_url(),
                                     allow_redirects=False)
        exchange.assert_called_once()
        self.assertEqual(exchange.call_args.args[0].id, self.account.id)
        self.assertEqual(exchange.call_args.args[1], 'abc')
        self.assertEqual(response.status_code, 303)
        self.assertIn('/odoo/action-google_drive_odoo_connector.'
                      'action_google_drive_config/%s' % self.account.id,
                      response.headers['Location'])

    def test_oauth_callback_exchange_error_still_redirects(self):
        """A failing exchange is logged and the user is still redirected."""
        with patch(EXCHANGE_PATH, side_effect=UserError('boom')), \
                self.assertLogs(CONTROLLER_LOGGER, level='WARNING'):
            response = self.url_open(self._callback_url(),
                                     allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.account.invalidate_recordset(['state'])
        self.assertEqual(self.account.state, 'error')
