# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

# Warn-field defaults to pass via ORM when the 'sale' module is active.
_SALE_WARN_DEFAULTS = {
    'sale_line_warn': 'no-message',
    'purchase_line_warn': 'no-message',
}

# Map PostgreSQL data_type -> safe SQL literal for orphan NOT NULL columns.
_PG_TYPE_DEFAULTS = {
    'integer':           '0',
    'bigint':            '0',
    'smallint':          '0',
    'numeric':           '1',
    'real':              '1',
    'double precision':  '1',
    'boolean':           'false',
    'character varying': "''",
    'text':              "''",
    'character':         "''",
    'jsonb':             "'{}'",
    'json':              "'{}'",
}


class ProductCategoryTestBase(TransactionCase):
    """
    Base class for all product_category_management tests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._patch_orphan_columns()

    @classmethod
    def _patch_orphan_columns(cls):
        """Auto-detect and fix every orphan NOT NULL column in product tables.
        """
        # table_name -> ORM model whose _fields we check against
        tables = {
            'product_template': 'product.template',
            'product_product':  'product.product',
        }
        for table_name, model_name in tables.items():
            orm_fields = cls.env[model_name]._fields
            cls.env.cr.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name    = %s
                  AND is_nullable   = 'NO'
                  AND column_default IS NULL
                  AND column_name   <> 'id'
                ORDER BY column_name
                """,
                [table_name],
            )
            for col_name, data_type in cls.env.cr.fetchall():
                if col_name in orm_fields:
                    # ORM knows this column and supplies a value automatically.
                    continue
                sql_default = _PG_TYPE_DEFAULTS.get(data_type)
                if sql_default is None:
                    continue  # Unknown type – skip rather than guess wrongly.
                # col_name comes from information_schema (trusted source).
                cls.env.cr.execute(
                    "ALTER TABLE %s ALTER COLUMN %s SET DEFAULT %s"
                    % (table_name, col_name, sql_default)
                )

    def _make_product(self, name, categ_id, **extra):
        """Create a product.template, passing warn fields only when the ORM
        recognises them (i.e. the 'sale' module is installed)."""
        pt = self.env['product.template']
        vals = {'name': name, 'categ_id': categ_id}
        for warn_field, default in _SALE_WARN_DEFAULTS.items():
            if warn_field in pt._fields:
                vals.setdefault(warn_field, default)
        vals.update(extra)
        return pt.create(vals)

# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestProductCategoryFields(ProductCategoryTestBase):
    """Tests for custom fields added to product.category."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})

    def test_active_default_is_true(self):
        """New categories must be active by default."""
        self.assertTrue(self.category.active,
                        "A newly created category should have active=True by default.")

    def test_description_field_is_empty_by_default(self):
        """Description field should be falsy when not provided."""
        self.assertFalse(self.category.description,
                         "Description should be empty/False when not explicitly set.")


    def test_description_can_be_set(self):
        """Description text field should accept and store text values."""
        desc = "A detailed description of the test category."
        self.category.write({'description': desc})
        self.assertEqual(self.category.description, desc,
                         "Description should persist after write.")

    def test_image_can_be_stored_as_binary(self):
        """Image field should accept and store a base64-encoded binary value."""
        png_b64 = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            b"YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        self.category.write({'image': png_b64})
        self.assertEqual(self.category.image, png_b64,
                         "Binary image data should be stored and retrieved identically.")


class TestProductCategoryProductCount(ProductCategoryTestBase):
    """Tests for the _compute_product_count computed field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({'name': 'Count Category'})

    def test_product_count_zero_when_no_products(self):
        """product_count must be 0 for a category with no linked products."""
        self.assertEqual(self.category.product_count, 0,
                         "product_count should be 0 when no products are assigned.")

    def test_product_count_increments_on_product_creation(self):
        """product_count should reflect the number of products in the category."""
        self._make_product('Product A', self.category.id)
        self.category._compute_product_count()
        self.assertEqual(self.category.product_count, 1,
                         "product_count should be 1 after adding one product.")

    def test_product_count_multiple_products(self):
        """product_count should count all products in the category."""
        for i in range(3):
            self._make_product(f'Product {i}', self.category.id)
        self.category._compute_product_count()
        self.assertEqual(self.category.product_count, 3,
                         "product_count should equal the total number of products in category.")

    def test_product_count_does_not_count_other_categories(self):
        """product_count should only count products in the specific category."""
        other = self.env['product.category'].create({'name': 'Other Category'})
        self._make_product('Other Product', other.id)
        self.category._compute_product_count()
        self.assertEqual(self.category.product_count, 0,
                         "product_count should not count products from other categories.")

    def test_product_count_decrements_when_product_category_changes(self):
        """product_count should drop when a product is moved to another category."""
        other = self.env['product.category'].create({'name': 'New Cat'})
        product = self._make_product('Movable Product', self.category.id)
        self.category._compute_product_count()
        self.assertEqual(self.category.product_count, 1)

        product.write({'categ_id': other.id})
        self.category._compute_product_count()
        self.assertEqual(self.category.product_count, 0,
                         "product_count should decrease when the product is reassigned.")


