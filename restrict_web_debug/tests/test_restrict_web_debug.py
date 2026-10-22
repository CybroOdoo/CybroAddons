# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestRestrictWebDebug(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test users: one without the restrict group, one with
        cls.test_user_without_group = new_test_user(
            cls.env,
            login='test_without_restrict_debug',
            groups='base.group_user',
            password='password',
        )
        cls.test_user_with_group = new_test_user(
            cls.env,
            login='test_with_restrict_debug',
            groups='base.group_user,restrict_web_debug.restrict_debug_mode',
            password='password',
        )
        cls.env['res.users.settings']._find_or_create_for_user(cls.test_user_without_group)
        cls.env['res.users.settings']._find_or_create_for_user(cls.test_user_with_group)

    def test_session_info_without_group(self):
        """Test session info when user does not have the restrict_debug_mode group."""
        self.authenticate(self.test_user_without_group.login, 'password')
        response = self.make_jsonrpc_request('/web/session/get_session_info', {})
        self.assertIn('user_group', response)
        self.assertIs(response['user_group'], False)

    def test_session_info_with_group(self):
        """Test session info when user has the restrict_debug_mode group."""
        self.authenticate(self.test_user_with_group.login, 'password')
        response = self.make_jsonrpc_request('/web/session/get_session_info', {})
        self.assertIn('user_group', response)
        self.assertIs(response['user_group'], True)
        bundle_params = response.get('bundle_params', {})
        self.assertNotIn('debug', bundle_params)

    def test_debug_mode_url_restriction(self):
        """Test that ?debug=1 enables debug mode only for unrestricted users.

        The session is read back from the session store through the response,
        as the test's local ``self.session`` is not updated by the server.
        """
        self.authenticate(self.test_user_without_group.login, 'password')
        response = self.url_open('/odoo?debug=1')
        self.assertEqual(response.session.debug, '1')

        self.authenticate(self.test_user_with_group.login, 'password')
        response = self.url_open('/odoo?debug=1')
        self.assertEqual(response.session.debug, '')

    def test_technical_menus_and_features_blocked(self):
        """Test that technical features and technical menus are inaccessible for restricted users."""
        self.assertFalse(
            self.test_user_with_group.has_group('base.group_no_one'),
            "Restricted user must never have access to base.group_no_one"
        )
        menus = self.env['ir.ui.menu'].with_user(self.test_user_with_group).load_web_menus(debug='1')
        technical_group = self.env.ref('base.group_no_one', raise_if_not_found=False)

        if technical_group:
            tech_menu_records = self.env['ir.ui.menu'].search([
                ('group_ids', 'in', [technical_group.id]),
            ])
            for tech_menu in tech_menu_records:
                self.assertNotIn(
                    tech_menu.id,
                    menus,
                    f"Technical menu {tech_menu.name} should not be accessible to restricted user"
                )

    def test_tour_debug_menu_hidden_for_restricted_user(self):
        """Tour test verifying that .o_debug_manager is hidden in the UI for restricted users."""
        self.start_tour(
            "/odoo?debug=1",
            "restrict_web_debug_tour",
            login=self.test_user_with_group.login,
        )

    def test_tour_debug_menu_visible_for_unrestricted_user(self):
        """Tour test verifying that .o_debug_manager is shown in the UI for unrestricted users in debug mode."""
        self.start_tour(
            "/odoo?debug=1",
            "unrestricted_web_debug_tour",
            login=self.test_user_without_group.login,
        )
