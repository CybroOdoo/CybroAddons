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
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestPartnerRelation(TransactionCase):
    """Unit tests for Partner Relation management and reciprocal synchronization."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.PartnerRelation = cls.env['partner.relation']
        cls.RelationType = cls.env['relation.type']
        cls.RelationCategory = cls.env['relation.type.category']

        cls.category_family = cls.RelationCategory.create({'name': 'Family Test'})
        cls.category_work = cls.RelationCategory.create({'name': 'Work Test'})

        cls.type_father = cls.RelationType.create({
            'name': 'Father Test',
            'category_id': cls.category_family.id,
        })
        cls.type_son = cls.RelationType.create({
            'name': 'Son Test',
            'category_id': cls.category_family.id,
        })
        cls.type_manager = cls.RelationType.create({
            'name': 'Manager Test',
            'category_id': cls.category_work.id,
        })
        cls.type_employee = cls.RelationType.create({
            'name': 'Employee Test',
            'category_id': cls.category_work.id,
        })

        cls.partner_a = cls.Partner.create({
            'name': 'Partner A',
            'email': 'partner_a@test.com',
            'phone': '1234567890',
        })
        cls.partner_b = cls.Partner.create({
            'name': 'Partner B',
            'email': 'partner_b@test.com',
            'phone': '0987654321',
        })
        cls.partner_c = cls.Partner.create({
            'name': 'Partner C',
            'email': 'partner_c@test.com',
            'phone': '5555555555',
        })

    def test_check_self_relation(self):
        """Test that a contact cannot create a relationship with itself."""
        with self.assertRaises(ValidationError):
            self.PartnerRelation.create({
                'contact_id': self.partner_a.id,
                'relation_contact_id': self.partner_a.id,
                'relation_type_id': self.type_father.id,
                'reverse_relation_type_id': self.type_son.id,
            })

    def test_reciprocal_creation(self):
        """Test that creating a relationship creates its symmetric reciprocal record."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })

        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertEqual(len(reciprocal), 1)
        self.assertEqual(reciprocal.relation_type_id, self.type_son)
        self.assertEqual(reciprocal.reverse_relation_type_id, self.type_father)

        # Related display fields
        self.assertEqual(rel.relation_name, 'Partner B')
        self.assertEqual(rel.relation_email, 'partner_b@test.com')
        self.assertEqual(rel.relation_phone, '0987654321')

    def test_create_with_no_reverse_creation_context(self):
        """Test that no_reverse_creation context bypasses reciprocal creation."""
        self.PartnerRelation.with_context(no_reverse_creation=True).create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_c.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })

        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_c.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertFalse(reciprocal)

    def test_create_when_reciprocal_already_exists(self):
        """Test reciprocal is not duplicated if it already exists."""
        # Create reciprocal manually first
        self.PartnerRelation.with_context(no_reverse_creation=True).create({
            'contact_id': self.partner_b.id,
            'relation_contact_id': self.partner_a.id,
            'relation_type_id': self.type_son.id,
            'reverse_relation_type_id': self.type_father.id,
        })

        # Create the primary record
        self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })

        reciprocals = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertEqual(len(reciprocals), 1)

    def test_find_symmetric_reverse_relation(self):
        """Test _find_symmetric_reverse_relation finds the reciprocal record."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        reverse = rel._find_symmetric_reverse_relation()
        self.assertEqual(len(reverse), 1)
        self.assertEqual(reverse.contact_id, self.partner_b)
        self.assertEqual(reverse.relation_contact_id, self.partner_a)
        self.assertEqual(reverse.relation_type_id, self.type_son)

    def test_write_key_fields_updates_reciprocal(self):
        """Test writing key fields updates and re-creates reciprocal relationship."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })

        # Update relation types to manager / employee
        rel.write({
            'relation_type_id': self.type_manager.id,
            'reverse_relation_type_id': self.type_employee.id,
        })

        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertEqual(len(reciprocal), 1)
        self.assertEqual(reciprocal.relation_type_id, self.type_employee)
        self.assertEqual(reciprocal.reverse_relation_type_id, self.type_manager)

    def test_write_with_no_reverse_update_context(self):
        """Test write with no_reverse_update context bypasses reciprocal re-creation."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })

        rel.with_context(no_reverse_update=True).write({
            'relation_type_id': self.type_manager.id,
        })

        # The reciprocal still has the old type
        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertEqual(reciprocal.relation_type_id, self.type_son)

    def test_write_non_key_fields(self):
        """Test write without modifying key fields."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        res = rel.write({})
        self.assertTrue(res)

    def test_unlink_reciprocal(self):
        """Test deleting a relation record also deletes its reciprocal."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        rel.unlink()

        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertFalse(reciprocal)

    def test_unlink_with_no_reverse_unlink_context(self):
        """Test deleting with no_reverse_unlink context does not unlink reciprocal."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        rel.with_context(no_reverse_unlink=True).unlink()

        reciprocal = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        self.assertTrue(reciprocal)

    def test_open_related_contact(self):
        """Test open_related_contact action."""
        rel = self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        action = rel.open_related_contact()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'res.partner')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('res_id'), self.partner_b.id)

        # Test empty recordset handling (avoids Expected singleton ValueError)
        empty_rel = self.PartnerRelation.browse()
        self.assertFalse(empty_rel.open_related_contact())

        # Test resolution from context active_id
        ctx_action = empty_rel.with_context(
            active_model='partner.relation',
            active_id=rel.id
        ).open_related_contact()
        self.assertEqual(ctx_action.get('res_id'), self.partner_b.id)

        # Test resolution from default_relation_contact_id
        default_action = empty_rel.with_context(
            default_relation_contact_id=self.partner_b.id
        ).open_related_contact()
        self.assertEqual(default_action.get('res_id'), self.partner_b.id)

    def test_partner_compute_relation_info(self):
        """Test computed fields on res.partner."""
        # Initially partner_a has no relationships
        self.partner_a._compute_relation_info()
        self.assertFalse(self.partner_a.is_related)
        self.assertFalse(self.partner_a.relation_type_names)
        self.assertFalse(self.partner_a.relation_category_names)

        # Create multiple relationships across different categories
        self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_c.id,
            'relation_type_id': self.type_manager.id,
            'reverse_relation_type_id': self.type_employee.id,
        })

        self.partner_a._compute_relation_info()
        self.assertTrue(self.partner_a.is_related)
        self.assertIn('Son Test', self.partner_a.relation_type_names)
        self.assertIn('Employee Test', self.partner_a.relation_type_names)
        self.assertIn('Family Test', self.partner_a.relation_category_names)
        self.assertIn('Work Test', self.partner_a.relation_category_names)

        # Test searching by is_related and category/type names
        related_partners = self.Partner.search([('is_related', '=', True)])
        self.assertIn(self.partner_a, related_partners)
        self.assertIn(self.partner_b, related_partners)

        family_partners = self.Partner.search([
            ('relation_category_names', 'ilike', 'Family Test')
        ])
        self.assertIn(self.partner_a, family_partners)

    def test_unique_partner_relation_constraint(self):
        """Test SQL constraint preventing duplicate relationships."""
        self.PartnerRelation.create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.PartnerRelation.create({
                    'contact_id': self.partner_a.id,
                    'relation_contact_id': self.partner_b.id,
                    'relation_type_id': self.type_father.id,
                    'reverse_relation_type_id': self.type_son.id,
                })

    def test_create_multi(self):
        """Test batch creation with multiple relationship records."""
        records = self.PartnerRelation.create([
            {
                'contact_id': self.partner_a.id,
                'relation_contact_id': self.partner_b.id,
                'relation_type_id': self.type_father.id,
                'reverse_relation_type_id': self.type_son.id,
            },
            {
                'contact_id': self.partner_b.id,
                'relation_contact_id': self.partner_c.id,
                'relation_type_id': self.type_manager.id,
                'reverse_relation_type_id': self.type_employee.id,
            },
        ])
        self.assertEqual(len(records), 2)
        # Verify reciprocals were created
        recip_ba = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
        ])
        recip_cb = self.PartnerRelation.search([
            ('contact_id', '=', self.partner_c.id),
            ('relation_contact_id', '=', self.partner_b.id),
        ])
        self.assertEqual(len(recip_ba), 1)
        self.assertEqual(len(recip_cb), 1)

    def test_standard_user_access_rights(self):
        """Test standard internal user can CRUD relations without error."""
        test_user = self.env['res.users'].create({
            'name': 'Test Internal User',
            'login': 'test_internal_user',
            'email': 'test_internal_user@test.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        rel = self.PartnerRelation.with_user(test_user).create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.type_father.id,
            'reverse_relation_type_id': self.type_son.id,
        })
        self.assertTrue(rel.exists())
        rel.with_user(test_user).write({
            'relation_type_id': self.type_manager.id,
            'reverse_relation_type_id': self.type_employee.id,
        })
        self.assertEqual(rel.relation_type_id, self.type_manager)
        rel.with_user(test_user).unlink()
        self.assertFalse(rel.exists())
