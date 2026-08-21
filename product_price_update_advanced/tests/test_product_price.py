# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: K Sai Saran Varma (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


# ---------------------------------------------------------------------------
# TC-01 … TC-20  ProductPrice wizard
# ---------------------------------------------------------------------------

@tagged('post_install', '-at_install')
class TestProductPriceWizard(TransactionCase):
    """Test suite for the ProductPrice transient model.
    Wizard: product.price  (product_price_update_advanced/wizards/product_price.py)
    """

    def setUp(self):
        super().setUp()
        # Create a product template with known prices for all tests
        self.product = self.env['product.template'].create({
            'name': 'Test Product Alpha',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 60.0,
        })
        # Second product for multi-product tests
        self.product_b = self.env['product.template'].create({
            'name': 'Test Product Beta',
            'type': 'consu',
            'list_price': 200.0,
            'standard_price': 120.0,
        })

    def _make_wizard(self, product=None, sale_price=None, cost_price=None):
        """Helper — create a product.price wizard record with sane defaults."""
        product = product or self.product
        return self.env['product.price'].create({
            'product_id': product.id,
            'sale_price': sale_price if sale_price is not None else product.list_price,
            'cost_price': cost_price if cost_price is not None else product.standard_price,
        })

    # -----------------------------------------------------------------------
    # Field definitions & defaults  (TC-01 – TC-05)
    # -----------------------------------------------------------------------

    def test_01_wizard_model_exists(self):
        """TC-01: product.price transient model must be registered in the
        Odoo registry."""
        self.assertIn(
            'product.price', self.env,
            "TransientModel 'product.price' must be registered",
        )

    def test_02_product_id_field_is_many2one(self):
        """TC-02: product_id must be a Many2one field pointing to
        product.template."""
        field = self.env['product.price']._fields.get('product_id')
        self.assertIsNotNone(field, "Field 'product_id' not found on product.price")
        from odoo import fields
        self.assertIsInstance(field, fields.Many2one)
        self.assertEqual(field.comodel_name, 'product.template')

    def test_03_sale_price_field_is_float(self):
        """TC-03: sale_price must be a Float field."""
        field = self.env['product.price']._fields.get('sale_price')
        self.assertIsNotNone(field, "Field 'sale_price' not found on product.price")
        from odoo import fields
        self.assertIsInstance(field, fields.Float)

    def test_04_cost_price_field_is_float(self):
        """TC-04: cost_price must be a Float field."""
        field = self.env['product.price']._fields.get('cost_price')
        self.assertIsNotNone(field, "Field 'cost_price' not found on product.price")
        from odoo import fields
        self.assertIsInstance(field, fields.Float)

    def test_05_wizard_is_transient_model(self):
        """TC-05: product.price must inherit from TransientModel, confirming
        it is a wizard (auto-cleaned by the vacuum cron)."""
        model_cls = type(self.env['product.price'])
        self.assertTrue(
            model_cls._transient,
            "'product.price' must be a TransientModel",
        )

    # -----------------------------------------------------------------------
    # _onchange_product_id()  (TC-06 – TC-09)
    # -----------------------------------------------------------------------

    def test_06_onchange_populates_sale_price_from_product(self):
        """TC-06: Triggering _onchange_product_id() should set sale_price to
        the product's current list_price."""
        wizard = self.env['product.price'].new({'product_id': self.product.id})
        wizard._onchange_product_id()
        self.assertAlmostEqual(
            wizard.sale_price, self.product.list_price, places=2,
            msg="sale_price must match product's list_price after onchange",
        )

    def test_07_onchange_populates_cost_price_from_product(self):
        """TC-07: Triggering _onchange_product_id() should set cost_price to
        the product's current standard_price."""
        wizard = self.env['product.price'].new({'product_id': self.product.id})
        wizard._onchange_product_id()
        self.assertAlmostEqual(
            wizard.cost_price, self.product.standard_price, places=2,
            msg="cost_price must match product's standard_price after onchange",
        )

    def test_08_onchange_updates_when_product_changes(self):
        """TC-08: Switching product_id to a different product should update
        both sale_price and cost_price to the new product's prices."""
        wizard = self.env['product.price'].new({'product_id': self.product.id})
        wizard._onchange_product_id()
        # Switch to product_b
        wizard.product_id = self.product_b
        wizard._onchange_product_id()
        self.assertAlmostEqual(
            wizard.sale_price, self.product_b.list_price, places=2,
            msg="sale_price must update to product_b's list_price",
        )
        self.assertAlmostEqual(
            wizard.cost_price, self.product_b.standard_price, places=2,
            msg="cost_price must update to product_b's standard_price",
        )

    def test_09_onchange_reflects_product_zero_prices(self):
        """TC-09: If a product has 0.0 list_price and standard_price,
        _onchange_product_id() should set both wizard prices to 0.0."""
        zero_product = self.env['product.template'].create({
            'name': 'Free Product',
            'type': 'consu',
            'list_price': 0.0,
            'standard_price': 0.0,
        })
        wizard = self.env['product.price'].new({'product_id': zero_product.id})
        wizard._onchange_product_id()
        self.assertAlmostEqual(wizard.sale_price, 0.0, places=2)
        self.assertAlmostEqual(wizard.cost_price, 0.0, places=2)

    # -----------------------------------------------------------------------
    # action_change_product_price()  (TC-10 – TC-16)
    # -----------------------------------------------------------------------

    def test_10_action_updates_list_price_on_product(self):
        """TC-10: action_change_product_price() must write the wizard's
        sale_price to the product's list_price field."""
        new_sale = 150.0
        wizard = self._make_wizard(sale_price=new_sale)
        wizard.action_change_product_price()
        self.assertAlmostEqual(
            self.product.list_price, new_sale, places=2,
            msg="product.list_price must be updated to the wizard's sale_price",
        )


    def test_11_action_updates_standard_price_on_product(self):
        """TC-11: action_change_product_price() must write the wizard's
        cost_price to the product's standard_price field."""
        new_cost = 90.0
        wizard = self._make_wizard(cost_price=new_cost)
        wizard.action_change_product_price()
        self.assertAlmostEqual(
            self.product.standard_price, new_cost, places=2,
            msg="product.standard_price must be updated to the wizard's cost_price",
        )


    def test_12_action_updates_both_prices_simultaneously(self):
        """TC-12: action_change_product_price() must update both list_price
        and standard_price in a single call."""
        new_sale, new_cost = 250.0, 140.0
        wizard = self._make_wizard(sale_price=new_sale, cost_price=new_cost)
        wizard.action_change_product_price()
        self.assertAlmostEqual(self.product.list_price, new_sale, places=2)
        self.assertAlmostEqual(self.product.standard_price, new_cost, places=2)


    def test_13_action_returns_act_window_action(self):
        """TC-13: action_change_product_price() must return a dict with
        type 'ir.actions.act_window'."""
        wizard = self._make_wizard()
        result = wizard.action_change_product_price()
        self.assertIsInstance(result, dict, "Return value must be a dict")
        self.assertEqual(
            result.get('type'), 'ir.actions.act_window',
            "Return type must be 'ir.actions.act_window'",
        )

    def test_14_action_return_targets_product_template_model(self):
        """TC-14: The returned action must point to the res_model
        'product.template' so the UI navigates to the product form."""
        wizard = self._make_wizard()
        result = wizard.action_change_product_price()
        self.assertEqual(
            result.get('res_model'), 'product.template',
            "res_model in action must be 'product.template'",
        )


    def test_15_action_return_contains_correct_res_id(self):
        """TC-15: The returned action must contain the res_id of the product
        that was just updated, so the form navigates to the right record."""
        wizard = self._make_wizard()
        result = wizard.action_change_product_price()
        self.assertEqual(
            result.get('res_id'), self.product.id,
            "res_id in action must be the ID of the updated product",
        )


    def test_16_action_return_view_mode_is_form(self):
        """TC-16: The returned action must have view_mode='form' so the
        UI opens the product form view."""
        wizard = self._make_wizard()
        result = wizard.action_change_product_price()
        self.assertEqual(
            result.get('view_mode'), 'form',
            "view_mode in action must be 'form'",
        )

    # -----------------------------------------------------------------------
    # Edge / boundary cases  (TC-17 – TC-20)
    # -----------------------------------------------------------------------

    def test_17_update_with_zero_sale_price(self):
        """TC-17: Setting sale_price=0.0 in the wizard and confirming must
        write 0.0 to the product's list_price (zero is a valid price)."""
        wizard = self._make_wizard(sale_price=0.0, cost_price=0.0)
        wizard.action_change_product_price()
        self.assertAlmostEqual(
            self.product.list_price, 0.0, places=2,
            msg="list_price must accept 0.0 as a valid sale price",
        )

    def test_18_update_with_large_price_values(self):
        """TC-18: The wizard must handle very large float values without
        overflow errors (boundary test for Float field)."""
        large_sale = 9_999_999.99
        large_cost = 8_000_000.00
        wizard = self._make_wizard(sale_price=large_sale, cost_price=large_cost)
        wizard.action_change_product_price()
        self.assertAlmostEqual(self.product.list_price, large_sale, places=2)
        self.assertAlmostEqual(self.product.standard_price, large_cost, places=2)


    def test_19_update_does_not_affect_other_products(self):
        """TC-19: Updating prices for self.product must NOT change the prices
        of any other product (self.product_b)."""
        original_sale_b = self.product_b.list_price
        original_cost_b = self.product_b.standard_price
        wizard = self._make_wizard(
            product=self.product, sale_price=999.0, cost_price=500.0
        )
        wizard.action_change_product_price()
        self.assertAlmostEqual(self.product_b.list_price, original_sale_b, places=2)
        self.assertAlmostEqual(self.product_b.standard_price, original_cost_b, places=2)

    def test_20_consecutive_updates_reflect_latest_values(self):
        """TC-20: Running action_change_product_price() twice on the same
        product with different values must persist only the second (latest)
        values — no stale caching."""
        # First update
        wizard1 = self._make_wizard(sale_price=110.0, cost_price=70.0)
        wizard1.action_change_product_price()
        self.assertAlmostEqual(self.product.list_price, 110.0, places=2)
        self.assertAlmostEqual(self.product.standard_price, 70.0, places=2)

        # Second update — should overwrite the first
        wizard2 = self._make_wizard(sale_price=180.0, cost_price=95.0)
        wizard2.action_change_product_price()
        self.assertAlmostEqual(
            self.product.list_price, 180.0, places=2,
            msg="Second update must overwrite first — list_price should be 180.0",
        )
        self.assertAlmostEqual(
            self.product.standard_price, 95.0, places=2,
            msg="Second update must overwrite first — standard_price should be 95.0",
        )
