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
from odoo.tests.common import TransactionCase

class TestProductProduct(TransactionCase):

    def setUp(self):
        super(TestProductProduct, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Variant',
            'is_website_hide_variants': False,
        })
        self.website = self.env['website'].create({'name': 'Test Website'})

    def test_01_is_variant_possible_normal(self):
        """Test variant is possible when not hidden."""
        # Internal use
        self.assertTrue(self.product._is_variant_possible())
        # Website use
        self.assertTrue(self.product.with_context(website_id=self.website.id)._is_variant_possible())

    def test_02_is_variant_possible_hidden(self):
        """Test variant is impossible on website when hidden."""
        self.product.is_website_hide_variants = True
        # Internal use (should still be possible)
        self.assertTrue(self.product._is_variant_possible())
        # Website use (should be impossible)
        self.assertFalse(self.product.with_context(website_id=self.website.id)._is_variant_possible())
