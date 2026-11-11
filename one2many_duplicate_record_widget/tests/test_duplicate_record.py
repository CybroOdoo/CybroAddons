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
from odoo.tests.common import TransactionCase


class TestDuplicateRecord(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.parent = cls.env['res.partner'].create({
            'name': 'Parent Partner',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'parent_id': cls.parent.id,
        })

        cls.wizard = cls.env['duplicate.record']

    def test_duplicate_single_record(self):
        """Test duplication of a single partner."""

        before_records = self.env['res.partner'].search([])

        result = self.wizard.action_duplicate_records({
            'values': self.partner.id,
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        after_records = self.env['res.partner'].search([])

        self.assertTrue(result)
        self.assertEqual(len(after_records), len(before_records) + 1)

        new_records = after_records - before_records

        self.assertEqual(len(new_records), 1)
        self.assertNotEqual(new_records.id, self.partner.id)
        self.assertEqual(new_records.name, 'Test Partner (copy)')
        self.assertEqual(new_records.parent_id, self.parent)

    def test_duplicate_multiple_records(self):
        """Test duplication of multiple selected records."""
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'parent_id': self.parent.id,
        })

        before_count = self.env['res.partner'].search_count([])

        result = self.wizard.action_duplicate_records({
            'values': [self.partner.id, partner2.id],
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        after_count = self.env['res.partner'].search_count([])

        self.assertTrue(result)
        self.assertEqual(after_count, before_count + 2)

    def test_duplicate_invalid_record(self):
        """Test duplication with a non-existing record."""
        before_count = self.env['res.partner'].search_count([])

        result = self.wizard.action_duplicate_records({
            'values': [999999],
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        after_count = self.env['res.partner'].search_count([])

        self.assertTrue(result)
        self.assertEqual(after_count, before_count)

    def test_duplicate_empty_values(self):
        """Test duplication with empty values."""
        before_count = self.env['res.partner'].search_count([])

        result = self.wizard.action_duplicate_records({
            'values': [],
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        after_count = self.env['res.partner'].search_count([])

        self.assertTrue(result)
        self.assertEqual(after_count, before_count)

    def test_duplicate_invalid_values(self):
        """Test duplication with invalid values type."""
        result = self.wizard.action_duplicate_records({
            'values': 'invalid',
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        self.assertTrue(result)

    def test_duplicate_missing_values(self):
        """Test duplication when values are not provided."""
        result = self.wizard.action_duplicate_records({
            'model': 'res.partner',
            'relation_field': 'parent_id',
        })

        self.assertTrue(result)

    def test_duplicate_invalid_model(self):
        """Test duplication with an invalid model."""
        result = self.wizard.action_duplicate_records({
            'values': [self.partner.id],
            'model': 'invalid.model',
            'relation_field': 'parent_id',
        })

        self.assertTrue(result)