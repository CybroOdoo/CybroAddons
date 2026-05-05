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
from odoo.tests import common


class TestProductPublishWizard(common.TransactionCase):
    """ Test class for product publish wizard """

    @classmethod
    def setUpClass(cls):
        super(TestProductPublishWizard, cls).setUpClass()
        cls.product_1 = cls.env['product.template'].create({
            'name': 'Wizard Product 1',
            'is_published': False,
            'sale_ok': True,
        })
        cls.product_2 = cls.env['product.template'].create({
            'name': 'Wizard Product 2',
            'is_published': True,
            'sale_ok': True,
        })
        cls.product_3 = cls.env['product.template'].create({
            'name': 'Internal Wizard Product',
            'is_published': False,
            'sale_ok': False,
        })

    def test_action_product_multi_publish(self):
        """Test multi-publishing products via wizard"""
        wizard = self.env['product.publish'].with_context(
            active_ids=[self.product_1.id, self.product_2.id, self.product_3.id],
            active_model='product.template'
        ).create({})
        
        wizard.action_product_multi_publish()
        
        self.assertTrue(self.product_1.is_published, "Product 1 should be published")
        self.assertTrue(self.product_2.is_published, "Product 2 should remain published")
        self.assertFalse(self.product_3.is_published, "Product 3 (sale_ok=False) should not be published")

    def test_action_product_multi_unpublish(self):
        """Test multi-unpublishing products via wizard"""
        wizard = self.env['product.publish'].with_context(
            active_ids=[self.product_1.id, self.product_2.id, self.product_3.id],
            active_model='product.template'
        ).create({})
        
        # Publish product 3 manually to test it doesn't get UNpublished if sale_ok=False
        self.product_3.is_published = True
        
        wizard.action_product_multi_unpublish()
        
        self.assertFalse(self.product_1.is_published, "Product 1 should remain unpublished")
        self.assertFalse(self.product_2.is_published, "Product 2 should be unpublished")
        self.assertTrue(self.product_3.is_published, "Product 3 (sale_ok=False) should remains published as it is skipped")
