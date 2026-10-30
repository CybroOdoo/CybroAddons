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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestModelAccessRights(TransactionCase):
    """Comprehensive test suite for model_access_rights module covering:
    - access.right model: field defaults, record creation, hide_buttons RPC method
    - create and write operations: restrictions by user, restrictions by group, batch create, admin exemption
    - unlink operation: restrictions by user, restrictions by group, empty recordset, admin exemption
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.category_model = cls.env['ir.model'].search([('model', '=', 'res.partner.category')], limit=1)

        # Create a test group with an ir.model.data XML ID entry
        cls.test_group = cls.env['res.groups'].create({'name': 'Test Restricted Group'})
        cls.test_group_data = cls.env['ir.model.data'].create({
            'module': 'model_access_rights',
            'name': 'test_restricted_group_xml_id',
            'model': 'res.groups',
            'res_id': cls.test_group.id,
        })

        # Create an orphan group without ir.model.data entry
        cls.orphan_group = cls.env['res.groups'].create({'name': 'Orphan Group No XMLID'})

        # Users setup
        partner_manager_group = cls.env.ref('base.group_partner_manager')
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted Test User',
            'login': 'restricted_user_test',
            'email': 'restricted_user@example.com',
            'group_ids': [(4, partner_manager_group.id)],
        })
        cls.group_user = cls.env['res.users'].create({
            'name': 'Group Member User',
            'login': 'group_member_user_test',
            'email': 'group_user@example.com',
            'group_ids': [
                (4, partner_manager_group.id),
                (4, cls.test_group.id),
            ],
        })
        cls.unrestricted_user = cls.env['res.users'].create({
            'name': 'Unrestricted User',
            'login': 'unrestricted_user_test',
            'email': 'unrestricted_user@example.com',
            'group_ids': [(4, partner_manager_group.id)],
        })

    def test_01_access_right_defaults_and_fields(self):
        """Test access.right field defaults, record creation, and relations."""
        rule = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'groups_id': self.test_group.id,
        })
        self.assertEqual(rule.restriction_type, 'group', "Default restriction_type should be 'group'")
        self.assertFalse(rule.is_delete)
        self.assertFalse(rule.is_export)
        self.assertFalse(rule.is_create_or_update)
        self.assertFalse(rule.is_archive)
        self.assertEqual(rule.display_name, self.partner_model.display_name)

        user_rule = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_delete': True,
            'is_export': True,
            'is_create_or_update': True,
            'is_archive': True,
        })
        self.assertEqual(user_rule.restriction_type, 'user')
        self.assertTrue(user_rule.is_delete)
        self.assertTrue(user_rule.is_export)
        self.assertTrue(user_rule.is_create_or_update)
        self.assertTrue(user_rule.is_archive)

    def test_02_hide_buttons_rpc(self):
        """Test hide_buttons RPC method for group and user restrictions."""
        # Clean existing test rules to ensure predictable output
        self.env['access.right'].search([]).unlink()

        # Rule 1: Group with ir.model.data
        r1 = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.test_group.id,
            'is_delete': True,
        })
        # Rule 2: Group without ir.model.data
        r2 = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.orphan_group.id,
            'is_export': True,
        })
        # Rule 3: Group with False groups_id
        r3 = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': False,
        })
        # Rule 4: User restriction
        r4 = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_create_or_update': True,
        })
        # Rule 5: User restriction with False user_id
        r5 = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': False,
        })

        results = self.env['access.right'].hide_buttons()
        res_by_id = {dic['id']: dic for dic in results}

        # Check Rule 1 (group with ir.model.data)
        d1 = res_by_id[r1.id]
        self.assertEqual(d1['model'], 'res.partner')
        self.assertEqual(d1['group_name'], 'test_restricted_group_xml_id')
        self.assertEqual(d1['module'], 'model_access_rights')

        # Check Rule 2 (group without ir.model.data)
        d2 = res_by_id[r2.id]
        self.assertFalse(d2['group_name'])
        self.assertFalse(d2['module'])

        # Check Rule 3 (groups_id is False)
        d3 = res_by_id[r3.id]
        self.assertFalse(d3['group_name'])
        self.assertFalse(d3['module'])

        # Check Rule 4 (user restriction)
        d4 = res_by_id[r4.id]
        self.assertEqual(d4['model'], 'res.partner')
        self.assertEqual(d4['restriction_type'], 'user')
        self.assertFalse(d4['group_name'])
        self.assertEqual(d4['user'][0], self.restricted_user.id)

        # Check Rule 5 (user restriction with False user_id)
        d5 = res_by_id[r5.id]
        self.assertFalse(d5['user'])

    def test_03_create_unrestricted_and_batch(self):
        """Test normal record creation and batch creation without restrictions."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()

        # Single record
        p1 = self.env['res.partner'].with_user(self.unrestricted_user).create({
            'name': 'Partner Unrestricted',
            'email': 'unrestricted@test.com',
        })
        self.assertTrue(p1.id)

        # Batch records
        partners = self.env['res.partner'].create([
            {'name': 'Batch Partner 1'},
            {'name': 'Batch Partner 2'},
        ])
        self.assertEqual(len(partners), 2)

        # Heterogeneous batch to test default values for omitted fields across records
        hetero_partners = self.env['res.partner'].create([
            {'name': 'Hetero 1', 'email': 'h1@example.com'},
            {'name': 'Hetero 2'},
        ])
        self.assertEqual(len(hetero_partners), 2)

        # Record with relational/inverse/parent store
        child = self.env['res.partner'].create({
            'name': 'Child Partner',
            'parent_id': p1.id,
        })
        self.assertEqual(child.parent_id, p1)

    def test_04_create_user_restriction_blocked(self):
        """Test record creation is blocked when user-specific restriction is active."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_create_or_update': True,
        })

        # Restricted user must be blocked
        with self.assertRaises(UserError) as cm:
            self.env['res.partner'].with_user(self.restricted_user).create({
                'name': 'Blocked Partner',
            })
        self.assertIn('restricted from performing this operation', str(cm.exception))

        # Unrestricted user should succeed
        p = self.env['res.partner'].with_user(self.unrestricted_user).create({
            'name': 'Allowed Partner',
        })
        self.assertTrue(p.id)

    def test_05_create_user_restriction_flag_false(self):
        """Test record creation succeeds if is_create_or_update is False."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_create_or_update': False,
        })

        p = self.env['res.partner'].with_user(self.restricted_user).create({
            'name': 'Flag False Partner',
        })
        self.assertTrue(p.id)

    def test_06_create_group_restriction_blocked(self):
        """Test record creation is blocked when group-specific restriction is active."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.test_group.id,
            'is_create_or_update': True,
        })

        # Group member must be blocked
        with self.assertRaises(UserError) as cm:
            self.env['res.partner'].with_user(self.group_user).create({
                'name': 'Blocked Group Partner',
            })
        self.assertIn('restricted from performing this operation', str(cm.exception))

        # Non-member should succeed
        p = self.env['res.partner'].with_user(self.unrestricted_user).create({
            'name': 'Allowed Non-Member Partner',
        })
        self.assertTrue(p.id)

    def test_07_create_group_restriction_orphan_group(self):
        """Test record creation succeeds when group has no ir.model.data entry."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        orphan_user = self.env['res.users'].create({
            'name': 'Orphan Group User',
            'login': 'orphan_group_user_test',
            'email': 'orphan_user@example.com',
            'group_ids': [
                (4, self.env.ref('base.group_partner_manager').id),
                (4, self.orphan_group.id),
            ],
        })
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.orphan_group.id,
            'is_create_or_update': True,
        })

        # Group data not found, so no restriction raised
        p = self.env['res.partner'].with_user(orphan_user).create({
            'name': 'Orphan Allowed Partner',
        })
        self.assertTrue(p.id)

    def test_08_internal_models_bypassed(self):
        """Test that internal models bypass custom access restriction checks."""
        access_group = self.env.ref('model_access_rights.model_access_rights_groups_configure_model_access')
        manager_user = self.env['res.users'].create({
            'name': 'Manager User Bypass Create',
            'login': 'manager_user_bypass_create',
            'group_ids': [(4, access_group.id)],
        })
        access_model = self.env['ir.model'].search([('model', '=', 'access.right')], limit=1)
        self.env['access.right'].create({
            'model_id': access_model.id,
            'restriction_type': 'user',
            'user_id': manager_user.id,
            'is_create_or_update': True,
        })
        rule = self.env['access.right'].with_user(manager_user).create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
        })
        self.assertTrue(rule.id)

    def test_09_unlink_empty_recordset(self):
        """Test unlink on empty recordset returns True immediately."""
        empty_records = self.env['res.partner'].browse([])
        self.assertTrue(empty_records.unlink())

    def test_10_unlink_unrestricted(self):
        """Test normal record deletion without restrictions."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        p = self.env['res.partner'].create({'name': 'Unlink Partner'})
        res = p.with_user(self.unrestricted_user).unlink()
        self.assertTrue(res)

    def test_11_unlink_user_restriction_blocked(self):
        """Test record deletion is blocked when user restriction is active."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_delete': True,
        })

        p = self.env['res.partner'].create({'name': 'Restricted Delete Partner'})
        with self.env.cr.savepoint():
            with self.assertRaises(UserError) as cm:
                p.with_user(self.restricted_user).unlink()
            self.assertIn('restricted from performing this operation', str(cm.exception))

        # Unrestricted user should succeed
        res = p.with_user(self.unrestricted_user).unlink()
        self.assertTrue(res)

    def test_12_unlink_user_restriction_flag_false(self):
        """Test record deletion succeeds if is_delete is False."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_delete': False,
        })

        p = self.env['res.partner'].create({'name': 'Allowed Delete Partner'})
        res = p.with_user(self.restricted_user).unlink()
        self.assertTrue(res)

    def test_13_unlink_group_restriction_blocked(self):
        """Test record deletion is blocked when group restriction is active."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.test_group.id,
            'is_delete': True,
        })

        p = self.env['res.partner'].create({'name': 'Group Delete Partner'})
        with self.env.cr.savepoint():
            with self.assertRaises(UserError) as cm:
                p.with_user(self.group_user).unlink()
            self.assertIn('restricted from performing this operation', str(cm.exception))

        # Non-member should succeed
        res = p.with_user(self.unrestricted_user).unlink()
        self.assertTrue(res)

    def test_14_unlink_group_restriction_orphan_group(self):
        """Test record deletion succeeds when group has no ir.model.data entry."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        orphan_user = self.env['res.users'].create({
            'name': 'Orphan Group User 2',
            'login': 'orphan_group_user_test_2',
            'email': 'orphan_user2@example.com',
            'group_ids': [
                (4, self.env.ref('base.group_partner_manager').id),
                (4, self.orphan_group.id),
            ],
        })
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'group',
            'groups_id': self.orphan_group.id,
            'is_delete': True,
        })

        p = self.env['res.partner'].create({'name': 'Orphan Group Partner'})
        res = p.with_user(orphan_user).unlink()
        self.assertTrue(res)

    def test_15_unlink_with_attachments_and_model_data(self):
        """Test deletion cleans up attached ir.attachment and ir.model.data records."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        partner = self.env['res.partner'].create({'name': 'Partner With Attached Data'})

        attachment = self.env['ir.attachment'].create({
            'name': 'test_attachment.txt',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'raw': b'Hello Attachment',
        })
        data = self.env['ir.model.data'].create({
            'module': 'model_access_rights',
            'name': 'test_partner_data',
            'model': 'res.partner',
            'res_id': partner.id,
        })

        res = partner.unlink()
        self.assertTrue(res)
        self.assertFalse(attachment.exists())
        self.assertFalse(data.exists())

    def test_16_unlink_internal_models_bypassed(self):
        """Test that unlink on internal models bypasses custom access restriction checks."""
        access_group = self.env.ref('model_access_rights.model_access_rights_groups_configure_model_access')
        manager_user = self.env['res.users'].create({
            'name': 'Manager User Bypass Unlink',
            'login': 'manager_user_bypass_unlink',
            'group_ids': [(4, access_group.id)],
        })
        access_model = self.env['ir.model'].search([('model', '=', 'access.right')], limit=1)
        self.env['access.right'].create({
            'model_id': access_model.id,
            'restriction_type': 'user',
            'user_id': manager_user.id,
            'is_delete': True,
        })
        rule = self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
        })
        self.assertTrue(rule.with_user(manager_user).unlink())

    def test_17_write_user_restriction_blocked(self):
        """Test write is blocked when user-specific is_create_or_update is active."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': self.restricted_user.id,
            'is_create_or_update': True,
        })
        partner = self.env['res.partner'].create({'name': 'Partner Before Write'})

        with self.assertRaises(UserError) as cm:
            partner.with_user(self.restricted_user).write({'name': 'Updated Blocked Name'})
        self.assertIn('restricted from performing this operation', str(cm.exception))

        # Unrestricted user can write
        res = partner.with_user(self.unrestricted_user).write({'name': 'Updated Allowed Name'})
        self.assertTrue(res)
        self.assertEqual(partner.name, 'Updated Allowed Name')

    def test_18_admin_exemption(self):
        """Test that administrators are exempt from create, write, and delete restrictions."""
        self.env['access.right'].search([('model_id', '=', self.partner_model.id)]).unlink()
        admin_user = self.env.ref('base.user_admin')
        self.env['access.right'].create({
            'model_id': self.partner_model.id,
            'restriction_type': 'user',
            'user_id': admin_user.id,
            'is_create_or_update': True,
            'is_delete': True,
        })

        # Admin create is allowed
        p = self.env['res.partner'].with_user(admin_user).create({'name': 'Admin Partner'})
        self.assertTrue(p.id)

        # Admin write is allowed
        res = p.with_user(admin_user).write({'name': 'Admin Partner Renamed'})
        self.assertTrue(res)

        # Admin delete is allowed
        del_res = p.with_user(admin_user).unlink()
        self.assertTrue(del_res)
