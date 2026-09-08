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

from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestSortWizardCategoryInput(TransactionCase):
    """Unit tests verifying category-based input validation in the batch sort wizard."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Test Sort Category',
            'code': 'TSORTCAT',
        })
        cls.dest_location = cls.env['stock.location'].create({
            'name': 'Category Sorted Stock Location',
            'usage': 'internal',
        })
        cls.category_sort_config = cls.env['wm.waste.category.sort.config'].create({
            'category_id': cls.category.id,
            'dest_location_id': cls.dest_location.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Raw Waste Item',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'is_storable': True,
        })
        cls.sorted_product = cls.env['product.product'].create({
            'name': 'Test Sorted Output Item',
            'type': 'consu',
        })
        warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1) or cls.env['stock.warehouse'].search([], limit=1)
        cls.location = warehouse.lot_stock_id if warehouse else cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

        cls.batch = cls.env['waste.batch'].create({
            'category_id': cls.category.id,
            'warehouse_id': warehouse.id if warehouse else False,
            'location_id': cls.location.id,
            'draft_quantity': 200.0,
            'intake_weight': 200.0,
            'status': 'draft',
            'batch_type': 'collection',
            'line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'quantity': 200.0,
            })],
        })
        cls.batch.with_context(skip_inspection_check=True).action_receive_batch()

    def test_sort_wizard_category_input(self):
        """
        Sort wizard loads category sort config when batch has category_id set,
        output batch has batch_type=sorted_material.
        """
        wizard = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=self.batch.id).create({})
        self.assertTrue(wizard.line_ids, "Wizard should populate sort wizard lines")

        wiz_line = wizard.line_ids[0]
        self.assertEqual(wiz_line.dest_location_id, self.dest_location, "Wizard line should auto-load destination location from category sort config")

        wiz_line.write({'dest_product_id': self.sorted_product.id})

        action = wizard.action_confirm_sort()
        self.assertTrue(action, "Confirm sort should return an action")

        child_batch = self.env['waste.batch'].browse(action['res_id']) if action.get('res_id') else False
        if not child_batch and action.get('domain'):
            child_batch = self.env['waste.batch'].search(action['domain'], limit=1)

        self.assertTrue(child_batch, "Output sorted batch should be created")
        self.assertEqual(child_batch.batch_type, 'sorted_material', "Output batch must have batch_type set to 'sorted_material'")

        _logger.info('PASS: test_sort_wizard_category_input')
