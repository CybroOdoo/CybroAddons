# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockQuant(TransactionCase):
    """Test cases for stock.quant functions defined in
    pos_alternative_products/models/stock_quant.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config Stock',
        })
        # In Odoo 19, storable products are type='consu' + is_storable=True.
        # There is no 'product' type value and no 'detailed_type' field.
        # is_storable=True enables stock.quant tracking (qty_available reflects
        # real on-hand stock rather than always returning 0).
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Alt Test Product',
            'type': 'consu',
            'is_storable': True,
            'available_in_pos': True,
            'list_price': 10.0,
        })
        cls.product = cls.product_tmpl.product_variant_ids[0]

        # Create an alternative product template
        cls.alt_product_tmpl = cls.env['product.template'].create({
            'name': 'Alt Product',
            'type': 'consu',
            'available_in_pos': True,
            'list_price': 12.0,
        })
        cls.alt_product = cls.alt_product_tmpl.product_variant_ids[0]

    # -----------------------------------------------------------------
    # Tests for _load_pos_data_fields
    # -----------------------------------------------------------------

    def test_load_pos_data_fields_returns_required_keys(self):
        """_load_pos_data_fields must return the exact set of fields required
        by the POS frontend: product_id, available_quantity, quantity,
        location_id."""
        result = self.env['stock.quant']._load_pos_data_fields(
            self.pos_config.id)
        for field in ('product_id', 'available_quantity', 'quantity',
                      'location_id'):
            self.assertIn(
                field, result,
                f"'{field}' must be present in stock.quant POS data fields."
            )

    def test_load_pos_data_fields_returns_list(self):
        """_load_pos_data_fields must return a list."""
        result = self.env['stock.quant']._load_pos_data_fields(
            self.pos_config.id)
        self.assertIsInstance(result, list,
                              "_load_pos_data_fields must return a list.")

    def test_load_pos_data_fields_does_not_include_unexpected_fields(self):
        """_load_pos_data_fields should return exactly the 4 defined fields
        and not grow unexpectedly (verifies the override does not call super)."""
        result = self.env['stock.quant']._load_pos_data_fields(
            self.pos_config.id)
        self.assertEqual(
            len(result), 4,
            "stock.quant._load_pos_data_fields should return exactly 4 fields."
        )

    # -----------------------------------------------------------------
    # Tests for pos_stock_product
    # -----------------------------------------------------------------

    def test_pos_stock_product_returns_zero_when_qty_unavailable(self):
        """pos_stock_product must return 0 when the product's qty_available
        is <= 0 (no stock on hand)."""
        # A freshly created consumable product has qty_available = 0
        result = self.env['stock.quant'].pos_stock_product(self.product.id)
        self.assertEqual(
            result, 0,
            "pos_stock_product should return 0 when qty_available <= 0."
        )

    def test_pos_stock_product_returns_product_when_qty_available(self):
        """pos_stock_product must return the product.product record (truthy)
        when the product has positive stock on hand.
        Uses _update_available_quantity() — the correct Odoo 19 API for
        adjusting storable product stock without going through inventory
        validation. stock.quant.create() is blocked for consumables/services."""
        self.env['stock.quant']._update_available_quantity(
            self.product,
            self.env.ref('stock.stock_location_stock'),
            10.0,
        )
        result = self.env['stock.quant'].pos_stock_product(self.product.id)
        self.assertTrue(
            result,
            "pos_stock_product should return the product record when qty > 0."
        )

    # -----------------------------------------------------------------
    # Tests for pos_alternative_product
    # -----------------------------------------------------------------

    def test_pos_alternative_product_returns_product_id_when_available_in_pos(self):
        """pos_alternative_product must return the product's ID when the
        product variant exists, has no internal reference filter, and is
        available in POS."""
        result = self.env['stock.quant'].pos_alternative_product(
            self.alt_product_tmpl.id, False)
        self.assertEqual(
            result, self.alt_product.id,
            "pos_alternative_product should return the product ID when "
            "the product is available in POS."
        )

    def test_pos_alternative_product_returns_zero_when_no_product_found(self):
        """pos_alternative_product must return 0 when no product.product
        matches the given template id and internal reference."""
        # Use a nonexistent template id
        result = self.env['stock.quant'].pos_alternative_product(
            999999999, False)
        self.assertEqual(
            result, 0,
            "pos_alternative_product should return 0 when no product is found."
        )

    def test_pos_alternative_product_filters_by_default_code(self):
        """pos_alternative_product must narrow the search by internal reference
        (default_code) when a code is provided."""
        self.alt_product.default_code = 'ALT-001'
        # Search with the correct code — should find the product
        result_found = self.env['stock.quant'].pos_alternative_product(
            self.alt_product_tmpl.id, 'ALT-001')
        self.assertEqual(
            result_found, self.alt_product.id,
            "pos_alternative_product should find the product with matching code."
        )
        # Search with the wrong code — should return 0
        result_miss = self.env['stock.quant'].pos_alternative_product(
            self.alt_product_tmpl.id, 'WRONG-CODE')
        self.assertEqual(
            result_miss, 0,
            "pos_alternative_product should return 0 when the code doesn't match."
        )

    def test_pos_alternative_product_returns_zero_when_not_in_pos(self):
        """pos_alternative_product must return 0 when the matching product
        variant is NOT marked as available_in_pos."""
        # Create a product explicitly NOT available in POS
        tmpl_not_in_pos = self.env['product.template'].create({
            'name': 'Not In POS Product',
            'type': 'consu',
            'available_in_pos': False,
            'list_price': 5.0,
        })
        product_not_in_pos = tmpl_not_in_pos.product_variant_ids[0]
        result = self.env['stock.quant'].pos_alternative_product(
            tmpl_not_in_pos.id, False)
        self.assertEqual(
            result, 0,
            "pos_alternative_product must return 0 for products not in POS."
        )

    # -----------------------------------------------------------------
    # Tests for product_in_pos
    # -----------------------------------------------------------------

    def test_product_in_pos_returns_product_id_when_available_in_pos(self):
        """product_in_pos must return the product_id when the product is
        flagged as available_in_pos=True."""
        result = self.env['stock.quant'].product_in_pos(self.product.id)
        self.assertEqual(
            result, self.product.id,
            "product_in_pos should return the product_id when available_in_pos is True."
        )

    def test_product_in_pos_returns_zero_when_not_available_in_pos(self):
        """product_in_pos must return 0 when the product is NOT available
        in POS (available_in_pos=False)."""
        tmpl_not_pos = self.env['product.template'].create({
            'name': 'Non-POS Product',
            'type': 'consu',
            'available_in_pos': False,
            'list_price': 5.0,
        })
        product_not_pos = tmpl_not_pos.product_variant_ids[0]
        result = self.env['stock.quant'].product_in_pos(product_not_pos.id)
        self.assertEqual(
            result, 0,
            "product_in_pos should return 0 when available_in_pos is False."
        )
