# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPackageCategory(TransactionCase):

    def test_create_package_category(self):
        category = self.env['package.category'].create({
            'name': 'Fragile',
        })

        self.assertEqual(category.name, 'Fragile')
        self.assertEqual(category._name, 'package.category')
