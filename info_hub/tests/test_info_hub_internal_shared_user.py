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

class TestInternalSharedUser(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Clean up existing articles to avoid conflicts with demo data
        cls.env['info.hub.article'].sudo().search([]).unlink()

        # Helper to create partner
        def create_partner(name, email):
            vals = {'name': name, 'email': email}
            return cls.env['res.partner'].create(vals)

        # Internal user (Marc Demo style)
        cls.shared_partner = create_partner('Shared Internal Partner', 'shared_user@example.com')
        cls.shared_user = cls.env['res.users'].create({
            'name': 'Shared Internal User',
            'login': 'shared_user_login',
            'partner_id': cls.shared_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Regular internal user (not shared, not in info groups)
        cls.regular_partner = create_partner('Regular Partner', 'regular_user@example.com')
        cls.regular_user = cls.env['res.users'].create({
            'name': 'Regular User',
            'login': 'regular_user_login',
            'partner_id': cls.regular_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Information Admin user
        cls.admin_partner = create_partner('Admin Partner', 'admin_user@example.com')
        cls.admin_user = cls.env['res.users'].create({
            'name': 'Admin User',
            'login': 'admin_user_login',
            'partner_id': cls.admin_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('info_hub.group_info_admin').id])],
        })

        # Create some articles
        cls.article_1 = cls.env['info.hub.article'].create({
            'name': 'Article 1',
            'category': 'private',
            'visibility': 'members',
            'default_access': 'read',
        })
        cls.article_2 = cls.env['info.hub.article'].create({
            'name': 'Article 2',
            'category': 'workspace',
            'visibility': 'everyone',
            'default_access': 'read',
        })

    def test_01_auto_group_assignment(self):
        """Test that internal user automatically receives group_info_shared_user when invited."""
        shared_group = self.env.ref('info_hub.group_info_shared_user')
        self.assertFalse(self.shared_user.has_group('info_hub.group_info_shared_user'))

        # Add as member to Article 1
        self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.shared_partner.id,
            'permission': 'read',
        })

        self.assertTrue(self.shared_user.has_group('info_hub.group_info_shared_user'))

    def test_02_article_access_and_permissions(self):
        """Test invited article visibility, read-only and edit behavior, and permission withdrawal."""
        # Setup shared user group
        shared_group = self.env.ref('info_hub.group_info_shared_user')
        self.shared_user.write({'group_ids': [(4, shared_group.id)]})

        # Before invite, shared_user has no access to Article 1
        article_shared = self.article_1.with_user(self.shared_user)
        with self.assertRaises(AccessError):
            article_shared.read(['name', 'body'])

        # 1. Invite with read-only
        member = self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.shared_partner.id,
            'permission': 'read',
        })

        # Now they can read it
        data = article_shared.read(['name', 'body'])
        self.assertEqual(data[0]['name'], 'Article 1')

        # But they cannot write to it
        with self.assertRaises(AccessError):
            article_shared.write({'name': 'Changed Title'})

        # 2. Upgrade to edit permission
        member.write({'permission': 'edit'})
        
        # Now they can write to it
        article_shared.write({'name': 'Updated Article 1'})
        self.assertEqual(self.article_1.name, 'Updated Article 1')

        # 3. Withdraw permission (permission = 'none')
        member.write({'permission': 'none'})

        # Access should be denied again
        with self.assertRaises(AccessError):
            article_shared.read(['name', 'body'])

    def test_03_sidebar_and_metadata_helpers(self):
        """Test get_user_metadata and get_shared_sidebar_data."""
        # Setup shared user group
        shared_group = self.env.ref('info_hub.group_info_shared_user')
        self.shared_user.write({'group_ids': [(4, shared_group.id)]})

        # Invite to Article 1
        self.env['info.hub.article.member'].create({
            'article_id': self.article_1.id,
            'partner_id': self.shared_partner.id,
            'permission': 'read',
        })

        # Check metadata
        meta = self.env['info.hub.article'].with_user(self.shared_user).get_user_metadata()
        self.assertTrue(meta['is_shared_user'])
        self.assertFalse(meta['is_admin'])
        self.assertFalse(meta['is_info_user'])

        # Check sidebar data
        sidebar = self.env['info.hub.article'].with_user(self.shared_user).get_shared_sidebar_data()
        self.assertEqual(len(sidebar['articles']), 1)
        article_ids = [a['id'] for a in sidebar['articles']]
        self.assertIn(self.article_1.id, article_ids)
        self.assertNotIn(self.article_2.id, article_ids)

    def test_04_create_private_article_shared_user(self):
        """Test that shared user can create private article using the custom bypass helper."""
        shared_group = self.env.ref('info_hub.group_info_shared_user')
        self.shared_user.write({'group_ids': [(4, shared_group.id)]})

        # Create private article as shared user using helper
        new_article_id = self.env['info.hub.article'].with_user(self.shared_user).create_shared_user_private_article()
        self.assertTrue(new_article_id)

        new_article = self.env['info.hub.article'].browse(new_article_id)
        # Check permissions on this article for shared user
        permission = new_article._get_user_permission(self.shared_user)
        self.assertEqual(permission, 'edit')
