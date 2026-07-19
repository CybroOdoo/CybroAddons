# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
################################################################################
from odoo import Command
from odoo.tests.common import TransactionCase

class TestProductTemplate(TransactionCase):

    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.template = self.env['product.template'].create({
            'name': 'Test Template',
            'type': 'product',
        })
        self.variant = self.template.product_variant_id
        self.website = self.env['website'].create({'name': 'Test Website'})

    def test_01_get_combination_info_hidden(self):
        """Test combination info reflects hidden status."""
        self.variant.is_website_hide_variants = True
        info = self.template._get_combination_info(product_id=self.variant.id)
        self.assertTrue(info['is_website_hide_variants'])
        self.assertFalse(info['is_combination_possible'])

    def test_02_get_combination_info_visible(self):
        """Test combination info reflect visible status."""
        self.variant.is_website_hide_variants = False
        info = self.template._get_combination_info(product_id=self.variant.id)
        self.assertFalse(info['is_website_hide_variants'])
        self.assertTrue(info['is_combination_possible'])

    def test_03_get_website_accessory_product_filtering(self):
        """Test accessory products are filtered on website."""
        accessory_product = self.env['product.product'].create({
            'name': 'Accessory',
            'is_website_hide_variants': True,
        })
        self.template.accessory_product_ids = [Command.link(accessory_product.id)]
        
        # Internal context (no filtering)
        internal_accessories = self.template._get_website_accessory_product()
        self.assertIn(accessory_product, internal_accessories)
        
        # Website context (filtering)
        website_accessories = self.template.with_context(website_id=self.website.id)._get_website_accessory_product()
        self.assertNotIn(accessory_product, website_accessories)
