# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestProductBrand(TransactionCase):

    def test_product_brand_creation_and_count(self):
        """Test product brand creation and product templates count computation."""
        brand = self.env['product.brand'].create({
            'name': 'Test Brand',
        })
        # Trigger compute
        brand._compute_product_count()
        self.assertEqual(brand.product_count, '0')
        
        # Create product template with brand
        product_tmpl = self.env['product.template'].create({
            'name': 'Branded Product',
            'type': 'consu',
            'brand_id': brand.id,
        })
        
        brand._compute_product_count()
        self.assertEqual(brand.product_count, '1')
