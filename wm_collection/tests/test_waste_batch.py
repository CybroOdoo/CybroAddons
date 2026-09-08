# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestWasteBatch(TransactionCase):
    """Unit tests verifying waste batch weight reconciliation and status transitions."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super(TestWasteBatch, cls).setUpClass()
        # Disable inspection and approval workflows during testing to prevent validation failures
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_approval', 'False')
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'False')

        # Create UoM if not exists
        cls.uom_unit = cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].search([('name', '=', 'Units')], limit=1)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].create({
                'name': 'Units',
                'relative_factor': 1.0,
            })

        # Create Warehouse
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
        })
        cls.location = cls.warehouse.lot_stock_id

        # Create Category
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'E-Waste',
            'code': 'EW',
        })

        # Create Products (one standard waste product, one with negative standard price/disposal fee)
        cls.waste_product = cls.env['product.product'].create({
            'name': 'Battery Waste Product',
            'is_waste_material': True,
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
            'standard_price': 0.0,
            'hazardous': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.disposal_product = cls.env['product.product'].create({
            'name': 'Hazardous Liquid Waste Product',
            'is_waste_material': True,
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
            'standard_price': 15.0,
            'hazardous': True,
            'wm_waste_category_id': cls.category.id,
        })

    def test_01_waste_batch_workflow(self):
        """
        Test the full flow: batch creation, quantity editing, manual reception,
        stock move check.
        """
        # Create a batch
        batch = self.env['waste.batch'].create({
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 100.0,
                    'uom_id': self.uom_unit.id,
                    'net_weight': 100.0,
                })
            ],
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
        })

        # Check fields
        self.assertEqual(batch.quantity, 100.0)
        self.assertEqual(batch.draft_quantity, 100.0)
        self.assertFalse(batch.is_received)
        self.assertEqual(batch.status, 'draft')

        # Check lines and lots
        self.assertEqual(len(batch.line_ids), 1)
        line = batch.line_ids[0]
        self.assertTrue(line.lot_id, "Lot ID should be generated upon batch creation")
        self.assertEqual(line.lot_id.name, batch.name)
        self.assertTrue(batch.hazardous)
        self.assertIn(self.category, batch.category_ids)

        # Quantity can be edited before reception (via the line)
        line.write({'quantity': 150.0})
        self.assertEqual(batch.quantity, 150.0)
        self.assertEqual(batch.draft_quantity, 150.0)

        # Step 1: Log batch arrival (truck showed up, lots assigned, no stock move yet)
        batch.action_receive_batch()
        self.assertFalse(batch.is_received)
        self.assertEqual(batch.status, 'arrived')

        # Step 2: Move waste into physical stock inventory
        batch.action_move_to_stock()

        # Check status and quantity behavior after stock move
        self.assertTrue(batch.is_received)
        self.assertEqual(batch.status, 'received')  # 'received' = stock moved into inventory

        # Since we completed the stock picking, let's verify stock quant contains the quantity
        quants = self.env['stock.quant'].search([
            ('product_id', '=', self.waste_product.id),
            ('location_id', '=', self.location.id),
            ('lot_id', '=', line.lot_id.id),
        ])
        self.assertEqual(sum(quants.mapped('quantity')), 150.0)
        self.assertEqual(batch.quantity, 150.0)

        # Double receive should raise an error
        with self.assertRaises(UserError):
            batch.action_receive_batch()

    def test_02_waste_costing_valuation(self):
        """
        Test standard price costing behavior with standard valuation settings.
        """
        self.assertEqual(self.waste_product.cost_method, 'standard')
        self.assertEqual(self.disposal_product.cost_method, 'standard')

        # Create batch for disposal product with standard cost
        batch = self.env['waste.batch'].create({
            'line_ids': [
                (0, 0, {
                    'product_id': self.disposal_product.id,
                    'quantity': 10.0,
                    'uom_id': self.uom_unit.id,
                    'net_weight': 10.0,
                })
            ],
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
        })

        self.disposal_product.categ_id.write({
            'property_valuation': 'real_time',
            'property_cost_method': 'standard',
        })

        self.disposal_product.write({'standard_price': 20.0})
        self.assertEqual(self.disposal_product.standard_price, 20.0)

        # Receive batch and move to stock
        batch.action_receive_batch()
        batch.action_move_to_stock()
        self.assertTrue(batch.is_received)

        moves = self.env['stock.move'].search([('origin', '=', batch.name)])
        self.assertTrue(moves)
        for move in moves:
            # Under standard valuation, verify Odoo's standard accounting lines are created normally
            aml_vals = move._get_account_move_line_vals()
            self.assertTrue(aml_vals)

    def test_03_failed_inspection_disposal(self):
        """
        Test failed inspection workflow: auto-creates disposal transfer to
        Landfill/Disposal in Ready state, batch status set to disposed.
        """
        # Enable inspection for this test
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'True')

        # Create landfill location if ref not loaded in test env
        landfill_loc = self.env.ref('wm_collection.stock_location_landfill', raise_if_not_found=False)
        if not landfill_loc:
            landfill_loc = self.env['stock.location'].create({
                'name': 'Landfill/Disposal',
                'usage': 'inventory',
            })

        batch = self.env['waste.batch'].create({
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 50.0,
                    'uom_id': self.uom_unit.id,
                    'net_weight': 50.0,
                })
            ],
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
        })
        # Start inspection
        batch.action_start_inspection()
        self.assertEqual(batch.status, 'inspection')
        inspection = self.env['wm.batch.inspection'].search([('batch_id', '=', batch.id)], limit=1)
        self.assertTrue(inspection)
        self.assertEqual(inspection.state, 'in_progress')

        # Fail inspection
        inspection.action_fail_inspection()

        # 1. Inspection state is failed
        self.assertEqual(inspection.state, 'failed')
        # 2. Batch status is disposed
        self.assertEqual(batch.status, 'disposed')

        # 3. Disposal picking created and linked via origin
        disposal_picking = self.env['stock.picking'].search([('origin', '=', batch.name)], limit=1)
        self.assertTrue(disposal_picking)
        self.assertEqual(disposal_picking.location_id, batch.location_id)
        self.assertEqual(disposal_picking.location_dest_id, landfill_loc)
        # 4. Picking is automatically validated to Done
        self.assertEqual(disposal_picking.state, 'done')

    def test_04_batch_inspection_gating(self):
        """
        Test batch inspection gating logic based on use_batch_inspection
        setting.
        """
        # (a) Setting enabled + no inspection -> receive blocked
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'True')
        batch_a = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 50.0,
                    'uom_id': self.uom_unit.id,
                })
            ]
        })
        with self.assertRaises(UserError) as cm:
            batch_a.action_receive_batch()
        self.assertIn("This batch requires inspection before it can be received into inventory", str(cm.exception))

        # (b) Setting enabled + passed inspection -> receive succeeds
        batch_b = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 50.0,
                    'uom_id': self.uom_unit.id,
                })
            ]
        })
        batch_b.action_start_inspection()
        inspection_b = self.env['wm.batch.inspection'].search([('batch_id', '=', batch_b.id)], limit=1)
        inspection_b.action_pass_inspection()
        self.assertEqual(inspection_b.state, 'passed')
        self.assertEqual(batch_b.inspection_state, 'passed')

        # Now action_receive_batch should succeed
        batch_b.action_receive_batch()
        self.assertEqual(batch_b.status, 'arrived')

        # (c) Setting enabled + failed inspection -> receive blocked
        batch_c = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 50.0,
                    'uom_id': self.uom_unit.id,
                })
            ]
        })
        batch_c.action_start_inspection()
        inspection_c = self.env['wm.batch.inspection'].search([('batch_id', '=', batch_c.id)], limit=1)
        inspection_c.action_fail_inspection()
        self.assertEqual(inspection_c.state, 'failed')
        self.assertEqual(batch_c.status, 'disposed')

        with self.assertRaises(UserError):
            batch_c.action_receive_batch()

        # (d) Setting disabled -> receive succeeds regardless of inspection state
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'False')
        batch_d = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.waste_product.id,
                    'quantity': 50.0,
                    'uom_id': self.uom_unit.id,
                })
            ]
        })
        # No inspection created, but setting is disabled -> receive succeeds
        batch_d.action_receive_batch()
        self.assertEqual(batch_d.status, 'arrived')
