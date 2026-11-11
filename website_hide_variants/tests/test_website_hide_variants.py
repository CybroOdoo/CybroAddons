# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website_sale.tests.common import MockRequest


@tagged('post_install', '-at_install')
class TestWebsiteHideVariants(TransactionCase):
    """Test suite for hiding product variants on the website,

    covering the hide flag, the product views, the variant possibility
    check, the combination info, the add to cart guard and the accessory
    products.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref('base.default_website')
        cls.color_attribute = cls.env['product.attribute'].create({
            'name': 'Test Hide Color',
            'create_variant': 'always',
            'value_ids': [
                Command.create({'name': 'Test Red'}),
                Command.create({'name': 'Test Blue'}),
            ],
        })
        cls.red, cls.blue = cls.color_attribute.value_ids
        cls.template = cls.env['product.template'].create({
            'name': 'Test Hide Variant Shirt',
            'list_price': 20.0,
            'sale_ok': True,
            'is_published': True,
            'website_id': cls.website.id,
            'attribute_line_ids': [Command.create({
                'attribute_id': cls.color_attribute.id,
                'value_ids': [Command.set(cls.color_attribute.value_ids.ids)],
            })],
        })
        cls.red_variant = cls._get_variant(cls.red)
        cls.blue_variant = cls._get_variant(cls.blue)
        cls.red_variant.is_website_hide_variants = True

    @classmethod
    def _get_variant(cls, value):
        """Return the variant of the test template for the given value."""
        return cls.template.product_variant_ids.filtered(
            lambda p: p.product_template_attribute_value_ids
            .product_attribute_value_id == value)

    @classmethod
    def _get_ptav(cls, value):
        """Return the template attribute value of the given value."""
        return cls.template.attribute_line_ids.product_template_value_ids \
            .filtered(lambda v: v.product_attribute_value_id == value)

    def _website_env(self, record):
        """Return the record in a website request like context."""
        return record.with_context(website_id=self.website.id)

    def _get_combination_info(self, record, method='_get_combination_info',
                              **kwargs):
        """Return the combination info computed inside a website request."""
        with MockRequest(self.env, website=self.website):
            return getattr(self._website_env(record), method)(**kwargs)

    def test_01_flag_field_attributes(self):
        """Verify the hide flag is a boolean which is off by default."""
        field = self.env['product.product']._fields['is_website_hide_variants']
        self.assertEqual(field.type, 'boolean')
        self.assertEqual(field.string, 'Hide on Website')
        self.assertFalse(self.blue_variant.is_website_hide_variants)
        self.assertTrue(self.red_variant.is_website_hide_variants)

    def test_02_variant_list_view_shows_flag(self):
        """Verify the variant list view displays the hide flag."""
        view = self.env.ref('product.product_product_tree_view')
        arch = self.env['product.product'].get_view(view_id=view.id)['arch']
        self.assertIn('is_website_hide_variants', arch)

    def test_03_variant_form_view_shows_flag(self):
        """Verify the variant form view displays the hide flag."""
        view = self.env.ref('product.product_normal_form_view')
        arch = self.env['product.product'].get_view(view_id=view.id)['arch']
        self.assertIn('is_website_hide_variants', arch)

    def test_04_hidden_variant_not_possible_on_website(self):
        """Verify a hidden variant is not possible on the website."""
        self.assertFalse(
            self._website_env(self.red_variant)._is_variant_possible())
        self.assertTrue(
            self._website_env(self.blue_variant)._is_variant_possible())

    def test_05_hidden_variant_possible_in_backend(self):
        """Verify a hidden variant is still possible outside the website."""
        self.assertTrue(self.red_variant._is_variant_possible())
        self.assertTrue(self.blue_variant._is_variant_possible())

    def test_06_possible_variants_exclude_hidden(self):
        """Verify the website possible variants exclude hidden variants."""
        website_variants = self._website_env(
            self.template)._get_possible_variants()
        self.assertNotIn(self.red_variant, website_variants)
        self.assertIn(self.blue_variant, website_variants)
        self.assertIn(self.red_variant, self.template._get_possible_variants())

    def test_07_combination_info_hidden_variant(self):
        """Verify the combination info of a hidden variant is flagged and
        marked as not possible.
        """
        info = self._get_combination_info(
            self.template, combination=self._get_ptav(self.red))
        self.assertEqual(info['product_id'], self.red_variant.id)
        self.assertTrue(info['is_website_hide_variants'])
        self.assertFalse(info['is_combination_possible'])

    def test_08_combination_info_visible_variant(self):
        """Verify the combination info of a visible variant is unchanged."""
        info = self._get_combination_info(
            self.template, combination=self._get_ptav(self.blue))
        self.assertEqual(info['product_id'], self.blue_variant.id)
        self.assertFalse(info['is_website_hide_variants'])
        self.assertTrue(info['is_combination_possible'])

    def test_09_combination_info_accepts_pricelist(self):
        """Verify the pricelist and fiscal position arguments of
        website_sale are still accepted.
        """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test Hide Variant Pricelist',
        })
        info = self._website_env(self.template)._get_combination_info(
            combination=self._get_ptav(self.red),
            pricelist=pricelist,
            fiscal_position=self.env['account.fiscal.position'],
        )
        self.assertTrue(info['is_website_hide_variants'])

    def test_10_combination_info_variant(self):
        """Verify the variant combination info helper reports the flag."""
        info = self._get_combination_info(
            self.red_variant, method='_get_combination_info_variant')
        self.assertTrue(info['is_website_hide_variants'])
        info = self._get_combination_info(
            self.blue_variant, method='_get_combination_info_variant')
        self.assertFalse(info['is_website_hide_variants'])

    def test_11_template_only_combination_info(self):
        """Verify the template only combination info has no hidden flag."""
        info = self._get_combination_info(self.template, only_template=True)
        self.assertFalse(info['product_id'])
        self.assertFalse(info['is_website_hide_variants'])

    def test_12_hidden_variant_cannot_be_added_to_cart(self):
        """Verify a hidden variant can not be added to the cart."""
        self.assertFalse(
            self._website_env(self.red_variant)._is_add_to_cart_allowed())
        self.assertTrue(
            self._website_env(self.blue_variant)._is_add_to_cart_allowed())

    def test_13_unhiding_variant_restores_it(self):
        """Verify unchecking the flag makes the variant available again."""
        self.red_variant.is_website_hide_variants = False
        self.assertTrue(
            self._website_env(self.red_variant)._is_variant_possible())
        self.assertTrue(
            self._website_env(self.red_variant)._is_add_to_cart_allowed())
        info = self._get_combination_info(
            self.template, combination=self._get_ptav(self.red))
        self.assertFalse(info['is_website_hide_variants'])

    def test_14_accessory_products_exclude_hidden(self):
        """Verify hidden variants are removed from the website accessory
        products, and shown again once the flag is unchecked.
        """
        accessory_template = self.env['product.template'].create({
            'name': 'Test Hide Variant Accessory Holder',
            'is_published': True,
            'accessory_product_ids': [Command.set(
                (self.red_variant | self.blue_variant).ids)],
        })
        website_accessories = self._website_env(
            accessory_template)._get_website_accessory_product()
        self.assertNotIn(self.red_variant, website_accessories)
        self.assertIn(self.blue_variant, website_accessories)

        self.red_variant.is_website_hide_variants = False
        website_accessories = self._website_env(
            accessory_template)._get_website_accessory_product()
        self.assertIn(self.red_variant, website_accessories)
