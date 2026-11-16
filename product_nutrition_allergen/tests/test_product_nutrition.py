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
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductNutrition(TransactionCase):
    """Test suite for product nutrition, ingredients, and allergen functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.uom_g = cls.env.ref('uom.product_uom_gram', raise_if_not_found=False)
        if not cls.uom_g:
            cls.uom_g = cls.env['uom.uom'].search([('name', '=', 'g')], limit=1)
        if not cls.uom_g:
            uom_unit_categ = cls.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
            if not uom_unit_categ:
                uom_unit_categ = cls.env['uom.category'].create({'name': 'Weight'})
            cls.uom_g = cls.env['uom.uom'].create({
                'name': 'g',
                'category_id': uom_unit_categ.id,
                'uom_type': 'reference',
            })

        cls.nutrition_group = cls.env.ref(
            'product_nutrition_allergen.product_nutrition_allergen_group_user'
        )

        cls.nutrition_user = cls.env['res.users'].create({
            'name': 'Nutrition Test User',
            'login': 'nutrition_user@example.com',
            'email': 'nutrition_user@example.com',
        })
        if 'group_ids' in cls.env['res.users']._fields:
            cls.nutrition_user.write({'group_ids': [(4, cls.nutrition_group.id)]})
        elif 'groups_id' in cls.env['res.users']._fields:
            cls.nutrition_user.write({'groups_id': [(4, cls.nutrition_group.id)]})
        elif 'users' in cls.env['res.groups']._fields:
            cls.nutrition_group.write({'users': [(4, cls.nutrition_user.id)]})
        elif 'user_ids' in cls.env['res.groups']._fields:
            cls.nutrition_group.write({'user_ids': [(4, cls.nutrition_user.id)]})

        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted Test User',
            'login': 'restricted_user@example.com',
            'email': 'restricted_user@example.com',
        })

        cls.product_template = cls.env['product.template'].create({
            'name': 'Organic Energy Bar',
            'nutrition_details': True,
            'ingredients_details': True,
            'allergy_details': True,
            'nutrition_amount': 100.0,
            'unit_id': cls.uom_g.id,
            'ingredients_information': 'Oats, Honey, Almonds, Cocoa Butter.',
            'allergy_information': 'Contains nuts and honey. May contain traces of milk.',
            'nutrition_ids': [
                (0, 0, {
                    'name': 'Energy',
                    'nutrition_value': 450.0,
                    'uom_id': cls.uom_g.id,
                }),
                (0, 0, {
                    'name': 'Protein',
                    'nutrition_value': 12.5,
                    'uom_id': cls.uom_g.id,
                }),
                (0, 0, {
                    'name': 'Fat',
                    'nutrition_value': 18.0,
                    'uom_id': cls.uom_g.id,
                }),
            ],
        })

    def test_product_nutrition_creation(self):
        """Test product template creation with nutrition and allergen details."""
        product = self.product_template
        self.assertTrue(product.nutrition_details)
        self.assertTrue(product.ingredients_details)
        self.assertTrue(product.allergy_details)
        self.assertEqual(product.nutrition_amount, 100.0)
        self.assertEqual(product.unit_id, self.uom_g)
        self.assertEqual(len(product.nutrition_ids), 3)

        protein_line = product.nutrition_ids.filtered(lambda n: n.name == 'Protein')
        self.assertTrue(protein_line)
        self.assertEqual(protein_line.nutrition_value, 12.5)
        self.assertEqual(protein_line.uom_id, self.uom_g)
        self.assertEqual(protein_line.product_template_id, product)

    def test_nutrition_toggles(self):
        """Test enabling and disabling the nutrition, ingredient, and allergen toggles."""
        product = self.product_template
        product.write({
            'nutrition_details': False,
            'ingredients_details': False,
            'allergy_details': False,
        })
        self.assertFalse(product.nutrition_details)
        self.assertFalse(product.ingredients_details)
        self.assertFalse(product.allergy_details)

        product.write({'nutrition_details': True})
        self.assertTrue(product.nutrition_details)

    def test_product_nutrition_line_crud(self):
        """Test CRUD operations on product.nutrition lines."""
        nutrition_line = self.env['product.nutrition'].create({
            'name': 'Carbohydrates',
            'nutrition_value': 55.0,
            'uom_id': self.uom_g.id,
            'product_template_id': self.product_template.id,
        })
        self.assertEqual(nutrition_line.name, 'Carbohydrates')
        self.assertEqual(nutrition_line.nutrition_value, 55.0)

        nutrition_line.write({'nutrition_value': 60.0})
        self.assertEqual(nutrition_line.nutrition_value, 60.0)

        line_id = nutrition_line.id
        nutrition_line.unlink()
        self.assertFalse(self.env['product.nutrition'].browse(line_id).exists())

    def test_nutrition_report_generation(self):
        """Test that the QWeb PDF nutrition report renders successfully."""
        report_action = self.env.ref('product_nutrition_allergen.action_report_product_nutrition')
        self.assertTrue(report_action)

        report_content, report_format = self.env['ir.actions.report']._render_qweb_pdf(
            report_action,
            res_ids=self.product_template.ids,
        )
        self.assertIn(report_format, ('pdf', 'html'))
        self.assertTrue(report_content)
        self.assertTrue(len(report_content) > 0)

    def test_security_access_rights(self):
        """Test access rights for users with and without product nutrition group."""
        nutrition_as_user = self.env['product.nutrition'].with_user(self.nutrition_user)
        line = nutrition_as_user.create({
            'name': 'Fiber',
            'nutrition_value': 8.0,
            'uom_id': self.uom_g.id,
            'product_template_id': self.product_template.id,
        })
        self.assertTrue(line.id)
        self.assertEqual(line.name, 'Fiber')

        nutrition_as_restricted = self.env['product.nutrition'].with_user(self.restricted_user)
        with self.assertRaises(AccessError):
            nutrition_as_restricted.create({
                'name': 'Sodium',
                'nutrition_value': 0.2,
                'uom_id': self.uom_g.id,
                'product_template_id': self.product_template.id,
            })

