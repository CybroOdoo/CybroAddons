# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026+-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import TransactionCase, tagged
from unittest.mock import patch


@tagged('post_install', '-at_install')
class TestMrpSubstituteProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMrpSubstituteProduct, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'product',
        })
        
        cls.component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'product',
        })
        
        cls.substitute_product = cls.env['product.product'].create({
            'name': 'Substitute Product',
            'type': 'consu',
        })
        
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component_1.id,
                    'product_qty': 1.0,
                    'mrp_substitute_product_id': cls.substitute_product.id,
                })
            ]
        })

    def test_01_substitute_product_applied(self):
        """Test if the substitute product replaces the original component when it's out of stock."""
        # Ensure Component 1 has 0 qty
        self.assertEqual(self.component_1.qty_available, 0)
        
        # We need to mock free_qty of substitute_product to be >= required qty
        # because it is a consumable and normally doesn't have stock quants.
        with patch('odoo.addons.stock.models.product.ProductProduct.free_qty', new=10.0):
            mo = self.env['mrp.production'].create({
                'product_id': self.finished_product.id,
                'product_qty': 1.0,
                'bom_id': self.bom.id,
            })
            mo.action_confirm()
            
            # Check that the raw material is now the substitute product
            self.assertEqual(len(mo.move_raw_ids), 1)
            self.assertEqual(mo.move_raw_ids[0].product_id.id, self.substitute_product.id)

    def test_02_substitute_product_not_applied_component_in_stock(self):
        """Test that substitute is not applied if the main component is in stock."""
        # Add stock to Component 1
        stock_location = self.env.ref('stock.stock_location_stock')
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        move = self.env['stock.move'].create({
            'name': 'Add component qty',
            'product_id': self.component_1.id,
            'product_uom_qty': 10,
            'product_uom': self.component_1.uom_id.id,
            'location_id': supplier_location.id,
            'location_dest_id': stock_location.id,
        })
        move._action_confirm()
        move._action_assign()
        move.move_line_ids.write({'quantity': 10})
        move.picked = True
        move._action_done()

        self.assertTrue(self.component_1.qty_available > 0)
        
        with patch('odoo.addons.stock.models.product.ProductProduct.free_qty', new=10.0):
            mo = self.env['mrp.production'].create({
                'product_id': self.finished_product.id,
                'product_qty': 1.0,
                'bom_id': self.bom.id,
            })
            mo.action_confirm()
            
            # Check that the raw material is still the original component
            self.assertEqual(len(mo.move_raw_ids), 1)
            self.assertEqual(mo.move_raw_ids[0].product_id.id, self.component_1.id)

    def test_03_substitute_product_not_applied_substitute_insufficient_qty(self):
        """Test that substitute is not applied if the substitute product doesn't have enough free_qty."""
        # We need another component with 0 qty
        component_3 = self.env['product.product'].create({
            'name': 'Component 3',
            'type': 'product',
        })
        
        bom_2 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': component_3.id,
                    'product_qty': 5.0, # requires 5
                    'mrp_substitute_product_id': self.substitute_product.id,
                })
            ]
        })
        
        # mock free_qty of substitute_product to be less than required qty (e.g., 2 < 5)
        with patch('odoo.addons.stock.models.product.ProductProduct.free_qty', new=2.0):
            mo = self.env['mrp.production'].create({
                'product_id': self.finished_product.id,
                'product_qty': 1.0,
                'bom_id': bom_2.id,
            })
            mo.action_confirm()
            
            # Check that the raw material is still the original component
            self.assertEqual(len(mo.move_raw_ids), 1)
            self.assertEqual(mo.move_raw_ids[0].product_id.id, component_3.id)

    def test_04_substitute_product_not_applied_wrong_type(self):
        """Test that substitute is not applied if the substitute product is not a consumable."""
        component_4 = self.env['product.product'].create({
            'name': 'Component 4',
            'type': 'product',
        })
        
        substitute_product_wrong_type = self.env['product.product'].create({
            'name': 'Substitute Product Storable',
            'type': 'product', # Not consu
        })
        
        bom_3 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': component_4.id,
                    'product_qty': 1.0,
                    'mrp_substitute_product_id': substitute_product_wrong_type.id,
                })
            ]
        })
        
        with patch('odoo.addons.stock.models.product.ProductProduct.free_qty', new=10.0):
            mo = self.env['mrp.production'].create({
                'product_id': self.finished_product.id,
                'product_qty': 1.0,
                'bom_id': bom_3.id,
            })
            mo.action_confirm()
            
            # Check that the raw material is still the original component
            self.assertEqual(len(mo.move_raw_ids), 1)
            self.assertEqual(mo.move_raw_ids[0].product_id.id, component_4.id)
