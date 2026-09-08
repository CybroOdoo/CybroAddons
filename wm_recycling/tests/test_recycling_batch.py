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


class TestRecyclingBatch(TransactionCase):
    """Unit tests verifying waste batch recycling workflows, yield calculation, and stock moves."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super(TestRecyclingBatch, cls).setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_approval', 'False')
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'False')

        cls.uom_unit = cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].search([('name', '=', 'Units')], limit=1)

        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Recycling WH',
            'code': 'TRWH',
        })
        cls.location = cls.warehouse.lot_stock_id

        cls.material_a = cls.env['product.product'].create({
            'name': 'PET Plastic Bottle',
            'is_waste_material': True,
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        })
        cls.material_b = cls.env['product.product'].create({
            'name': 'Aluminum Can',
            'is_waste_material': True,
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        })

    def test_single_material_batch_allows_recycling_order(self):
        """
        Batch with single line or same material in all lines allows creating
        recycling order.
        """
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.material_a.id,
                    'quantity': 50.0,
                })
            ]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        self.assertFalse(batch.has_multiple_materials)
        action = batch.action_create_recycling_order()
        self.assertEqual(action.get('res_model'), 'recycling.order')

    def test_multiple_different_materials_batch_prevents_recycling_order(self):
        """
        Batch with multiple different waste materials prevents creating
        recycling order.
        """
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.material_a.id,
                    'quantity': 50.0,
                }),
                (0, 0, {
                    'product_id': self.material_b.id,
                    'quantity': 30.0,
                })
            ]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        self.assertTrue(batch.has_multiple_materials)
        with self.assertRaises(UserError):
            batch.action_create_recycling_order()

    def test_recycling_input_qty_reflects_remaining_qty(self):
        """
        Recycling order input_qty updates dynamically based on batch line
        remaining_qty.
        """
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'quantity': 100.0,
            })]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
        })
        self.assertEqual(order.input_qty, 100.0)

        # Simulate partial sort (40kg sorted out, 60kg remaining)
        batch.line_ids[0].sorted_qty = 40.0
        self.assertEqual(batch.line_ids[0].remaining_qty, 60.0)
        order._compute_input_qty()
        self.assertEqual(order.input_qty, 60.0)

    def test_recycling_process_loss_moves_residue_to_scrap(self):
        """
        Completing a recycling order moves unrecovered residue to the scrap
        location.
        """
        dest_loc = self.env['stock.location'].create({
            'name': 'Recycled Output Bin',
            'usage': 'internal',
        })
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'quantity': 100.0,
            })]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'uom_id': self.uom_unit.id,
                'dest_location_id': dest_loc.id,
                'expected_qty': 100.0,
                'recovered_qty': 60.0,
            })]
        })
        order.action_confirm()
        order.action_start()
        order.action_done()

        self.assertEqual(order.state, 'done')
        self.assertEqual(order.input_qty, 100.0)
        self.assertEqual(order.total_recovered_qty, 60.0)

        # Check process loss move to scrap location for 40.0 kg residue
        scrap_loc = self.env.ref('stock.stock_location_scrapped', raise_if_not_found=False)
        if not scrap_loc:
            scrap_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)

        loss_move = self.env['stock.move'].search([
            ('origin', '=', 'Process Loss: %s' % order.name),
            ('location_dest_id', '=', scrap_loc.id),
        ])
        self.assertTrue(loss_move, "A stock move for process loss to scrap location should exist")
        self.assertAlmostEqual(loss_move.product_uom_qty, 40.0)

    def test_recycling_order_on_sorted_material_child_batch(self):
        """
        Sorted child batches created via sorting wizard are received in stock
        and can be recycled.
        """
        self.env['wm.waste.category'].create({'name': 'Recycling Test Cat', 'code': 'RTCAT'})
        dest_loc = self.env['stock.location'].create({'name': 'Sorted Bin', 'usage': 'internal'})
        self.env['wm.waste.material.sort.config'].create({
            'material_id': self.material_a.product_tmpl_id.id,
            'dest_product_id': self.material_a.id,
            'dest_location_id': dest_loc.id,
        })
        parent_batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'quantity': 100.0,
            })]
        })
        parent_batch.action_receive_batch()
        parent_batch.action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=parent_batch.id).create({})
        action = wizard.action_confirm_sort()

        child_batch = self.env['waste.batch'].browse(action['res_id'])
        self.assertTrue(child_batch.is_received, "Child sorted batch must have is_received=True")
        self.assertEqual(child_batch.batch_type, 'sorted_material')

        order = self.env['recycling.order'].create({
            'waste_batch_id': child_batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'uom_id': self.uom_unit.id,
                'dest_location_id': dest_loc.id,
                'expected_qty': 100.0,
                'recovered_qty': 90.0,
            })]
        })
        self.assertEqual(order.input_qty, 100.0)
        order.action_confirm()
        order.action_start()
        order.action_done()
        self.assertEqual(order.state, 'done')

    def test_full_recycling_lifecycle_and_sale_order(self):
        """
        Test the end-to-end recycling order lifecycle including computations,
        stock movement, sale order creation, and sale order smart button.
        """
        dest_loc = self.env['stock.location'].create({
            'name': 'Pellets Output Bin',
            'usage': 'internal',
        })
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'quantity': 100.0,
            })]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'uom_id': self.uom_unit.id,
                'dest_location_id': dest_loc.id,
                'expected_qty': 100.0,
                'recovered_qty': 80.0,
                'sale_price': 15.0,
            })]
        })
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.input_qty, 100.0)
        self.assertAlmostEqual(order.overall_recovery_rate, 80.0)
        self.assertAlmostEqual(order.total_recovered_value, 1200.0)

        # Confirm order
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        self.assertEqual(batch.status, 'sorting')

        # Start processing
        order.action_start()
        self.assertEqual(order.state, 'in_progress')

        # Mark done
        order.action_done()
        self.assertEqual(order.state, 'done')
        self.assertEqual(batch.status, 'recycled')

        # Create Sale Order
        action = order.action_create_sale_order()
        self.assertEqual(action.get('res_model'), 'sale.order')
        context = action.get('context', {})
        self.assertEqual(context.get('default_origin'), order.name)

        # Create actual SO from context to verify smart button & view sales
        partner = self.env['res.partner'].create({'name': 'Test Recycling Buyer'})
        so = self.env['sale.order'].create({
            'partner_id': partner.id,
            'origin': order.name,
            'order_line': context.get('default_order_line', []),
        })
        order._compute_sale_count()
        self.assertEqual(order.sale_order_count, 1)

        view_action = order.action_view_sales()
        self.assertIn(so.id, view_action['domain'][0][2])

    def test_cancel_and_reset_draft_workflow(self):
        """
        Test cancelling a recycling order returns linked batch to received state
        and allows resetting back to draft.
        """
        dest_loc = self.env['stock.location'].create({
            'name': 'Cancel Test Bin',
            'usage': 'internal',
        })
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'quantity': 50.0,
            })]
        })
        batch.action_receive_batch()
        batch.action_move_to_stock()

        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.material_a.id,
                'uom_id': self.uom_unit.id,
                'dest_location_id': dest_loc.id,
                'expected_qty': 50.0,
                'recovered_qty': 40.0,
            })]
        })
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        self.assertEqual(batch.status, 'sorting')

        # Cancel
        order.action_cancel()
        self.assertEqual(order.state, 'cancelled')
        self.assertEqual(batch.status, 'received')

        # Reset to draft
        order.action_reset_draft()
        self.assertEqual(order.state, 'draft')
        self.assertEqual(batch.status, 'received')