class TestProductCategoryArchiveConstraint(ProductCategoryTestBase):
    """Tests for the _check_archive constraint on product.category."""

    def setUp(self):
        super().setUp()
        self.category = self.env['product.category'].create({'name': 'Archivable Category'})

    def test_archive_empty_category_succeeds(self):
        """Archiving a category with no products should succeed without error."""
        try:
            self.category.write({'active': False})
        except ValidationError:
            self.fail("_check_archive raised ValidationError for a category with no products.")
        self.assertFalse(self.category.active,
                         "Category should be archived (active=False) after write.")

    def test_archive_category_with_products_raises_validation_error(self):
        """Archiving a category that has linked products must raise ValidationError."""
        self._make_product('Linked Product', self.category.id)
        with self.assertRaises(ValidationError):
            self.category.write({'active': False})

    def test_archive_parent_with_child_having_products_raises_error(self):
        """Archiving a parent whose child category has products must raise ValidationError."""
        child = self.env['product.category'].create({
            'name': 'Child Category',
            'parent_id': self.category.id,
        })
        self._make_product('Child Product', child.id)
        with self.assertRaises(ValidationError):
            self.category.write({'active': False})

    def test_writing_other_fields_does_not_trigger_constraint(self):
        """Writing non-active fields must not accidentally fire the archive constraint."""
        self._make_product('Linked Product', self.category.id)
        try:
            self.category.write({'description': 'Updated description'})
        except ValidationError:
            self.fail("_check_archive should not trigger when active is not changed.")


