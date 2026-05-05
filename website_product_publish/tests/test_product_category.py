# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Prasudhi A (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from odoo.tests import common

_LOGGER = logging.getLogger(__name__)


class TestProductCategory(common.TransactionCase):
    """ Test class for product category publish functionality """

    @classmethod
    def setUpClass(cls):
        super(TestProductCategory, cls).setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': "Test Category",
        })
        # Published product
        cls.product_1 = cls.env['product.template'].create({
            'name': 'Published Product',
            'categ_id': cls.category.id,
            'is_published': True,
            'sale_ok': True,
        })
        # Unpublished product
        cls.product_2 = cls.env['product.template'].create({
            'name': 'Unpublished Product',
            'categ_id': cls.category.id,
            'is_published': False,
            'sale_ok': True,
        })
        # Product not for sale (should be ignored in counts and publish all)
        cls.product_3 = cls.env['product.template'].create({
            'name': 'Internal Product',
            'categ_id': cls.category.id,
            'is_published': False,
            'sale_ok': False,
        })

    def test_compute_published_count(self):
        """Test if the counts are correctly computed"""
        self.category._compute_published_count()
        self.assertEqual(self.category.published_count, 1, "Should have 1 published product")
        self.assertEqual(self.category.unpublished_count, 1, "Should have 1 unpublished product (ignoring sale_ok=False)")

    def test_action_publish_all_products(self):
        """Test publishing all products in a category"""
        self.category.action_publish_all_products()
        self.assertTrue(self.product_1.is_published)
        self.assertTrue(self.product_2.is_published, "Unpublished product should now be published")
        self.assertFalse(self.product_3.is_published, "Product with sale_ok=False should remain unpublished")
