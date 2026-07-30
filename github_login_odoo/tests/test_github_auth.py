# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

class TestGithubAuth(TransactionCase):

    def setUp(self):
        super(TestGithubAuth, self).setUp()
        self.ResUsers = self.env['res.users']
        self.portal_group = self.env.ref('base.group_portal')
        
        # Setup mock OAuth provider
        self.provider = self.env['auth.oauth.provider'].create({
            'name': 'GitHub Test',
            'client_id': 'test_client_id',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'scope': 'user:email',
            'validation_endpoint': 'https://api.github.com/user',
            'data_endpoint': '',
            'css_class': 'fa-github',
            'enabled': True,
            'body': 'Log in with GitHub',
        })
        
        # Create an existing user to test linking
        self.existing_email = 'test_linking@example.com'
        self.existing_user = self.ResUsers.create({
            'name': 'Existing Linked User',
            'login': self.existing_email,
            'email': self.existing_email,
        })
        
    def test_01_github_user_linking(self):
        """ Test that an existing user is properly linked without throwing duplicate email error """
        validation = {
            'user_id': 1234567, # Mock OAuth UID
            'email': self.existing_email,
            'name': 'Existing Linked User'
        }
        
        params = {
            'access_token': 'test_access_token'
        }
        
        # Call the signin logic with GitHub context
        login = self.ResUsers.with_context(github=True)._auth_oauth_signin(
            self.provider.id, validation, params
        )
        
        self.assertEqual(login, self.existing_email, "Should return existing user's login")
        
        # Verify the user actually got linked
        linked_user = self.ResUsers.search([('login', '=', self.existing_email)])
        self.assertEqual(linked_user.oauth_provider_id.id, self.provider.id)
        self.assertEqual(linked_user.oauth_uid, '1234567')
        self.assertEqual(linked_user.oauth_access_token, 'test_access_token')

    def test_02_github_portal_signup(self):
        """ Test that a completely new GitHub user is forcefully created as a portal user """
        new_email = 'new_github_user@example.com'
        
        # In Odoo standard auth_oauth, creating a user calls _signup_create_user
        values = {
            'name': 'New GitHub User',
            'login': new_email,
            'email': new_email,
            'oauth_provider_id': self.provider.id,
            'oauth_uid': '999888',
        }
        
        new_user = self.ResUsers.with_context(github=True)._signup_create_user(values)
        
        # Verify user creation
        self.assertTrue(new_user)
        self.assertEqual(new_user.login, new_email)
        
        # Verify portal group is explicitly present
        self.assertIn(self.portal_group, new_user.groups_id, "User should be assigned to the Portal group")
