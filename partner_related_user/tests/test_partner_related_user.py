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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPartnerRelatedUser(common.TransactionCase):
    """Test suite for Partner Related User and User Filters."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_without_user = cls.env['res.partner'].create({
            'name': 'Partner Without User',
            'email': 'without_user@test.com',
        })

        cls.partner_with_user = cls.env['res.partner'].create({
            'name': 'Partner With User',
            'email': 'with_user@test.com',
        })
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Related User',
            'login': 'test_related_user_login',
            'partner_id': cls.partner_with_user.id,
        })

    def test_partner_computed_related_user(self):
        """Test computed related_user_id and is_have_user on partners."""
        # Computed immediately on creation without calling get_views
        self.assertEqual(self.partner_with_user.related_user_id, self.test_user)
        self.assertTrue(self.partner_with_user.is_have_user)

        self.assertFalse(self.partner_without_user.related_user_id)
        self.assertFalse(self.partner_without_user.is_have_user)

        # Standard get_views returns valid view dictionary without error
        views = [(False, 'list'), (False, 'form')]
        res = self.env['res.partner'].get_views(views)
        self.assertIsInstance(res, dict)
        self.assertIn('views', res)

    def test_partner_change_user_clears_old_partner(self):
        """When a user's partner_id changes, the old partner is automatically cleared."""
        new_partner = self.env['res.partner'].create({
            'name': 'New Target Partner',
            'email': 'new_target@test.com',
        })
        # Move user from partner_with_user to new_partner
        self.test_user.partner_id = new_partner.id

        self.partner_with_user.invalidate_recordset()
        new_partner.invalidate_recordset()

        self.assertFalse(self.partner_with_user.related_user_id)
        self.assertFalse(self.partner_with_user.is_have_user)
        self.assertEqual(new_partner.related_user_id, self.test_user)
        self.assertTrue(new_partner.is_have_user)

    def test_partner_user_removal_clears_fields(self):
        """When a related user is deleted, the partner's fields are automatically cleared."""
        partner = self.env['res.partner'].create({
            'name': 'Partner For Deletion Test',
            'email': 'deletion_test@test.com',
        })
        user = self.env['res.users'].create({
            'name': 'User To Delete',
            'login': 'user_to_delete_login',
            'partner_id': partner.id,
        })
        self.assertEqual(partner.related_user_id, user)
        self.assertTrue(partner.is_have_user)

        # Delete the user
        user.unlink()
        partner.invalidate_recordset()

        self.assertFalse(partner.related_user_id)
        self.assertFalse(partner.is_have_user)

    def test_partner_user_deactivation_clears_fields(self):
        """When a related user is deactivated (active=False), fields update accordingly."""
        partner = self.env['res.partner'].create({
            'name': 'Partner For Deactivation Test',
            'email': 'deactivation_test@test.com',
        })
        user = self.env['res.users'].create({
            'name': 'User To Deactivate',
            'login': 'user_to_deactivate_login',
            'partner_id': partner.id,
        })
        self.assertEqual(partner.related_user_id, user)
        self.assertTrue(partner.is_have_user)

        user.active = False
        partner.invalidate_recordset()
        self.assertFalse(partner.related_user_id)
        self.assertFalse(partner.is_have_user)

        user.active = True
        partner.invalidate_recordset()
        self.assertEqual(partner.related_user_id, user)
        self.assertTrue(partner.is_have_user)

    def test_partner_search_filters(self):
        """Test searching partners with the is_have_user and related_user_id filters."""
        partners_with_users = self.env['res.partner'].search([
            ('id', 'in', [self.partner_with_user.id, self.partner_without_user.id]),
            ('is_have_user', '!=', False),
        ])
        self.assertIn(self.partner_with_user, partners_with_users)
        self.assertNotIn(self.partner_without_user, partners_with_users)

        partners_by_user = self.env['res.partner'].search([
            ('related_user_id', '=', self.test_user.id),
        ])
        self.assertIn(self.partner_with_user, partners_by_user)

    def test_users_filter_booleans_and_get_views(self):
        """Test module filter boolean fields and get_views on res.users."""
        views = [(False, 'list'), (False, 'form')]
        res = self.env['res.users'].get_views(views)
        self.assertIsInstance(res, dict)
        self.assertIn('views', res)

        field_names = [
            'sales_user',
            'invoice_user',
            'purchase_user',
            'website_user',
            'inventory_user',
            'pos_user',
            'project_user',
            'manufacturing_user',
        ]
        for field in field_names:
            self.assertIsInstance(getattr(self.test_user, field), bool)

        for field in field_names:
            users = self.env['res.users'].search([
                (field, '!=', False)
            ])
            self.assertIsInstance(users, type(self.env['res.users']))

    def test_user_module_group_computation(self):
        """Test that user module filter booleans recompute automatically with groups."""
        categories = {
            'sales_user': 'base.module_category_sales_sales',
            'invoice_user': 'base.module_category_accounting_accounting',
            'purchase_user': 'base.module_category_inventory_purchase',
            'website_user': 'base.module_category_website_website',
            'inventory_user': 'base.module_category_inventory_inventory',
            'pos_user': 'base.module_category_sales_point_of_sale',
            'project_user': 'base.module_category_services_project',
            'manufacturing_user': 'base.module_category_manufacturing_manufacturing',
        }

        user = self.env['res.users'].create({
            'name': 'Multi Category Test User',
            'login': 'multi_category_test_login',
        })

        for field_name, cat_xml_id in categories.items():
            category = self.env.ref(cat_xml_id, raise_if_not_found=False)
            if not category:
                continue

            privilege = self.env['res.groups.privilege'].create({
                'name': f'Privilege for {field_name}',
                'category_id': category.id,
            })
            group = self.env['res.groups'].create({
                'name': f'Group for {field_name}',
                'privilege_id': privilege.id,
            })

            # Assign group
            user.write({'group_ids': [(4, group.id)]})
            user.invalidate_recordset([field_name])
            self.assertTrue(
                getattr(user, field_name),
                f"Expected {field_name} to be True after adding group for {cat_xml_id}"
            )

            # Remove group
            user.write({'group_ids': [(3, group.id)]})
            user.invalidate_recordset([field_name])
            self.assertFalse(
                getattr(user, field_name),
                f"Expected {field_name} to be False after removing group for {cat_xml_id}"
            )
