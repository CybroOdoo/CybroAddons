# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    def test_package_category_can_be_assigned_to_product(self):
        category = self.env['package.category'].create({
            'name': 'Cold Chain',
        })
        product = self.env['product.product'].create({
            'name': 'Vaccine',
            'is_storable': True,
            'package_category_id': category.id,
        })

        self.assertEqual(product.package_category_id, category)

    def test_package_split_value_follows_config_parameter(self):
        product = self.env['product.product'].create({
            'name': 'Pack Split Product',
            'is_storable': True,
        })
        config = self.env['ir.config_parameter'].sudo()

        config.set_param('package_split.enable_package_split', True)
        product.invalidate_recordset(['package_split_value'])
        self.assertTrue(product.package_split_value)

        config.set_param('package_split.enable_package_split', False)
        product.invalidate_recordset(['package_split_value'])
        self.assertFalse(product.package_split_value)
