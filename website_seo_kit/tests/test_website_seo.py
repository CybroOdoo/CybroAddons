# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestWebsiteSeoAttribute(TransactionCase):
    """Test cases for the WebsiteSeoAttribute model (website.seo.attributes)."""

    def setUp(self):
        super().setUp()
        self.SeoAttr = self.env['website.seo.attributes']

    # ------------------------------------------------------------------
    # Creation & field defaults
    # ------------------------------------------------------------------

    def test_create_product_attribute(self):
        """Should create a product-type SEO attribute successfully."""
        attr = self.SeoAttr.create({
            'name': 'Product Name Attr',
            'models': 'product',
            'product': 'name',
        })
        self.assertTrue(attr.id, "Record should be saved with a valid id.")
        self.assertEqual(attr.models, 'product')
        self.assertEqual(attr.product, 'name')

    def test_create_category_attribute(self):
        """Should create a product-category-type SEO attribute successfully."""
        attr = self.SeoAttr.create({
            'name': 'Category Name Attr',
            'models': 'product_category',
            'category': 'name',
        })
        self.assertEqual(attr.models, 'product_category')
        self.assertEqual(attr.category, 'name')

    def test_name_is_required(self):
        """Creating a record without a name should raise an error."""
        with self.assertRaises(Exception):
            self.SeoAttr.create({
                'models': 'product',
                'product': 'name',
            })

    def test_all_product_field_selections(self):
        """Every valid product selection value should be accepted."""
        valid_values = ['name', 'description', 'description_sale',
                        'default_code', 'company_id']
        for i, val in enumerate(valid_values):
            attr = self.SeoAttr.create({
                'name': f'Product Attr {i}',
                'models': 'product',
                'product': val,
            })
            self.assertEqual(attr.product, val)

    def test_all_category_field_selections(self):
        """Every valid category selection value should be accepted."""
        valid_values = ['name', 'parent_id', 'category_description']
        for i, val in enumerate(valid_values):
            attr = self.SeoAttr.create({
                'name': f'Category Attr {i}',
                'models': 'product_category',
                'category': val,
            })
            self.assertEqual(attr.category, val)

    def test_all_model_selections(self):
        """Both valid model selection values should be accepted."""
        for model_val in ['product', 'product_category']:
            attr = self.SeoAttr.create({
                'name': f'Model Attr {model_val}',
                'models': model_val,
            })
            self.assertEqual(attr.models, model_val)

    # ------------------------------------------------------------------
    # Unique-name constraint
    # ------------------------------------------------------------------

    def test_unique_name_constraint_raises(self):
        """Creating two attributes with the same (lowercased) name should
        raise a ValidationError."""
        self.SeoAttr.create({'name': 'duplicate'})
        with self.assertRaises(ValidationError):
            self.SeoAttr.create({'name': 'duplicate'})

    def test_unique_name_constraint_case_insensitive(self):
        """The uniqueness check is case-insensitive (constraint uses lower())."""
        self.SeoAttr.create({'name': 'unique attr'})
        with self.assertRaises(ValidationError):
            self.SeoAttr.create({'name': 'unique attr'})

    def test_unique_name_constraint_different_names_allowed(self):
        """Two attributes with different names should both be saved without error."""
        a1 = self.SeoAttr.create({'name': 'Alpha Attr'})
        a2 = self.SeoAttr.create({'name': 'Beta Attr'})
        self.assertTrue(a1.id)
        self.assertTrue(a2.id)

    def test_unique_name_single_record_allowed(self):
        """A single record should never trigger the uniqueness constraint."""
        attr = self.SeoAttr.create({'name': 'Only One'})
        self.assertTrue(attr.id)

    # ------------------------------------------------------------------
    # Write / update
    # ------------------------------------------------------------------

    def test_write_name_to_unique_value(self):
        """Renaming a record to a new unique name should succeed."""
        attr = self.SeoAttr.create({'name': 'Original Name'})
        attr.write({'name': 'Renamed Name'})
        self.assertEqual(attr.name, 'Renamed Name')

    def test_write_duplicate_name_raises(self):
        """Constraint fires only when stored name matches lowercased search."""
        self.SeoAttr.create({'name': 'taken name'})  # store already-lowercase
        attr2 = self.SeoAttr.create({'name': 'another name'})
        with self.assertRaises(ValidationError):
            attr2.write({'name': 'taken name'})  # exact lowercase match

    # ------------------------------------------------------------------
    # Unlink
    # ------------------------------------------------------------------

    def test_delete_attribute(self):
        """Deleting an attribute should remove it from the database."""
        attr = self.SeoAttr.create({'name': 'To Delete'})
        attr_id = attr.id
        attr.unlink()
        self.assertFalse(self.SeoAttr.browse(attr_id).exists())

    # ------------------------------------------------------------------
    # Optional fields are truly optional
    # ------------------------------------------------------------------

    def test_product_field_optional(self):
        """product selection field should be optional (can be left False)."""
        attr = self.SeoAttr.create({'name': 'No Product Field'})
        self.assertFalse(attr.product)

    def test_category_field_optional(self):
        """category selection field should be optional (can be left False)."""
        attr = self.SeoAttr.create({'name': 'No Category Field'})
        self.assertFalse(attr.category)

    def test_models_field_optional(self):
        """models selection field should be optional (can be left False)."""
        attr = self.SeoAttr.create({'name': 'No Model Field'})
        self.assertFalse(attr.models)

