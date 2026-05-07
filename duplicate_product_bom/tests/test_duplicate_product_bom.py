# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestDuplicateProductBom(TransactionCase):
    """Test suite for the Duplicate Product BOM module.

    Validates that duplicating a product.template also duplicates all
    associated Bills of Materials (BOMs), including their component lines,
    while keeping the copied BOMs correctly linked to the new product.
    """

    @classmethod
    def setUpClass(cls):
        """Set up shared test fixtures for all test methods."""
        super().setUpClass()
        # Create a product category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        # Create a component product used in BOM lines
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
        })
        # Create the main product template with a storable type
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Product',
            'categ_id': cls.category.id,
            'type': 'consu',
        })
        # Resolve the product.product variant for the template
        cls.product_variant = cls.product_tmpl.product_variant_ids[0]

    def _create_bom(self, product_tmpl, qty=1.0, with_lines=True):
        """Helper: create a BOM for *product_tmpl* with optional line.

        Args:
            product_tmpl (product.template): The product template record.
            qty (float): Quantity for the BOM.
            with_lines (bool): Whether to add a component line.

        Returns:
            mrp.bom: The newly created BOM record.
        """
        bom_vals = {
            'product_tmpl_id': product_tmpl.id,
            'product_qty': qty,
            'type': 'normal',
        }
        bom = self.env['mrp.bom'].create(bom_vals)
        if with_lines:
            self.env['mrp.bom.line'].create({
                'bom_id': bom.id,
                'product_id': self.component.id,
                'product_qty': 2.0,
            })
        return bom

    # ------------------------------------------------------------------
    # Test 1: Duplicate product with a single BOM
    # ------------------------------------------------------------------
    def test_duplicate_product_with_single_bom(self):
        """Duplicating a product that has one BOM must create exactly one
        copied BOM linked to the new product template."""
        bom = self._create_bom(self.product_tmpl)
        original_bom_count = len(self.product_tmpl.bom_ids)

        new_product = self.product_tmpl.copy()

        # The duplicated product should have at least one BOM
        self.assertEqual(
            len(new_product.bom_ids),
            original_bom_count,
            "Duplicated product should have the same number of BOMs as the "
            "original.",
        )
        # The copied BOM must be a different record
        self.assertNotIn(
            bom.id,
            new_product.bom_ids.ids,
            "Copied BOM must be a new record, not the original BOM.",
        )

    # ------------------------------------------------------------------
    # Test 2: Duplicate product with multiple BOMs
    # ------------------------------------------------------------------
    def test_duplicate_product_with_multiple_boms(self):
        """All BOMs attached to the original product must be duplicated
        and linked to the new product template."""
        self._create_bom(self.product_tmpl, qty=1.0)
        self._create_bom(self.product_tmpl, qty=5.0)
        original_bom_count = len(self.product_tmpl.bom_ids)

        new_product = self.product_tmpl.copy()

        self.assertEqual(
            len(new_product.bom_ids),
            original_bom_count,
            "All BOMs must be duplicated when the product is copied.",
        )
        # None of the original BOM ids should appear on the new product
        original_ids = set(self.product_tmpl.bom_ids.ids)
        copied_ids = set(new_product.bom_ids.ids)
        self.assertTrue(
            original_ids.isdisjoint(copied_ids),
            "Copied BOMs must be distinct records from the original BOMs.",
        )

    # ------------------------------------------------------------------
    # Test 3: Duplicate product with NO BOM
    # ------------------------------------------------------------------
    def test_duplicate_product_without_bom(self):
        """Duplicating a product that has no BOM should not raise an error
        and the new product must also have no BOMs."""
        product_no_bom = self.env['product.template'].create({
            'name': 'Product Without BOM',
            'type': 'consu',
        })
        # Ensure there are no BOMs
        self.assertFalse(
            product_no_bom.bom_ids,
            "Product should start with no BOMs.",
        )

        new_product = product_no_bom.copy()

        self.assertFalse(
            new_product.bom_ids,
            "Duplicated product with no BOMs should also have no BOMs.",
        )

    # ------------------------------------------------------------------
    # Test 4: BOM component lines are preserved on copy
    # ------------------------------------------------------------------
    def test_bom_lines_are_copied(self):
        """Component lines in the BOM must be duplicated to the new BOM."""
        bom = self._create_bom(self.product_tmpl, with_lines=True)
        original_line_count = len(bom.bom_line_ids)

        new_product = self.product_tmpl.copy()

        copied_bom = new_product.bom_ids.filtered(
            lambda b: b.id not in self.product_tmpl.bom_ids.ids
        )
        # Verify lines exist and match count
        self.assertEqual(
            len(copied_bom.bom_line_ids),
            original_line_count,
            "Copied BOM should have the same number of component lines as "
            "the original BOM.",
        )
        # Verify the component product is the same
        self.assertEqual(
            copied_bom.bom_line_ids[0].product_id,
            self.component,
            "Copied BOM line must reference the same component product.",
        )

    # ------------------------------------------------------------------
    # Test 5: product_tmpl_id on copied BOM points to new product
    # ------------------------------------------------------------------
    def test_copied_bom_linked_to_new_product(self):
        """After duplication, each copied BOM's `product_tmpl_id` must
        point to the new (duplicated) product template."""
        self._create_bom(self.product_tmpl)

        new_product = self.product_tmpl.copy()

        for bom in new_product.bom_ids:
            self.assertEqual(
                bom.product_tmpl_id,
                new_product,
                "Copied BOM's product_tmpl_id must reference the new "
                "product template, not the original.",
            )

    # ------------------------------------------------------------------
    # Test 6: Original product's BOMs are not modified after copy
    # ------------------------------------------------------------------
    def test_original_bom_unchanged_after_copy(self):
        """Duplicating a product must not alter the original product's BOMs
        or their component lines."""
        bom = self._create_bom(self.product_tmpl)
        original_line_count = len(bom.bom_line_ids)
        original_bom_ids = list(self.product_tmpl.bom_ids.ids)

        self.product_tmpl.copy()

        # BOM ids on original product must be unchanged
        self.assertEqual(
            sorted(self.product_tmpl.bom_ids.ids),
            sorted(original_bom_ids),
            "Original product BOMs must not be changed after duplication.",
        )
        # Component lines on original BOM must be unchanged
        self.assertEqual(
            len(bom.bom_line_ids),
            original_line_count,
            "Original BOM lines must remain intact after duplication.",
        )

    # ------------------------------------------------------------------
    # Test 7: Default values are respected during copy
    # ------------------------------------------------------------------
    def test_copy_with_default_name(self):
        """Passing a custom name via the `default` parameter should name
        the new product template accordingly."""
        self._create_bom(self.product_tmpl)

        new_product = self.product_tmpl.copy(default={'name': 'Custom Copy'})

        self.assertEqual(
            new_product.name,
            'Custom Copy',
            "The copied product's name must match the value passed in "
            "`default`.",
        )
        # BOMs must still be duplicated even when defaults are provided
        self.assertTrue(
            new_product.bom_ids,
            "BOMs must be duplicated even when custom defaults are passed.",
        )
