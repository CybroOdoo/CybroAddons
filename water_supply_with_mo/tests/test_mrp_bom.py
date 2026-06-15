# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'water_supply_with_mo')
class TestMrpBom(TransactionCase):

    def test_onchange_product_tmpl_id(self):
        """Test that _onchange_product_tmpl_id updates product_id correctly."""
        # Create a product template
        template = self.env['product.template'].create({
            'name': 'Test Water Template',
            'type': 'consu',
        })
        # Find the product.product associated with the template
        product = self.env['product.product'].search([
            ('product_tmpl_id', '=', template.id)
        ], limit=1)
        self.assertTrue(product)

        # Create a new BOM in memory to simulate user UI behavior
        bom = self.env['mrp.bom'].new({
            'product_tmpl_id': template.id,
        })
        
        # Trigger the onchange
        bom._onchange_product_tmpl_id()
        
        # Verify the product_id is set correctly to the template's product
        self.assertEqual(bom.product_id, product)
