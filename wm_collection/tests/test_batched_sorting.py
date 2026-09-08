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
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_collection')
class TestBatchedSorting(TransactionCase):
    """Unit tests verifying batch segregation into single-material child batches."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.src_location = cls.warehouse.lot_stock_id
        cls.dest_location = cls.env['stock.location'].create({
            'name': 'Sorted Materials Yard',
            'usage': 'internal',
            'location_id': cls.src_location.location_id.id,
        })

        cls.category = cls.env['wm.waste.category'].create({'name': 'Mixed Recyclables', 'code': 'MIX'})
        cls.materials = []
        cls.products = []

        for i in range(1, 6):
            mat = cls.env['product.template'].create({
                'name': f'Material {i}',
                'is_waste_material': True,
                'wm_waste_category_id': cls.category.id,
            })
            cls.materials.append(mat)
            prod = mat.product_variant_id
            prod.write({'is_storable': True})
            cls.products.append(prod)

        cls.batch = cls.env['waste.batch'].create({
            'name': 'WB/TEST/5MAT',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.src_location.id,
            'category_id': cls.category.id,
            'line_ids': [(0, 0, {
                'product_id': prod.id,
                'quantity': 100.0,
            }) for prod in cls.products]
        })
        cls.batch.with_context(skip_inspection_check=True).action_receive_batch()
        cls.batch.with_context(skip_inspection_check=True).action_move_to_stock()

    def test_sorting_5_materials_batches_pickings(self):
        """
        Sorting a batch with 5 materials in per_material mode produces 5 child
        batches but only 2 stock pickings total (1 for source->production, 1
        for production->dest).
        """
        initial_picking_count = self.env['stock.picking'].search_count([('origin', 'like', self.batch.name)])

        wizard = self.env['waste.batch.sort.wizard'].create({
            'batch_id': self.batch.id,
            'output_batch_mode': 'per_material',
            'line_ids': [(0, 0, {
                'batch_line_id': line.id,
                'sort_qty': 100.0,
                'dest_product_id': line.product_id.id,
                'dest_location_id': self.dest_location.id,
            }) for line in self.batch.line_ids]
        })
        wizard.action_confirm_sort()

        child_batches = self.batch.sorted_batch_ids
        self.assertEqual(len(child_batches), 5, "Should create 5 distinct child batches (1 per material).")

        new_pickings = self.env['stock.picking'].search([('origin', 'like', self.batch.name)])
        additional_pickings = len(new_pickings) - initial_picking_count

        # 1 incoming picking from receive_batch/move_to_stock, plus 2 pickings during batched sort = 3 total pickings linked to batch
        self.assertLessEqual(additional_pickings, 2, "Should create at most 2 stock pickings (1 for source->production, 1 for production->dest) for all 5 materials instead of 10.")

        # Verify quantities and child batch details
        for child in child_batches:
            self.assertEqual(child.draft_quantity, 100.0)
            self.assertTrue(child.is_received)
            self.assertEqual(child.status, 'received')
            self.assertEqual(child.location_id, self.dest_location)

        self.assertEqual(self.batch.sorting_progress, 100.0)
        self.assertEqual(self.batch.status, 'sorted')

    def test_dispose_fully_sorted_parent_raises_user_error(self):
        """
        1. Disposing a fully-sorted parent with live children raises UserError.
        """
        parent_batch = self.env['waste.batch'].create({
            'name': 'WB/TEST/FULLY_SORTED',
            'warehouse_id': self.warehouse.id,
            'location_id': self.src_location.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {
                'product_id': self.products[0].id,
                'quantity': 50.0,
            }), (0, 0, {
                'product_id': self.products[1].id,
                'quantity': 50.0,
            })]
        })
        parent_batch.with_context(skip_inspection_check=True).action_receive_batch()
        parent_batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].create({
            'batch_id': parent_batch.id,
            'output_batch_mode': 'per_material',
            'line_ids': [(0, 0, {
                'batch_line_id': line.id,
                'sort_qty': line.quantity,
                'dest_product_id': line.product_id.id,
                'dest_location_id': self.dest_location.id,
            }) for line in parent_batch.line_ids]
        })
        wizard.action_confirm_sort()
        self.assertEqual(parent_batch.status, 'sorted')
        self.assertEqual(len(parent_batch.sorted_batch_ids), 2)

        from odoo.exceptions import UserError
        with self.assertRaises(UserError) as cm:
            parent_batch.action_dispose_batch()
        self.assertIn("This batch has been fully sorted into child batches", str(cm.exception))

    def test_dispose_partially_sorted_parent_succeeds(self):
        """
        2. Disposing a partially-sorted parent (some remaining_qty left) still
        scraps correctly and succeeds.
        """
        parent_batch = self.env['waste.batch'].create({
            'name': 'WB/TEST/PARTIAL_SORT',
            'warehouse_id': self.warehouse.id,
            'location_id': self.src_location.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {
                'product_id': self.products[0].id,
                'quantity': 100.0,
            })]
        })
        parent_batch.with_context(skip_inspection_check=True).action_receive_batch()
        parent_batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].create({
            'batch_id': parent_batch.id,
            'output_batch_mode': 'per_material',
            'line_ids': [(0, 0, {
                'batch_line_id': parent_batch.line_ids[0].id,
                'sort_qty': 40.0,
                'dest_product_id': parent_batch.line_ids[0].product_id.id,
                'dest_location_id': self.dest_location.id,
            })]
        })
        wizard.action_confirm_sort()
        self.assertEqual(parent_batch.status, 'sorting')
        self.assertEqual(parent_batch.line_ids[0].remaining_qty, 60.0)

        # Disposing the partially sorted parent should succeed and move remaining 60.0 to scrap
        parent_batch.action_dispose_batch()
        self.assertEqual(parent_batch.status, 'disposed')

    def test_children_all_disposed_rolls_parent_to_disposed(self):
        """
        3. Disposing all child batches of a parent as 'disposed' rolls the
        parent up to 'disposed', not 'sorted'.
        """
        parent_batch = self.env['waste.batch'].create({
            'name': 'WB/TEST/ROLLUP_DISPOSED',
            'warehouse_id': self.warehouse.id,
            'location_id': self.src_location.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {
                'product_id': self.products[0].id,
                'quantity': 50.0,
            }), (0, 0, {
                'product_id': self.products[1].id,
                'quantity': 50.0,
            })]
        })
        parent_batch.with_context(skip_inspection_check=True).action_receive_batch()
        parent_batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].create({
            'batch_id': parent_batch.id,
            'output_batch_mode': 'per_material',
            'line_ids': [(0, 0, {
                'batch_line_id': line.id,
                'sort_qty': line.quantity,
                'dest_product_id': line.product_id.id,
                'dest_location_id': self.dest_location.id,
            }) for line in parent_batch.line_ids]
        })
        wizard.action_confirm_sort()
        self.assertEqual(parent_batch.status, 'sorted')

        children = parent_batch.sorted_batch_ids
        self.assertEqual(len(children), 2)

        # Dispose child 1
        children[0].action_dispose_batch()
        self.assertEqual(children[0].status, 'disposed')
        self.assertEqual(parent_batch.status, 'sorted')  # child 2 still received

        # Dispose child 2
        children[1].action_dispose_batch()
        self.assertEqual(children[1].status, 'disposed')
        # Parent should now roll up to 'disposed', not 'sorted'
        self.assertEqual(parent_batch.status, 'disposed')

    def test_children_all_recycled_rolls_parent_to_recycled(self):
        """
        4. Disposing all child batches as 'recycled' still rolls the parent up
        to 'recycled'.
        """
        parent_batch = self.env['waste.batch'].create({
            'name': 'WB/TEST/ROLLUP_RECYCLED',
            'warehouse_id': self.warehouse.id,
            'location_id': self.src_location.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {
                'product_id': self.products[0].id,
                'quantity': 50.0,
            }), (0, 0, {
                'product_id': self.products[1].id,
                'quantity': 50.0,
            })]
        })
        parent_batch.with_context(skip_inspection_check=True).action_receive_batch()
        parent_batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].create({
            'batch_id': parent_batch.id,
            'output_batch_mode': 'per_material',
            'line_ids': [(0, 0, {
                'batch_line_id': line.id,
                'sort_qty': line.quantity,
                'dest_product_id': line.product_id.id,
                'dest_location_id': self.dest_location.id,
            }) for line in parent_batch.line_ids]
        })
        wizard.action_confirm_sort()
        self.assertEqual(parent_batch.status, 'sorted')

        children = parent_batch.sorted_batch_ids
        self.assertEqual(len(children), 2)

        # Mark both children as recycled
        children[0].write({'status': 'recycled'})
        self.assertEqual(parent_batch.status, 'sorted')

        children[1].write({'status': 'recycled'})
        self.assertEqual(parent_batch.status, 'recycled')
