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
import logging

from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestWasteBatchWorkflow(TransactionCase):
    """Unit tests verifying end-to-end waste batch intake, inspection, and sorting workflows."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Workflow Test Category',
            'code': 'WKFLCAT',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Workflow Raw Material',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'is_storable': True,
        })
        cls.dest_location = cls.env['stock.location'].create({
            'name': 'Sorted Yard Stream A',
            'usage': 'internal',
        })
        cls.category_sort_config = cls.env['wm.waste.category.sort.config'].create({
            'category_id': cls.category.id,
            'dest_location_id': cls.dest_location.id,
        })
        warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1) or cls.env['stock.warehouse'].search([], limit=1)
        cls.warehouse = warehouse
        cls.location = warehouse.lot_stock_id if warehouse else cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

    def test_category_batch_intake_and_auto_line_resolution(self):
        """
        Batch created without line_ids auto-resolves line from category on
        stock move.
        """
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'intake_weight': 500.0,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'batch_type': 'collection',
            'sorting_status': 'unsorted',
        })
        self.assertEqual(batch.draft_quantity, 500.0)
        self.assertFalse(batch.line_ids, "Initial batch line_ids should be empty")

        batch.with_context(skip_inspection_check=True).action_move_to_stock()

        self.assertTrue(batch.is_received, "Batch should be marked received")
        self.assertEqual(batch.status, 'received')
        self.assertTrue(batch.line_ids, "Default line should be auto-created during stock reception")
        self.assertEqual(batch.line_ids[0].quantity, 500.0)
        self.assertEqual(batch.weight_variance, 0.0)
        _logger.info('PASS: test_category_batch_intake_and_auto_line_resolution')

    def test_sorting_status_and_child_batch_type(self):
        """
        Sorting a received collection batch updates sorting_status and creates
        sorted_material child batch.
        """
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'intake_weight': 300.0,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'batch_type': 'collection',
            'sorting_status': 'unsorted',
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 300.0,
            })],
        })
        batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=batch.id).create({})
        action = wizard.action_confirm_sort()

        child_batch = self.env['waste.batch'].browse(action['res_id']) if action.get('res_id') else False
        if not child_batch and action.get('domain'):
            child_batch = self.env['waste.batch'].search(action['domain'], limit=1)

        self.assertTrue(child_batch)
        self.assertEqual(child_batch.batch_type, 'sorted_material')
        self.assertEqual(child_batch.sorting_status, 'sorted')
        self.assertEqual(batch.sorting_status, 'sorted')
        self.assertEqual(batch.status, 'sorted')
        _logger.info('PASS: test_sorting_status_and_child_batch_type')

    def test_waste_batch_disposal(self):
        """
        Disposing a batch updates status to disposed and blocks duplicate
        disposal.
        """
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'draft_quantity': 100.0,
        })
        batch.action_dispose_batch()
        self.assertEqual(batch.status, 'disposed')

        with self.assertRaises(UserError):
            batch.action_dispose_batch()
        _logger.info('PASS: test_waste_batch_disposal')

    def test_product_creation_and_filtering_for_category_batch(self):
        """
        New waste material created from batch line inherits batch category_id.
        """
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'draft_quantity': 150.0,
        })
        new_product = self.env['product.product'].with_context({
            'default_is_waste_material': True,
            'default_wm_waste_category_id': batch.category_id.id,
        }).create({
            'name': 'New Category Material',
        })
        self.assertTrue(new_product.is_waste_material)
        self.assertEqual(new_product.wm_waste_category_id, self.category)

        line = self.env['waste.batch.line'].create({
            'batch_id': batch.id,
            'product_id': new_product.id,
            'quantity': 150.0,
        })
        self.assertEqual(line.category_id, self.category)
        _logger.info('PASS: test_product_creation_and_filtering_for_category_batch')

    def test_duplicate_product_prevention_on_batch(self):
        """
        Adding the same waste product multiple times to a batch raises
        ValidationError.
        """
        from odoo.exceptions import ValidationError
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
        })
        self.env['waste.batch.line'].create({
            'batch_id': batch.id,
            'product_id': self.product.id,
            'quantity': 100.0,
        })

        with self.assertRaises(ValidationError):
            self.env['waste.batch.line'].create({
                'batch_id': batch.id,
                'product_id': self.product.id,
                'quantity': 50.0,
            })
        _logger.info('PASS: test_duplicate_product_prevention_on_batch')

    def test_consolidated_sorting_mode(self):
        """
        Sorting multiple lines with output_batch_mode='consolidated' produces 1
        consolidated output batch.
        """
        prod2 = self.env['product.product'].create({
            'name': 'Workflow Raw Material 2',
            'is_waste_material': True,
            'wm_waste_category_id': self.category.id,
            'is_storable': True,
        })
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'intake_weight': 400.0,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'batch_type': 'collection',
            'sorting_status': 'unsorted',
            'line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 250.0}),
                (0, 0, {'product_id': prod2.id, 'quantity': 150.0}),
            ],
        })
        batch.with_context(skip_inspection_check=True).action_move_to_stock()

        wizard = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=batch.id).create({
            'output_batch_mode': 'consolidated',
        })
        action = wizard.action_confirm_sort()

        child_batch = self.env['waste.batch'].browse(action['res_id'])
        self.assertEqual(len(child_batch), 1, "Consolidated sort mode must produce exactly 1 child batch")
        self.assertEqual(len(child_batch.line_ids), 2, "Consolidated child batch must contain both sorted material lines")
        self.assertEqual(child_batch.draft_quantity, 400.0)
        self.assertEqual(batch.sorting_status, 'sorted')
        _logger.info('PASS: test_consolidated_sorting_mode')

    def test_single_material_auto_sort_valid_status(self):
        """
        Single material batch auto-sort updates status to 'sorted' and
        sorting_status to 'sorted' without error.
        """
        self.env['wm.waste.material.sort.config'].create({
            'material_id': self.product.product_tmpl_id.id,
            'dest_product_id': self.product.id,
            'dest_location_id': self.dest_location.id,
        })
        batch = self.env['waste.batch'].create({
            'category_id': self.category.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'batch_type': 'collection',
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 100.0,
            })],
        })
        batch.with_context(skip_inspection_check=True).action_move_to_stock()
        self.assertEqual(batch.status, 'received')

        batch.action_sort_batch()
        self.assertEqual(batch.status, 'sorted')
        self.assertEqual(batch.sorting_status, 'sorted')
        _logger.info('PASS: test_single_material_auto_sort_valid_status')