class TestProductCategoryHierarchyHtml(ProductCategoryTestBase):
    """Tests for _build_hierarchy_html and _compute_category_hierarchy_html."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent = cls.env['product.category'].create({'name': 'Parent Cat'})
        cls.child = cls.env['product.category'].create({
            'name': 'Child Cat',
            'parent_id': cls.parent.id,
        })

    def test_hierarchy_html_is_computed(self):
        """category_hierarchy_html should be a non-empty string."""
        self.parent._compute_category_hierarchy_html()
        self.assertTrue(self.parent.category_hierarchy_html,
                        "category_hierarchy_html should not be empty after computation.")

    def test_hierarchy_html_contains_parent_name(self):
        """The computed HTML must include the category's own name."""
        self.parent._compute_category_hierarchy_html()
        self.assertIn('Parent Cat', self.parent.category_hierarchy_html)

    def test_hierarchy_html_contains_child_name(self):
        """The computed HTML must include direct children names."""
        self.parent._compute_category_hierarchy_html()
        self.assertIn('Child Cat', self.parent.category_hierarchy_html)

    def test_hierarchy_html_contains_category_tree_class(self):
        """Root div should carry the 'category-tree' CSS class."""
        self.parent._compute_category_hierarchy_html()
        self.assertIn('category-tree', self.parent.category_hierarchy_html)

    def test_hierarchy_html_contains_fa_icon(self):
        """HTML must include the Font Awesome folder icon class."""
        self.parent._compute_category_hierarchy_html()
        self.assertIn('fa-folder-open', self.parent.category_hierarchy_html)

    def test_build_hierarchy_html_plural_products_badge(self):
        """Badge must read 'N products' (plural) when more than one product exists."""
        for i in range(2):
            self._make_product(f'Plural Product {i}', self.parent.id)
        self.parent._compute_product_count()
        html = self.parent._build_hierarchy_html(self.parent)
        self.assertIn('products', html,
                      "Badge should use plural 'products' when product_count > 1.")

    def test_build_hierarchy_html_zero_products_badge(self):
        """Badge should read '0 products' for a category with no products."""
        leaf = self.env['product.category'].create({'name': 'Zero Products Cat'})
        leaf._compute_product_count()
        html = leaf._build_hierarchy_html(leaf)
        self.assertIn('0 products', html,
                      "Badge should show '0 products' when no products are linked.")

    def test_hierarchy_html_no_children_section_for_leaf(self):
        """A leaf category (no children) should NOT contain a children <ul> block."""
        leaf = self.env['product.category'].create({'name': 'Leaf Category'})
        html = leaf._build_hierarchy_html(leaf)
        self.assertNotIn('category-children', html,
                         "Leaf node HTML should not contain a 'category-children' list.")

    def test_hierarchy_html_with_multiple_children(self):
        """All immediate children should appear in the parent's hierarchy HTML."""
        self.env['product.category'].create({
            'name': 'Child Cat 2',
            'parent_id': self.parent.id,
        })
        self.parent.invalidate_recordset(['category_hierarchy_html', 'child_id'])
        self.parent._compute_category_hierarchy_html()
        self.assertIn('Child Cat', self.parent.category_hierarchy_html)
        self.assertIn('Child Cat 2', self.parent.category_hierarchy_html)

    def test_hierarchy_html_deeply_nested(self):
        """Grandchild names should appear in the root category's hierarchy HTML."""
        self.env['product.category'].create({
            'name': 'Grandchild Cat',
            'parent_id': self.child.id,
        })
        self.parent.invalidate_recordset(['category_hierarchy_html', 'child_id'])
        self.parent._compute_category_hierarchy_html()
        self.assertIn('Grandchild Cat', self.parent.category_hierarchy_html,
                      "Deeply nested categories should be present in the hierarchy HTML.")


class TestProductCategoryIntegration(ProductCategoryTestBase):
    """Integration tests combining multiple features of the ProductCategory model."""

    def test_full_lifecycle_create_assign_count_archive(self):
        """
        Full lifecycle: create a category, assign a product, verify count,
        attempt (and fail) to archive, move the product away, then archive.
        """
        cat = self.env['product.category'].create({
            'name': 'Lifecycle Category',
            'description': 'A test category for lifecycle testing.',
        })
        cat._compute_product_count()
        self.assertEqual(cat.product_count, 0)

        product = self._make_product('Lifecycle Product', cat.id)
        cat._compute_product_count()
        self.assertEqual(cat.product_count, 1)

        with self.assertRaises(ValidationError):
            cat.write({'active': False})

        other = self.env['product.category'].create({'name': 'Fallback Category'})
        product.write({'categ_id': other.id})
        cat.write({'active': False})
        self.assertFalse(cat.active)

    def test_hierarchy_html_updates_after_child_added(self):
        """HTML output should reflect children added after initial computation."""
        parent = self.env['product.category'].create({'name': 'Dynamic Parent'})
        parent._compute_category_hierarchy_html()
        self.assertNotIn('Dynamic Child', parent.category_hierarchy_html)

        self.env['product.category'].create({'name': 'Dynamic Child', 'parent_id': parent.id})
        parent.invalidate_recordset(['category_hierarchy_html', 'child_id'])
        parent._compute_category_hierarchy_html()
        self.assertIn('Dynamic Child', parent.category_hierarchy_html,
                      "After adding a child, the HTML should reflect the new child.")
