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
from odoo.exceptions import UserError, AccessError


class TestArticleSharing(TransactionCase):

    @classmethod
    def _create_partner(cls, name, email):
        vals = {'name': name, 'email': email}
        return cls.env['res.partner'].create(vals)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Clean up existing articles to avoid conflicts with demo data
        cls.env['info.hub.article'].sudo().search([]).unlink()

        # Owner user (Admin)
        cls.admin_user = cls.env.ref('base.user_admin')

        # Test Article 1: Public, Everyone, default read
        cls.article_1 = cls.env['info.hub.article'].create({
            'name': 'Article 1',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
            'body': '<p>Body 1</p>',
        })

        # Test Article 2: Public, Members, default read
        cls.article_2 = cls.env['info.hub.article'].create({
            'name': 'Article 2',
            'category': 'workspace',
            'visibility': 'members',
            'default_access': 'read',
            'body': '<p>Body 2</p>',
        })

        # Create two test users
        cls.partner_a = cls._create_partner('User A Partner', 'usera@example.com')
        cls.user_a = cls.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a',
            'partner_id': cls.partner_a.id,
            'group_ids': [(6, 0, [cls.env.ref('info_hub.group_info_user').id])],
        })

        cls.partner_b = cls._create_partner('User B Partner', 'userb@example.com')
        cls.user_b = cls.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b',
            'partner_id': cls.partner_b.id,
            'group_ids': [(6, 0, [cls.env.ref('info_hub.group_info_user').id])],
        })

    def test_owner_permissions(self):
        """Test that the owner always has full edit rights and cannot be removed/changed."""
        # Creator of article_1 is the owner
        owner_user = self.article_1.create_uid
        self.assertEqual(self.article_1._get_user_permission(owner_user), 'edit')

        # Try to add a member record for the owner with 'read' permission
        owner_member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': owner_user.partner_id.id,
            'permission': 'edit',
        })

        # Verify writing read/none raises UserError
        with self.assertRaises(UserError):
            owner_member.write({'permission': 'read'})
        with self.assertRaises(UserError):
            owner_member.write({'permission': 'none'})

        # Verify deleting raises UserError
        with self.assertRaises(UserError):
            owner_member.unlink()

    def test_access_algorithm_priority(self):
        """Verify the Access Algorithm priorities."""
        # 1. Non-member, visibility = everyone, default_access = read
        self.assertEqual(self.article_1._get_user_permission(self.user_a), 'read')

        # 2. Member permission overrides default visibility
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.partner_a.id,
            'permission': 'edit',
        })
        self.assertEqual(self.article_1._get_user_permission(self.user_a), 'edit')

        # 3. Explicit 'none' permission overrides everything
        member.write({'permission': 'none'})
        self.assertEqual(self.article_1._get_user_permission(self.user_a), 'none')

        # 4. Visibility = members: non-member gets 'none'
        self.assertEqual(self.article_2._get_user_permission(self.user_b), 'none')

    def test_join_behavior(self):
        """Test action_join_article adds the user with default_access."""
        # User B joins Article 2 (visibility = members, default = read)
        self.article_2.with_user(self.user_b).action_join_article()
        
        # Verify User B is now a member
        member = self.env['info.hub.article.member'].search([
            ('article_id', '=', self.article_2.id),
            ('partner_id', '=', self.partner_b.id)
        ])
        self.assertTrue(member.exists())
        self.assertEqual(member.permission, 'read')
        self.assertEqual(self.article_2._get_user_permission(self.user_b), 'read')

    def test_invite_logic(self):
        """Test that invite_members adds members without duplicates."""
        # Invite User A to Article 1 with 'edit'
        self.article_1.invite_members([self.partner_a.id], 'edit')
        member = self.env['info.hub.article.member'].search([
            ('article_id', '=', self.article_1.id),
            ('partner_id', '=', self.partner_a.id)
        ])
        self.assertEqual(len(member), 1)
        self.assertEqual(member.permission, 'edit')

        # Invite again with 'read' (updates existing membership)
        self.article_1.invite_members([self.partner_a.id], 'read')
        self.assertEqual(len(member), 1)
        self.assertEqual(member.permission, 'read')

    def test_record_rules_read(self):
        """Verify record rules prevent read access for blocked members."""
        # User A has 'none' permission on Article 1
        self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.partner_a.id,
            'permission': 'none',
        })

        # User A cannot read Article 1
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            self.article_1.with_user(self.user_a).check_access('read')

        # User B (not a member) CAN read Article 1 (visibility Everyone)
        self.assertTrue(self.article_1.with_user(self.user_b).read(['name']))

    def test_record_rules_write(self):
        """Verify record rules restrict write access to editors only."""
        # User A is member with 'read' only -> write raises AccessError
        self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.partner_a.id,
            'permission': 'read',
        })
        with self.assertRaises(AccessError):
            self.article_1.with_user(self.user_a).write({'name': 'New Title'})

        # User B is member with 'edit' -> write succeeds
        self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.partner_b.id,
            'permission': 'edit',
        })
        self.article_1.with_user(self.user_b).write({'name': 'User B Title'})
        self.assertEqual(self.article_1.name, 'User B Title')

    def test_workspace_less_user_article_access(self):
        """Verify that an internal user without Information User group:
        1. Cannot read private article by default.
        2. Can read/edit the article after being invited (membership is created).
        3. Can read 'category' without triggering an AccessError.
        """
        # Create an internal user without the Information User group (only base.group_user)
        internal_user = self.env['res.users'].create({
            'name': 'Internal User No Workspace',
            'login': 'internal_no_workspace',
            'partner_id': self._create_partner('Internal User No Workspace Partner', 'internal_no_workspace@example.com').id,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # 1. Assert that the internal user cannot read a private article by default
        private_article = self.env['info.hub.article'].create({
            'name': 'Workspace-less Private Article',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })
        with self.assertRaises(AccessError):
            private_article.with_user(internal_user).check_access('read')

        # 2. Invite the internal user to the private article with read permission
        self.env['info.hub.article.member'].create({
            'article_id': private_article.id,
            'partner_id': internal_user.partner_id.id,
            'permission': 'read',
        })

        # 3. Invalidate cache to force reloading from database under the user context
        self.env.invalidate_all()

        # 4. Assert the internal user can read the article (no AccessError)
        article_under_user = private_article.with_user(internal_user)
        self.assertEqual(article_under_user.name, 'Workspace-less Private Article')

        # 5. Assert reading 'category' returns the correct value
        res = article_under_user.read(['name', 'category'])
        self.assertTrue(res)
        self.assertEqual(res[0]['category'], 'shared')

    def test_sharing_controller_internal_user_redirect(self):
        """Verify that visiting the public route redirects an internal user to backend action/resId."""
        from odoo.addons.info_hub.controllers.info_hub import InformationPublicController
        from unittest.mock import patch

        controller = InformationPublicController()
        
        # Create an article
        article = self.env['info.hub.article'].create({
            'name': 'Redirect Test Article',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
        })

        # Internal user
        internal_user = self.env['res.users'].create({
            'name': 'Internal User Redirect',
            'login': 'internal_redirect',
            'partner_id': self._create_partner('Internal Partner', '').id,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Mock odoo.http.request
        redirect_url = None
        class MockRequest:
            env = self.env(user=internal_user)
            @staticmethod
            def redirect(url):
                nonlocal redirect_url
                redirect_url = url
                from odoo.http import Response
                return Response("redirected")

        with patch('odoo.addons.info_hub.controllers.info_hub.request', MockRequest):
            res = controller.article_detail(article.id)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(
                redirect_url,
                f'/odoo/action-info_hub.action_info_client/{article.id}'
            )
