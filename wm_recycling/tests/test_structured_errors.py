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
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_recycling')
class TestStructuredErrors(TransactionCase):
    """Unit tests verifying structured error isolation and exception handling in recycling."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.src_location = cls.warehouse.lot_stock_id
        cls.category = cls.env['wm.waste.category'].create({'name': 'Plastic Waste', 'code': 'PLAS'})
        cls.mat = cls.env['product.template'].create({
            'name': 'PET Plastic',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.product = cls.mat.product_variant_id
        cls.product.write({'is_storable': True})

        cls.batch = cls.env['waste.batch'].create({
            'name': 'WB/TEST/RECYCLING_ERR',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.src_location.id,
            'category_id': cls.category.id,
            'line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'quantity': 50.0,
            })]
        })
        cls.batch.with_context(skip_inspection_check=True).action_receive_batch()
        cls.batch.with_context(skip_inspection_check=True).action_move_to_stock()

        cls.recycling_order = cls.env['recycling.order'].create({
            'waste_batch_id': cls.batch.id,
            'product_id': cls.product.id,
            'line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'uom_id': cls.product.uom_id.id,
                'recovered_qty': 45.0,
                'dest_location_id': False,  # Missing destination location
            })],
        })
        cls.recycling_order.action_confirm()
        cls.recycling_order.action_start()

    def test_missing_destination_location_raises_user_error(self):
        """
        Executing recycling order action_done with missing dest_location_id
        raises UserError.
        """
        with self.assertRaises(UserError) as cm:
            self.recycling_order.action_done()
        self.assertIn("Missing destination stock location", str(cm.exception))
