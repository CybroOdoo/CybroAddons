# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCustomerRelation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category = cls.env['relation.type.category'].create({
            'name': 'Family'
        })

        cls.father_type = cls.env['relation.type'].create({
            'name': 'Father',
            'category_id': cls.category.id,
        })

        cls.son_type = cls.env['relation.type'].create({
            'name': 'Son',
            'category_id': cls.category.id,
        })

        cls.partner_a = cls.env['res.partner'].create({
            'name': 'John',
            'email': 'john@test.com',
        })

        cls.partner_b = cls.env['res.partner'].create({
            'name': 'David',
            'email': 'david@test.com',
        })

    def test_relation_category_creation(self):
        self.assertEqual(self.category.name, 'Family')

    def test_relation_type_creation(self):
        self.assertEqual(self.father_type.category_id, self.category)

    def test_relation_creation(self):
        relation = self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        self.assertTrue(relation.id)

    def test_reverse_relation_created_automatically(self):
        relation = self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        reverse_relation = self.env['partner.relation'].search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
            ('relation_type_id', '=', self.son_type.id),
        ], limit=1)

        self.assertTrue(reverse_relation)

    def test_self_relation_validation(self):
        with self.assertRaises(ValidationError):
            self.env['partner.relation'].create({
                'contact_id': self.partner_a.id,
                'relation_contact_id': self.partner_a.id,
                'relation_type_id': self.father_type.id,
                'reverse_relation_type_id': self.son_type.id,
            })

    def test_duplicate_relation_not_allowed(self):
        self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        with self.assertRaises(Exception):
            self.env['partner.relation'].create({
                'contact_id': self.partner_a.id,
                'relation_contact_id': self.partner_b.id,
                'relation_type_id': self.father_type.id,
                'reverse_relation_type_id': self.son_type.id,
            })

    def test_write_updates_reverse_relation(self):
        relation = self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        relation.write({
            'relation_type_id': self.son_type.id,
            'reverse_relation_type_id': self.father_type.id,
        })

        reverse_relation = self.env['partner.relation'].search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
            ('relation_type_id', '=', self.father_type.id),
        ])

        self.assertTrue(reverse_relation)

    def test_unlink_removes_reverse_relation(self):
        relation = self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        reverse_relation = self.env['partner.relation'].search([
            ('contact_id', '=', self.partner_b.id),
            ('relation_contact_id', '=', self.partner_a.id),
            ('relation_type_id', '=', self.son_type.id),
        ], limit=1)

        relation.unlink()

        self.assertFalse(reverse_relation.exists())

    def test_partner_is_related_compute(self):
        self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        self.partner_a.invalidate_recordset()

        self.assertTrue(self.partner_a.is_related)

    def test_partner_relation_category_compute(self):
        self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        self.partner_a.invalidate_recordset()

        self.assertIn('Family', self.partner_a.relation_category_names)

    def test_open_related_contact(self):
        relation = self.env['partner.relation'].create({
            'contact_id': self.partner_a.id,
            'relation_contact_id': self.partner_b.id,
            'relation_type_id': self.father_type.id,
            'reverse_relation_type_id': self.son_type.id,
        })

        action = relation.open_related_contact()

        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['res_id'], self.partner_b.id)