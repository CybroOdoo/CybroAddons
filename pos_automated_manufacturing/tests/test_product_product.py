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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import common


class TestProductProduct(common.TransactionCase):
    """
    Test suite for checking product configurations in POS data loading.
    """
    def test_01_load_pos_data_fields(self):
        """Test that the automated manufacturing fields are added to POS data fields."""
        fields = self.env['product.product']._load_pos_data_fields({})
        self.assertIn('to_create_mrp', fields, "Field 'to_create_mrp' should be loaded in POS.")
        self.assertIn('create_mrp_done', fields, "Field 'create_mrp_done' should be loaded in POS.")

    def test_02_product_variant_fields_access(self):
        """Test accessing and writing automated manufacturing fields via product variant."""
        product = self.env['product.product'].create({
            'name': 'Test Variant Field Access',
            'type': 'consu',
        })
        self.assertFalse(product.to_create_mrp)
        self.assertFalse(product.create_mrp_done)

        # Create BoM so writing to_create_mrp succeeds
        component = self.env['product.product'].create({
            'name': 'Component Product',
            'type': 'consu',
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': component.id,
                'product_qty': 1.0,
            })],
        })

        product.write({'to_create_mrp': True, 'create_mrp_done': True})
        self.assertTrue(product.to_create_mrp)
        self.assertTrue(product.create_mrp_done)
        self.assertTrue(product.product_tmpl_id.to_create_mrp)

