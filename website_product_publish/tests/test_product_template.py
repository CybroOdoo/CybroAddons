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
from odoo import Command
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Template = cls.env['product.template']
        cls.product_template = Template.create({
            'name': 'Test Product',
            'is_published': True,
            'list_price': 750,
        })
        cls.second_product = Template.create({
            'name': 'Second Product',
            'is_published': False,
            'list_price': 100,
        })
        cls.not_for_sale = Template.create({
            'name': 'Not For Sale Product',
            'sale_ok': False,
            'is_published': False,
        })

    # ------------------------------------------------------------------
    # Product form buttons
    # ------------------------------------------------------------------
    def test_action_published(self):
        """action_published() must set is_published to True."""
        self.product_template.write({'is_published': False})
        self.product_template.action_published()
        self.assertTrue(self.product_template.is_published)

    def test_action_unpublished(self):
        """action_unpublished() must set is_published to False."""
        self.product_template.write({'is_published': True})
        self.product_template.action_unpublished()
        self.assertFalse(self.product_template.is_published)

    def test_quick_publish_products_unpublishes(self):
        """quick_publish_products() toggles published -> unpublished."""
        self.product_template.write({'is_published': True})
        self.product_template.quick_publish_products()
        self.assertFalse(self.product_template.is_published)

    def test_quick_publish_products_publishes(self):
        """quick_publish_products() toggles unpublished -> published."""
        self.product_template.write({'is_published': False})
        self.product_template.quick_publish_products()
        self.assertTrue(self.product_template.is_published)

    def test_quick_publish_products_multiple(self):
        """Each record in the recordset is toggled individually."""
        products = self.product_template | self.second_product
        products.quick_publish_products()
        self.assertFalse(self.product_template.is_published)
        self.assertTrue(self.second_product.is_published)

    def test_quick_publish_products_returns_reload(self):
        """quick_publish_products() asks the client to reload."""
        result = self.product_template.quick_publish_products()
        self.assertEqual(result, {
            'type': 'ir.actions.client',
            'tag': 'reload',
        })

    # ------------------------------------------------------------------
    # action_publish -> wizard
    # ------------------------------------------------------------------
    def test_action_publish_returns_wizard_action(self):
        """action_publish() opens the wizard with products preselected."""
        products = self.product_template | self.second_product
        action = products.action_publish()
        view = self.env.ref(
            'website_product_publish.product_publish_view_form')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.publish')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['view_id'], view.id)
        self.assertEqual(
            action['context']['default_product_ids'],
            [Command.set(products.ids)])

    def test_wizard_default_products_from_context(self):
        """Wizard picks the products from the action context."""
        products = self.product_template | self.second_product
        action = products.action_publish()
        wizard = self.env['product.publish'].with_context(
            **action['context']).create({})
        self.assertEqual(wizard.product_ids, products)

    # ------------------------------------------------------------------
    # Wizard
    # ------------------------------------------------------------------
    def _create_wizard(self, products):
        return self.env['product.publish'].create({
            'product_ids': [Command.set(products.ids)],
        })

    def test_wizard_multi_publish(self):
        """Wizard action_product_multi_publish publishes sale_ok products."""
        self.product_template.write({'is_published': False})
        wizard = self._create_wizard(self.product_template)
        wizard.action_product_multi_publish()
        self.assertTrue(
            self.product_template.is_published,
            "Wizard should publish the selected product")

    def test_wizard_multi_unpublish(self):
        """Wizard action_product_multi_unpublish unpublishes sale_ok products."""
        self.product_template.write({'is_published': True})
        wizard = self._create_wizard(self.product_template)
        wizard.action_product_multi_unpublish()
        self.assertFalse(
            self.product_template.is_published,
            "Wizard should unpublish the selected product")

    def test_wizard_publish_multiple_products(self):
        """Wizard publishes every selected product."""
        self.product_template.write({'is_published': False})
        products = self.product_template | self.second_product
        self._create_wizard(products).action_product_multi_publish()
        self.assertTrue(self.product_template.is_published)
        self.assertTrue(self.second_product.is_published)

    def test_wizard_unpublish_multiple_products(self):
        """Wizard unpublishes every selected product."""
        self.second_product.write({'is_published': True})
        products = self.product_template | self.second_product
        self._create_wizard(products).action_product_multi_unpublish()
        self.assertFalse(self.product_template.is_published)
        self.assertFalse(self.second_product.is_published)

    def test_wizard_publish_skips_not_sale_ok(self):
        """Products with sale_ok=False are not published by the wizard."""
        products = self.second_product | self.not_for_sale
        self._create_wizard(products).action_product_multi_publish()
        self.assertTrue(self.second_product.is_published)
        self.assertFalse(self.not_for_sale.is_published)

    def test_wizard_only_affects_selected_products(self):
        """Products outside the selection keep their state."""
        self.product_template.write({'is_published': True})
        self._create_wizard(self.second_product).action_product_multi_publish()
        self.assertTrue(self.second_product.is_published)
        self.assertTrue(self.product_template.is_published)

        self._create_wizard(self.second_product).action_product_multi_unpublish()
        self.assertFalse(self.second_product.is_published)
        self.assertTrue(self.product_template.is_published)

    def test_wizard_with_no_products(self):
        """Wizard with an empty selection must not fail."""
        wizard = self.env['product.publish'].create({})
        wizard.action_product_multi_publish()
        wizard.action_product_multi_unpublish()
