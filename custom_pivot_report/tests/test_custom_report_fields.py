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
"""Unit tests for the custom.report.fields model."""

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestCustomReportFields(TransactionCase):
    """Test cases for custom.report.fields model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1
        )
        # 1. Integer field (measurable)
        cls.field_integer = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('ttype', '=', 'integer'),
        ], limit=1)

        # 2. Many2one field (measurable)
        cls.field_many2one = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('ttype', '=', 'many2one'),
        ], limit=1)

        # 3. Many2many field (rowable)
        cls.field_many2many = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('ttype', '=', 'many2many'),
        ], limit=1)

        # 4. Char field (neither measurable nor rowable)
        cls.field_char = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('ttype', '=', 'char'),
        ], limit=1)

    def test_onchange_custom_field_id(self):
        """Test onchange_custom_field_id function for field label, measurable and rowable attributes."""
        # Test Case 1: Measurable Integer field
        field_rec_int = self.env['custom.report.fields'].new({
            'custom_field_id': self.field_integer.id,
        })
        field_rec_int.onchange_custom_field_id()
        self.assertEqual(field_rec_int.label, self.field_integer.field_description)
        self.assertTrue(field_rec_int.measurable, "Integer fields should be marked as measurable")
        self.assertFalse(field_rec_int.rowable, "Integer fields should not be marked as rowable")

        # Test Case 2: Measurable Many2one field
        if self.field_many2one:
            field_rec_m2o = self.env['custom.report.fields'].new({
                'custom_field_id': self.field_many2one.id,
            })
            field_rec_m2o.onchange_custom_field_id()
            self.assertEqual(field_rec_m2o.label, self.field_many2one.field_description)
            self.assertTrue(field_rec_m2o.measurable, "Many2one fields should be marked as measurable")

        # Test Case 3: Rowable Many2many field
        if self.field_many2many:
            field_rec_m2m = self.env['custom.report.fields'].new({
                'custom_field_id': self.field_many2many.id,
            })
            field_rec_m2m.onchange_custom_field_id()
            self.assertEqual(field_rec_m2m.label, self.field_many2many.field_description)
            self.assertTrue(field_rec_m2m.rowable, "Many2many fields should be marked as rowable")
            self.assertFalse(field_rec_m2m.measurable, "Many2many fields should not be marked as measurable")

        # Test Case 4: Standard Char field
        if self.field_char:
            field_rec_char = self.env['custom.report.fields'].new({
                'custom_field_id': self.field_char.id,
            })
            field_rec_char.onchange_custom_field_id()
            self.assertEqual(field_rec_char.label, self.field_char.field_description)
            self.assertFalse(field_rec_char.measurable, "Char fields should not be marked as measurable")
            self.assertFalse(field_rec_char.rowable, "Char fields should not be marked as rowable")
