# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase

class TestModelAccessRights(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Drop the NOT NULL constraint on autopost_bills at the database level if the account module 
        # is not loaded in the current test registry (avoiding NotNullViolation on res_partner).
        cls.env.cr.execute("""
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name='res_partner' AND column_name='autopost_bills' AND is_nullable='NO'
        """)
        if cls.env.cr.fetchone():
            cls.env.cr.execute("ALTER TABLE res_partner ALTER COLUMN autopost_bills DROP NOT NULL")

        # Find a model to restrict (e.g. res.partner)
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        # Get a standard user group with a XML ID (e.g. base.group_user)
        cls.user_group = cls.env.ref('base.group_user')
        
        # Create a test user for user-wise restrictions
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Access User',
            'login': 'test_access_user_unique',
            'email': 'test_access_user_unique@example.com',
        })
        
        # Safely assign the user group
        if hasattr(cls.test_user, 'groups_id'):
            cls.test_user.write({
                'groups_id': [(4, cls.user_group.id)]
            })

    def test_access_right_creation(self):
        """Test the creation of access.right records for both group and user wise restrictions"""
        # Group-wise restriction creation and field validation
        group_restriction = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.user_group.id,
            'is_delete': True,
            'is_export': True,
        })
        self.assertEqual(group_restriction.model_id, self.partner_model)
        self.assertEqual(group_restriction.restriction_type, 'group')
        self.assertEqual(group_restriction.groups_id, self.user_group)
        self.assertTrue(group_restriction.is_delete)
        self.assertTrue(group_restriction.is_export)
        self.assertFalse(group_restriction.is_create_or_update)
        self.assertFalse(group_restriction.is_archive)

        # User-wise restriction creation and field validation
        user_restriction = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.test_user.id,
            'is_create_or_update': True,
        })
        self.assertEqual(user_restriction.model_id, self.partner_model)
        self.assertEqual(user_restriction.restriction_type, 'user')
        self.assertEqual(user_restriction.user_id, self.test_user)
        self.assertTrue(user_restriction.is_create_or_update)
        self.assertFalse(user_restriction.is_delete)

    def test_hide_buttons_group_wise(self):
        """Test that hide_buttons returns the correct configuration for group-wise restrictions"""
        # Create restriction for res.partner model and user group
        restriction = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.user_group.id,
            'is_delete': True,
            'is_export': True,
        })

        res = self.env['access.right'].hide_buttons()
        # Find the record we just created in the list of results
        matching_res = [r for r in res if r['id'] == restriction.id]
        self.assertEqual(len(matching_res), 1)
        r = matching_res[0]

        self.assertEqual(r['model'], 'res.partner')
        self.assertEqual(r['restriction_type'], 'group')
        self.assertEqual(r['group_name'], 'group_user')
        self.assertEqual(r['module'], 'base')
        self.assertTrue(r['is_delete'])
        self.assertTrue(r['is_export'])
        self.assertFalse(r['is_create_or_update'])
        self.assertFalse(r['is_archive'])

    def test_hide_buttons_user_wise(self):
        """Test that hide_buttons returns the correct configuration for user-wise restrictions"""
        # Create restriction for res.partner model and test user
        restriction = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.test_user.id,
            'is_create_or_update': True,
            'is_archive': True,
        })

        res = self.env['access.right'].hide_buttons()
        matching_res = [r for r in res if r['id'] == restriction.id]
        self.assertEqual(len(matching_res), 1)
        r = matching_res[0]

        self.assertEqual(r['model'], 'res.partner')
        self.assertEqual(r['restriction_type'], 'user')
        self.assertEqual(r['user'][0], self.test_user.id)
        self.assertEqual(r['group_name'], False)
        self.assertEqual(r['module'], False)
        self.assertTrue(r['is_create_or_update'])
        self.assertTrue(r['is_archive'])
        self.assertFalse(r['is_delete'])
        self.assertFalse(r['is_export'])
