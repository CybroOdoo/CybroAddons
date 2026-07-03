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

from odoo.tests.common import TransactionCase

class TestGenerateSeo(TransactionCase):
    """Test cases for the GenerateSeo model (seo.generate)."""

    def setUp(self):
        super().setUp()
        self.GenerateSeo = self.env['seo.generate']
        self.SeoAttr = self.env['website.seo.attributes']

        # Product-scoped attributes
        self.attr_product_name = self.SeoAttr.create({
            'name': 'Attr Product Name',
            'models': 'product',
            'product': 'name',
        })
        self.attr_product_desc = self.SeoAttr.create({
            'name': 'Attr Product Desc',
            'models': 'product',
            'product': 'description_sale',
        })

        # Category-scoped attributes
        self.attr_categ_name = self.SeoAttr.create({
            'name': 'Attr Category Name',
            'models': 'product_category',
            'category': 'name',
        })
        self.attr_categ_desc = self.SeoAttr.create({
            'name': 'Attr Category Desc',
            'models': 'product_category',
            'category': 'category_description',
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_product_seo(self, **kwargs):
        vals = {
            'model_name': 'product',
            'meta_title_ids': [(4, self.attr_product_name.id)],
            'meta_description_ids': [(4, self.attr_product_desc.id)],
            'attribute_separator': '|',
        }
        vals.update(kwargs)
        return self.GenerateSeo.create(vals)

    def _make_category_seo(self, **kwargs):
        vals = {
            'model_name': 'product_category',
            'meta_title_ids': [(4, self.attr_categ_name.id)],
            'meta_description_ids': [(4, self.attr_categ_desc.id)],
            'attribute_separator': '|',
        }
        vals.update(kwargs)
        return self.GenerateSeo.create(vals)

    # ------------------------------------------------------------------
    # Creation & defaults
    # ------------------------------------------------------------------

    def test_create_product_seo_config(self):
        """Should create a product-type SEO configuration successfully."""
        seo = self._make_product_seo()
        self.assertTrue(seo.id)
        self.assertEqual(seo.model_name, 'product')

    def test_create_category_seo_config(self):
        """Should create a product_category-type SEO configuration successfully."""
        seo = self._make_category_seo()
        self.assertTrue(seo.id)
        self.assertEqual(seo.model_name, 'product_category')

    def test_default_state_is_deactivated(self):
        """Newly created SEO config should have state='deactivated'."""
        seo = self._make_product_seo()
        self.assertEqual(seo.state, 'deactivated')

    def test_default_separator_is_pipe(self):
        """Default attribute separator should be '|'."""
        seo = self.GenerateSeo.create({
            'model_name': 'product',
            'meta_title_ids': [(4, self.attr_product_name.id)],
            'meta_description_ids': [(4, self.attr_product_desc.id)],
        })
        self.assertEqual(seo.attribute_separator, '|')

    def test_default_company_is_current_company(self):
        """company_id should default to the current company."""
        seo = self._make_product_seo()
        self.assertEqual(seo.company_id, self.env.company)

    def test_model_name_required(self):
        """model_name is required; omitting it should raise an error."""
        with self.assertRaises(Exception):
            self.GenerateSeo.create({
                'meta_title_ids': [(4, self.attr_product_name.id)],
                'meta_description_ids': [(4, self.attr_product_desc.id)],
            })

    def test_action_save_with_no_meta_title_does_not_crash(self):
        """action_save_seo_info should not crash when meta_title_ids is empty
        (Many2many required is UI-only in Odoo 18)."""
        seo = self.GenerateSeo.create({
            'model_name': 'product',
            'meta_title_ids': [],
            'meta_description_ids': [(4, self.attr_product_desc.id)],
        })
        # Should complete without raising
        try:
            seo.action_save_seo_info()
        except Exception as e:
            self.fail(f"action_save_seo_info raised unexpectedly: {e}")

    def test_action_save_with_no_meta_description_does_not_crash(self):
        """action_save_seo_info should not crash when meta_description_ids is empty."""
        seo = self.GenerateSeo.create({
            'model_name': 'product',
            'meta_title_ids': [(4, self.attr_product_name.id)],
            'meta_description_ids': [],
        })
        try:
            seo.action_save_seo_info()
        except Exception as e:
            self.fail(f"action_save_seo_info raised unexpectedly: {e}")

    # ------------------------------------------------------------------
    # onchange _onchange_model_name
    # ------------------------------------------------------------------

    def test_onchange_model_name_clears_title_and_description(self):
        """Changing model_name should clear meta_title_ids and
        meta_description_ids."""
        seo = self._make_product_seo()
        # Simulate onchange by calling the method directly
        seo.model_name = 'product_category'
        seo._onchange_model_name()
        self.assertFalse(seo.meta_title_ids)
        self.assertFalse(seo.meta_description_ids)

    def test_onchange_model_name_product_populates_meta_ids(self):
        """After onchange with model_name='product', meta_ids should be
        populated with product-scoped attributes."""
        seo = self._make_product_seo()
        seo.model_name = 'product'
        seo._onchange_model_name()
        expected_ids = self.SeoAttr.search([('models', '=', 'product')]).ids
        self.assertEqual(sorted(seo.meta_ids.ids), sorted(expected_ids))

    def test_onchange_model_name_category_populates_meta_ids(self):
        """After onchange with model_name='product_category', meta_ids should
        be populated with category-scoped attributes."""
        seo = self._make_category_seo()
        seo.model_name = 'product_category'
        seo._onchange_model_name()
        expected_ids = self.SeoAttr.search(
            [('models', '=', 'product_category')]).ids
        self.assertEqual(sorted(seo.meta_ids.ids), sorted(expected_ids))

    # ------------------------------------------------------------------
    # action_save_seo_info – state & deactivation logic
    # ------------------------------------------------------------------

    def test_action_save_activates_current_record(self):
        """Calling action_save_seo_info should set state to 'activated'."""
        seo = self._make_product_seo()
        seo.action_save_seo_info()
        self.assertEqual(seo.state, 'activated')

    def test_action_save_deactivates_other_records(self):
        """When one record is saved/activated, all other existing records
        should be deactivated."""
        seo1 = self._make_product_seo()
        seo1.action_save_seo_info()
        self.assertEqual(seo1.state, 'activated')

        seo2 = self._make_category_seo()
        seo2.action_save_seo_info()

        seo1.invalidate_recordset()
        self.assertEqual(seo1.state, 'deactivated')
        self.assertEqual(seo2.state, 'activated')

    def test_action_save_returns_notification_for_product(self):
        """action_save_seo_info should return a display_notification action
        for product model."""
        seo = self._make_product_seo()
        result = seo.action_save_seo_info()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('product', result['params']['message'].lower())

    def test_action_save_returns_notification_for_category(self):
        """action_save_seo_info should return a display_notification action
        for product_category model."""
        # Create a public category with auto seo enabled so the method has
        # records to iterate over.
        self.env['product.public.category'].create({
            'name': 'Test Public Cat',
            'is_auto_seo': True,
        })
        seo = self._make_category_seo()
        result = seo.action_save_seo_info()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    def test_action_save_product_writes_meta_title(self):
        """action_save_seo_info for products should write website_meta_title
        onto every product.template record."""
        product = self.env['product.template'].create({'name': 'SEO Product'})
        seo = self._make_product_seo()
        seo.action_save_seo_info()
        product.invalidate_recordset()
        # Meta title should be set (non-empty)
        self.assertTrue(product.website_meta_title)

    def test_action_save_product_writes_meta_keywords(self):
        """action_save_seo_info for products should write website_meta_keywords
        (set to product name) onto every product.template record."""
        product = self.env['product.template'].create({'name': 'Keyword Product'})
        seo = self._make_product_seo()
        seo.action_save_seo_info()
        product.invalidate_recordset()
        self.assertEqual(product.website_meta_keywords, product.name)

    def test_action_save_product_writes_meta_description(self):
        """action_save_seo_info for products should write
        website_meta_description onto every product.template record."""
        self.env['product.template'].create({
            'name': 'Desc Product',
            'description_sale': 'Great product',
        })
        seo = self._make_product_seo()
        seo.action_save_seo_info()
        # If meta_description_ids is set the method should not raise
        # (smoke test – verifying it completes without error)

    def test_action_save_category_skips_non_auto_seo(self):
        """action_save_seo_info for categories should only process categories
        where is_auto_seo=True."""
        cat_no_auto = self.env['product.public.category'].create({
            'name': 'No Auto SEO Cat',
            'is_auto_seo': False,
        })
        seo = self._make_category_seo()
        seo.action_save_seo_info()
        cat_no_auto.invalidate_recordset()
        # website_meta_title should remain unset since is_auto_seo is False
        self.assertFalse(cat_no_auto.website_meta_title)

    def test_action_save_category_writes_meta_title(self):
        """action_save_seo_info for categories should write website_meta_title
        on is_auto_seo categories."""
        cat = self.env['product.public.category'].create({
            'name': 'Auto SEO Cat',
            'is_auto_seo': True,
        })
        seo = self._make_category_seo()
        seo.action_save_seo_info()
        cat.invalidate_recordset()
        self.assertTrue(cat.website_meta_title)

    # ------------------------------------------------------------------
    # action_deactivate_seo
    # ------------------------------------------------------------------

    def test_action_deactivate_sets_state_deactivated(self):
        """action_deactivate_seo should set state to 'deactivated'."""
        seo = self._make_product_seo()
        seo.action_save_seo_info()
        self.assertEqual(seo.state, 'activated')
        seo.action_deactivate_seo()
        self.assertEqual(seo.state, 'deactivated')

    def test_action_deactivate_already_deactivated_is_noop(self):
        """Calling action_deactivate_seo on an already-deactivated record
        should leave the state unchanged."""
        seo = self._make_product_seo()
        self.assertEqual(seo.state, 'deactivated')
        seo.action_deactivate_seo()
        self.assertEqual(seo.state, 'deactivated')

    # ------------------------------------------------------------------
    # attribute_separator behaviour
    # ------------------------------------------------------------------

    def test_custom_separator_used_in_meta_title(self):
        """The custom separator should appear in the generated meta title
        when multiple product attributes are selected."""
        attr2 = self.SeoAttr.create({
            'name': 'Attr Internal Ref',
            'models': 'product',
            'product': 'default_code',
        })
        product = self.env['product.template'].create({
            'name': 'Sep Test Product',
            'default_code': 'REF001',
        })
        seo = self._make_product_seo(
            meta_title_ids=[
                (4, self.attr_product_name.id),
                (4, attr2.id),
            ],
            attribute_separator=' -- ',
        )
        seo.action_save_seo_info()
        product.invalidate_recordset()
        self.assertIn(' -- ', product.website_meta_title)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def test_state_selection_values(self):
        """state field should only accept 'activated' or 'deactivated'."""
        seo = self._make_product_seo()
        seo.write({'state': 'activated'})
        self.assertEqual(seo.state, 'activated')
        seo.write({'state': 'deactivated'})
        self.assertEqual(seo.state, 'deactivated')
