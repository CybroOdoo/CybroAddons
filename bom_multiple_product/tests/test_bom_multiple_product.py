# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestBomMultipleProduct(TransactionCase):
    """Test cases for BOM Multiple Product Selection."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up environment variables
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create products
        cls.product_finished = cls.env['product.product'].create({
            'name': 'Finished Product A',
            'type': 'product',
            'list_price': 100.0,
        })
        
        cls.product_component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'product',
            'list_price': 10.0,
        })
        
        cls.product_component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'type': 'product',
            'list_price': 20.0,
        })
        
        # Create a basic BOM for action_select_products test
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product_finished.id,
            'product_tmpl_id': cls.product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

    def test_01_product_action_create_bom(self):
        """Test the action_create_bom method on product.product."""
        # Call the action on the product with context simulating multiple selection
        action = self.product_finished.with_context(
            active_ids=[self.product_component_1.id, self.product_component_2.id]
        ).action_create_bom()
        
        # Check action properties
        self.assertEqual(action.get('res_model'), 'product.bom', "Should open the product.bom wizard")
        self.assertEqual(action.get('type'), 'ir.actions.act_window', "Should return an act_window action")
        
        # Check context propagation
        expected_context_ids = [self.product_component_1.id, self.product_component_2.id]
        self.assertEqual(action.get('context', {}).get('default_product_ids'), expected_context_ids,
                         "Should pass active_ids to default_product_ids in context")

    def test_02_mrp_bom_action_select_products(self):
        """Test the action_select_products method on mrp.bom."""
        action = self.bom.action_select_products()
        
        # Check action properties
        self.assertEqual(action.get('res_model'), 'bom.products', "Should open the bom.products wizard")
        self.assertEqual(action.get('type'), 'ir.actions.act_window', "Should return an act_window action")
        
        # Check context propagation
        self.assertEqual(action.get('context', {}).get('default_bom_id'), self.bom.id,
                         "Should pass the bom id to default_bom_id in context")

    def test_03_wizard_bom_products_action_add_components(self):
        """Test adding components to an existing BOM using bom.products wizard."""
        # Initial check
        self.assertEqual(len(self.bom.bom_line_ids), 0, "BOM should initially have no lines")
        
        # Create wizard record
        wizard = self.env['bom.products'].create({
            'bom_id': self.bom.id,
            'product_ids': [(6, 0, [self.product_component_1.id, self.product_component_2.id])]
        })
        
        # Perform action
        wizard.action_add_components()
        
        # Verify components were added
        self.assertEqual(len(self.bom.bom_line_ids), 2, "Two components should be added to the BOM")
        added_product_ids = self.bom.bom_line_ids.mapped('product_id.id')
        self.assertIn(self.product_component_1.id, added_product_ids, "Component 1 should be in BOM lines")
        self.assertIn(self.product_component_2.id, added_product_ids, "Component 2 should be in BOM lines")
        
        # Check quantities are 1 by default
        for line in self.bom.bom_line_ids:
            self.assertEqual(line.product_qty, 1.0, "Default quantity for added components should be 1.0")

    def test_04_wizard_product_bom_action_create_bom(self):
        """Test creating a completely new BOM from the product.bom wizard."""
        # Get the uom_id (usually Unit by default for a new product, let's explicitly get it from the product)
        uom_id = self.product_finished.uom_id.id
        
        # Create wizard record
        wizard = self.env['product.bom'].create({
            'product_id': self.product_finished.id,
            'quantity': 5.0,
            'uom_id': uom_id,
            'bom_type': 'normal',
            'product_ids': [(6, 0, [self.product_component_1.id, self.product_component_2.id])]
        })
        
        # Perform action to create BOM
        action = wizard.action_create_bom()
        
        # Extract new BOM ID from the returned action
        new_bom_id = action.get('res_id')
        self.assertTrue(new_bom_id, "Action should return the ID of the newly created BOM")
        
        # Retrieve the newly created BOM
        new_bom = self.env['mrp.bom'].browse(new_bom_id)
        
        # Validate BOM header fields
        self.assertEqual(new_bom.product_id.id, self.product_finished.id, "BOM product should match")
        self.assertEqual(new_bom.product_qty, 5.0, "BOM quantity should match wizard quantity")
        self.assertEqual(new_bom.product_uom_id.id, uom_id, "BOM UoM should match wizard UoM")
        self.assertEqual(new_bom.type, 'normal', "BOM type should match wizard type")
        
        # Validate BOM lines
        self.assertEqual(len(new_bom.bom_line_ids), 2, "New BOM should have two lines")
        added_product_ids = new_bom.bom_line_ids.mapped('product_id.id')
        self.assertIn(self.product_component_1.id, added_product_ids, "Component 1 should be in BOM lines")
        self.assertIn(self.product_component_2.id, added_product_ids, "Component 2 should be in BOM lines")
