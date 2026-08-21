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


class TestArticlePermissions(TransactionCase):

    @classmethod
    def _create_partner(cls, name, email):
        vals = {'name': name, 'email': email}
        return cls.env['res.partner'].create(vals)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Test users
        cls.user_internal_partner = cls._create_partner('Internal User Partner', 'internal@example.com')
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_login',
            'partner_id': cls.user_internal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('info_hub.group_info_user').id])],
        })

        cls.user_portal_partner = cls._create_partner('Portal User Partner', 'portal@example.com')
        cls.user_portal = cls.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_login',
            'partner_id': cls.user_portal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        cls.user_shared_partner = cls._create_partner('Shared User Partner', 'shared@example.com')
        cls.user_shared = cls.env['res.users'].create({
            'name': 'Shared User',
            'login': 'shared_login',
            'partner_id': cls.user_shared_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_no_access_private(self):
        """Articles with default_access='none' are inaccessible to non-members."""
        article = self.env['info.hub.article'].create({
            'name': 'Private Article - None',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'none',
        })
        # Creator has access
        self.assertEqual(article._get_user_permission(article.create_uid), 'edit')
        # Non-member has no access
        self.assertEqual(article._get_user_permission(self.user_internal), 'none')
        
        # Test record rule access check
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            article.with_user(self.user_internal).check_access('read')

    def test_everyone_read(self):
        """Articles with default access Read and Everyone visibility are readable by all internal users."""
        article = self.env['info.hub.article'].create({
            'name': 'Everyone Read Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'read')
        
        # Test record rule access check (should not raise AccessError)
        self.env.invalidate_all()
        article.with_user(self.user_internal).check_access('read')
        # But write check should fail
        with self.assertRaises(AccessError):
            article.with_user(self.user_internal).write({'name': 'Should fail'})

    def test_everyone_edit(self):
        """Articles with default access Edit and Everyone visibility are editable by all internal users."""
        article = self.env['info.hub.article'].create({
            'name': 'Everyone Edit Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'edit',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'edit')
        
        # Test write check (should pass)
        self.env.invalidate_all()
        article.with_user(self.user_internal).write({'name': 'Allowed Name Change'})
        self.assertEqual(article.name, 'Allowed Name Change')

    def test_members_read(self):
        """Articles with Read/Members are only readable by members."""
        article = self.env['info.hub.article'].create({
            'name': 'Members Read Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })
        # Non-member has no access
        self.assertEqual(article._get_user_permission(self.user_internal), 'none')
        
        # Add internal user as a member
        self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_internal_partner.id,
            'permission': 'read',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'read')
        self.env.invalidate_all()
        article.with_user(self.user_internal).check_access('read')

    def test_members_edit(self):
        """Articles with Edit/Members are only editable by members."""
        article = self.env['info.hub.article'].create({
            'name': 'Members Edit Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'edit',
        })
        # Add internal user as a member
        self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_internal_partner.id,
            'permission': 'edit',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'edit')
        self.env.invalidate_all()
        article.with_user(self.user_internal).write({'name': 'Edited by Member'})

    def test_member_override(self):
        """Explicit member permissions override default permissions."""
        article = self.env['info.hub.article'].create({
            'name': 'Override Article',
            'category': 'private',
            'visibility': 'everyone',
            'default_access': 'edit',
        })
        # Although default access is edit, member permission restricts to read
        self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_internal_partner.id,
            'permission': 'read',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'read')
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            article.with_user(self.user_internal).write({'name': 'Should fail edit'})

    def test_portal_access(self):
        """Portal users can access shared articles matching internal user rules."""
        article = self.env['info.hub.article'].create({
            'name': 'Portal Shared Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })
        # Portal user gets 'none' since they aren't invited
        self.assertEqual(article._get_user_permission(self.user_portal), 'none')
        
        # Invite portal user
        self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_portal_partner.id,
            'permission': 'read',
        })
        self.assertEqual(article._get_user_permission(self.user_portal), 'read')
        self.env.invalidate_all()
        article.with_user(self.user_portal).check_access('read')

    def test_internal_access(self):
        """Internal shared users can access shared articles without workspace access."""
        # The user_shared is an internal user (base.group_user) but doesn't have info group
        article = self.env['info.hub.article'].create({
            'name': 'Internal Shared Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })
        # Prior to invitation, should fail
        with self.assertRaises(AccessError):
            article.with_user(self.user_shared).check_access('read')
            
        # Invite user
        self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_shared_partner.id,
            'permission': 'read',
        })
        self.env.invalidate_all()
        # Should now succeed without raising AccessError
        article.with_user(self.user_shared).check_access('read')

    def test_search_visibility(self):
        """Non-members cannot search/find private or members-only articles."""
        article_private = self.env['info.hub.article'].create({
            'name': 'Super Secret Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'none',
        })
        article_everyone = self.env['info.hub.article'].create({
            'name': 'Public Everyone Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
        })
        
        self.env.invalidate_all()
        # Search as self.user_internal
        searched = self.env['info.hub.article'].with_user(self.user_internal).search([])
        self.assertNotIn(article_private, searched)
        self.assertIn(article_everyone, searched)

    def test_sidebar_visibility(self):
        """Shared user sidebar lists only permitted articles."""
        article_shared = self.env['info.hub.article'].create({
            'name': 'Shared With Me Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'none',
        })
        self.env['info.hub.article.member'].create({
            'article_id': article_shared.id,
            'partner_id': self.user_shared_partner.id,
            'permission': 'read',
        })
        
        article_not_shared = self.env['info.hub.article'].create({
            'name': 'Other Private Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'none',
        })

        self.env.invalidate_all()
        sidebar_data = self.env['info.hub.article'].with_user(self.user_shared).get_shared_sidebar_data()
        # Check if only shared is in sidebar_data
        shared_ids = [a['id'] for a in sidebar_data.get('articles', [])]
        self.assertIn(article_shared.id, shared_ids)
        self.assertNotIn(article_not_shared.id, shared_ids)

    def test_url_access(self):
        """Route verification for various permission levels."""
        article = self.env['info.hub.article'].create({
            'name': 'URL Test Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
        })
        
        # Test controller access response redirect/rendering
        controller = InformationPublicController()
        
        # Mock request
        redirect_url = None
        class MockRequestRedirect:
            env = self.env(user=self.user_internal)
            @staticmethod
            def redirect(url):
                nonlocal redirect_url
                redirect_url = url
                return "redirected"

        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequestRedirect):
            res = controller.article_detail(article.id)
            self.assertEqual(redirect_url, f'/odoo/action-info_hub.action_info_client/{article.id}')

    def test_permission_removal(self):
        """Immediately revoking membership or changing access to 'none' revokes access."""
        article = self.env['info.hub.article'].create({
            'name': 'Revocable Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'none',
        })
        membership = self.env['info.hub.article.member'].create({
            'article_id': article.id,
            'partner_id': self.user_internal_partner.id,
            'permission': 'read',
        })
        self.assertEqual(article._get_user_permission(self.user_internal), 'read')
        
        # Revoke membership by writing 'none'
        membership.write({'permission': 'none'})
        self.assertEqual(article._get_user_permission(self.user_internal), 'none')
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            article.with_user(self.user_internal).check_access('read')
