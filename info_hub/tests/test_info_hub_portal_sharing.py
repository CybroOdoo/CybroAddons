# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError
from odoo.addons.info_hub.controllers.info_hub import InformationPublicController
from unittest.mock import patch


class TestPortalSharing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Helper to create partner
        def create_partner(name, email):
            vals = {'name': name, 'email': email}
            return cls.env['res.partner'].create(vals)

        # Portal partner and user
        cls.portal_partner = create_partner('Portal User Partner', 'portal_user@example.com')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user_login',
            'partner_id': cls.portal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        # Internal user
        cls.internal_partner = create_partner('Internal Partner', 'internal_user@example.com')
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_user_login',
            'partner_id': cls.internal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Article 1: Private, Members visibility, default read
        cls.article_1 = cls.env['info.hub.article'].create({
            'name': 'Portal Shared Article 1',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })

        # Article 2: Public, Everyone visibility, default read
        cls.article_2 = cls.env['info.hub.article'].create({
            'name': 'Public Web Published Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
            'website_published': True,
        })

    def test_shared_article_count_compute(self):
        """Test res.users.shared_article_count compute logic."""
        # 1. No membership: shared_article_count should be 0
        self.assertEqual(self.portal_user.shared_article_count, 0)

        # 2. Invite to Article 1 with read permission
        membership = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'read',
        })
        self.portal_user.invalidate_recordset(['shared_article_count'])
        self.assertEqual(self.portal_user.shared_article_count, 1)

        # 3. Setting permission to 'none' reduces count back to 0
        membership.write({'permission': 'none'})
        self.portal_user.invalidate_recordset(['shared_article_count'])
        self.assertEqual(self.portal_user.shared_article_count, 0)

        # Clean up
        membership.unlink()

    def test_portal_user_access_rules(self):
        """Test portal user access rules via _can_access_portal."""
        # 1. No membership on private article -> False
        self.assertFalse(self.article_1._can_access_portal(self.portal_user))

        # 2. Add membership with read permission -> True
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'read',
        })
        self.assertTrue(self.article_1._can_access_portal(self.portal_user))

        # 3. Add membership with edit permission -> True
        member.write({'permission': 'edit'})
        self.assertTrue(self.article_1._can_access_portal(self.portal_user))

        # 4. Remove membership -> False
        member.unlink()
        self.assertFalse(self.article_1._can_access_portal(self.portal_user))

        # 5. Access to website published Everyone article -> True
        self.assertTrue(self.article_2._can_access_portal(self.portal_user))

    def test_anonymous_access_rules(self):
        """Test public/anonymous user access rules via _can_access_portal."""
        public_user = self.env.ref('base.public_user')
        
        # 1. Article 2 is published to Everyone -> True
        self.assertTrue(self.article_2._can_access_portal(public_user))

        # 2. Article 1 is private -> False
        self.assertFalse(self.article_1._can_access_portal(public_user))

    def test_record_rules_portal_access(self):
        """Verify that record rules correctly enforce portal isolation."""
        # Portal user cannot read private article without membership
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            self.article_1.with_user(self.portal_user).read(['name'])

        # Portal user gets membership -> can read article
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'read',
        })
        self.env.invalidate_all()
        
        # Succeeds
        self.assertEqual(self.article_1.with_user(self.portal_user).name, 'Portal Shared Article 1')

        # Clean up
        member.unlink()

    def test_portal_search_restriction(self):
        """Verify that portal users can only search accessible articles."""
        # Portal search for 'Portal' (matches Article 1)
        # Without membership, search returns empty list
        search_res = self.env['info.hub.article'].with_user(self.portal_user).search([('name', 'ilike', 'Portal')])
        self.assertNotIn(self.article_1, search_res)

        # Grant access
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'read',
        })
        self.env.invalidate_all()

        # With membership, search returns the article
        search_res = self.env['info.hub.article'].with_user(self.portal_user).search([('name', 'ilike', 'Portal')])
        self.assertIn(self.article_1, search_res)

        # Clean up
        member.unlink()

    def test_portal_controller_routing(self):
        """Test portal controller responses and redirects."""
        import werkzeug
        controller = InformationPublicController()

        # Mock odoo.http.request
        redirect_url = None
        rendered_template = None
        not_found_raised = False
        
        class MockRequest:
            env = self.env
            session = {}
            csrf_token = lambda: 'token'
            
            @staticmethod
            def redirect(url):
                nonlocal redirect_url
                redirect_url = url
                return werkzeug.Response(f"Redirect to {url}", status=302)

            @staticmethod
            def render(template, values=None):
                nonlocal rendered_template
                rendered_template = template
                return werkzeug.Response("rendered", status=200)

            @staticmethod
            def not_found():
                nonlocal not_found_raised
                not_found_raised = True
                return werkzeug.Response("Not Found", status=404)

        # 1. Internal User visiting /info/shared -> redirects to backend client action
        MockRequest.env = self.env(user=self.internal_user)
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            controller.info_shared()
            self.assertEqual(redirect_url, '/odoo/action-info_hub.action_info_client')

        # 2. Portal User visiting /info/shared
        # Mock user as portal user
        MockRequest.env = self.env(user=self.portal_user)
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            # No membership: welcome empty screen is rendered
            controller.info_shared()
            self.assertEqual(rendered_template, 'info_hub.info_portal_layout')

        # 3. Portal User visiting /info/article/<id> with access -> redirects to /info/shared?article_id=<id>
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'read',
        })
        self.env.invalidate_all()
        MockRequest.env = self.env(user=self.portal_user)
        redirect_url = None
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            controller.article_detail(self.article_1.id)
            self.assertEqual(redirect_url, f'/info/shared?article_id={self.article_1.id}')

        # 4. Portal User visiting /info/article/<id> without access -> 403
        member.unlink()
        self.env.invalidate_all()
        MockRequest.env = self.env(user=self.portal_user)
        rendered_template = None
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            controller.article_detail(self.article_1.id)
            self.assertEqual(rendered_template, 'http_routing.403')

        # 5. Public User visiting /info/article/<id> (website published) -> renders public view
        MockRequest.env = self.env(user=self.env.ref('base.public_user'))
        rendered_template = None
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            controller.article_detail(self.article_2.id)
            self.assertEqual(rendered_template, 'info_hub.public_article_view')

    def test_portal_controller_actions(self):
        """Test portal creation, save, and collaboration actions."""
        import werkzeug
        controller = InformationPublicController()

        redirect_url = None
        class MockRequest:
            env = self.env
            session = {}
            csrf_token = lambda: 'token'

            @staticmethod
            def redirect(url):
                nonlocal redirect_url
                redirect_url = url
                return werkzeug.Response(f"Redirect to {url}", status=302)

        # 1. Create a private article via controller
        MockRequest.env = self.env(user=self.portal_user)
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            controller.info_portal_create()
            self.assertTrue(redirect_url.startswith('/info/shared?article_id='))
            # Find the created article ID from redirect URL
            created_id = int(redirect_url.split('article_id=')[1])
            created_article = self.env['info.hub.article'].sudo().browse(created_id)
            self.assertEqual(created_article.name, 'Untitled')
            self.assertEqual(created_article.author_id, self.portal_user)
            self.assertEqual(created_article.category, 'private')

            # 2. Save/Edit the article name and body via controller
            # First, check that trying to save on article_1 (no access) returns Access Denied
            res = controller.info_portal_save(self.article_1.id, name='Modified Name')
            self.assertEqual(res.get('error'), 'Access Denied')

            # Now save on the created article (edit access since portal_user is author)
            res = controller.info_portal_save(created_article.id, name='My New Title', body='<p>Test Body</p>')
            self.assertEqual(res.get('success'), True)
            self.assertEqual(created_article.name, 'My New Title')
            self.assertEqual(created_article.body, '<p>Test Body</p>')

            # 3. Update Settings (visibility / default_access)
            res = controller.info_portal_update_settings(created_article.id, visibility='members', default_access='read')
            self.assertEqual(res.get('success'), True)
            self.assertEqual(created_article.visibility, 'members')
            self.assertEqual(created_article.default_access, 'read')

            # 4. Toggle published
            res = controller.info_portal_toggle_published(created_article.id, publish=True)
            self.assertEqual(res.get('success'), True)
            self.assertTrue(created_article.website_published)

            # 5. Search partners for invitation
            partners_res = controller.info_portal_search_partners(q='Internal')
            self.assertTrue(any(p['name'] == 'Internal User' for p in partners_res))

            # 6. Invite a partner (Internal Partner)
            res = controller.info_portal_invite(created_article.id, self.internal_partner.id, 'read')
            self.assertEqual(res.get('success'), True)
            member = created_article.member_ids.filtered(lambda m: m.partner_id == self.internal_partner)
            self.assertEqual(member.permission, 'read')

            # Remove invitation
            res = controller.info_portal_invite(created_article.id, self.internal_partner.id, 'none')
            self.assertEqual(res.get('success'), True)
            member = created_article.member_ids.filtered(lambda m: m.partner_id == self.internal_partner)
            self.assertFalse(member)

    def test_portal_guest_sharing_limits(self):
        """Test that guests (portal users invited to someone else's article with edit permission)
        are blocked from configuring public sharing, default access, visibility, and inviting members (except leaving).
        """
        import werkzeug
        controller = InformationPublicController()

        class MockRequest:
            env = self.env
            session = {}
            csrf_token = lambda: 'token'

        # 1. Mitchell Admin is the creator of article_1. Invite portal_user to article_1 with 'edit' permission.
        self.article_1.create_uid = self.env.ref('base.user_admin')
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.portal_partner.id,
            'permission': 'edit',
        })
        self.env.invalidate_all()

        # Mock request as portal_user (guest with edit permission on article_1)
        MockRequest.env = self.env(user=self.portal_user)
        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            # 2. Can edit the body (this is allowed!)
            res = controller.info_portal_save(self.article_1.id, name='Edit by Guest')
            self.assertEqual(res.get('success'), True)
            self.assertEqual(self.article_1.name, 'Edit by Guest')

            # 3. Cannot toggle published
            res = controller.info_portal_toggle_published(self.article_1.id, publish=True)
            self.assertIn('error', res)
            self.assertTrue(res['error'].startswith('Access Denied'))

            # 4. Cannot update settings (visibility/default_access)
            res = controller.info_portal_update_settings(self.article_1.id, visibility='everyone', default_access='edit')
            self.assertIn('error', res)
            self.assertTrue(res['error'].startswith('Access Denied'))

            # 5. Cannot invite other partners
            res = controller.info_portal_invite(self.article_1.id, self.internal_partner.id, 'read')
            self.assertIn('error', res)
            self.assertTrue(res['error'].startswith('Access Denied'))

            # 6. CAN leave the article (invite self with 'none' permission)
            res = controller.info_portal_invite(self.article_1.id, self.portal_partner.id, 'none')
            self.assertEqual(res.get('success'), True)
            # Verify membership is removed
            self.assertFalse(self.article_1.member_ids.filtered(lambda m: m.partner_id == self.portal_partner))
