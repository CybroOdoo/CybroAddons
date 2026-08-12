# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: K Sai Saran Varma(Contact : odoo@cybrosys.com)
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
###########################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestScrapManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestScrapManagement, cls).setUpClass()
        cls.company = cls.env.user.company_id

        # Create locations
        cls.location_src = cls.env['stock.location'].create({
            'name': 'Test Source Location',
            'usage': 'internal',
            'company_id': cls.company.id,
        })
        cls.location_scrap = cls.env['stock.location'].create({
            'name': 'Test Scrap Location',
            'usage': 'inventory',
            'scrap_location': True,
            'company_id': cls.company.id,
        })
        cls.location_dest = cls.env['stock.location'].create({
            'name': 'Test Dest Location',
            'usage': 'internal',
            'company_id': cls.company.id,
        })

        # Create products
        cls.product_component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'product',
        })
        cls.product_component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'type': 'product',
        })
        cls.product_finished = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'product',
        })

        # Create BOM
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_finished.product_tmpl_id.id,
            'product_id': cls.product_finished.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_component_1.id, 'product_qty': 2.0}),
                (0, 0, {'product_id': cls.product_component_2.id, 'product_qty': 3.0}),
            ]
        })

        # Add initial stock for finished product
        cls.env['stock.quant'].create({
            'product_id': cls.product_finished.id,
            'location_id': cls.location_src.id,
            'quantity': 10.0,
        })

    def test_01_scrap_management_flow(self):
        # 1. Create Scrap Order
        scrap_order = self.env['stock.scrap'].create({
            'product_id': self.product_finished.id,
            'scrap_qty': 2.0,
            'location_id': self.location_src.id,
            'scrap_location_id': self.location_scrap.id,
            'typ_of_reuse': 'dismantle',
            'bill_of_material_id': self.bom.id,
            'company_id': self.company.id,
        })

        scrap_order.do_scrap()
        self.assertEqual(scrap_order.state, 'done')

        # 2. Create Scrap Management Record
        scrap_management = self.env['scrap.management'].create({
            'scrap_order_id': scrap_order.id,
            'location_id': self.location_dest.id,
        })

        self.assertEqual(scrap_management.state, 'draft')

        # 3. Action Confirm
        scrap_management.action_confirm()
        self.assertEqual(scrap_management.state, 'confirm')
        self.assertEqual(len(scrap_management.scrap_management_line_ids), 2)

        for line in scrap_management.scrap_management_line_ids:
            if line.product_id == self.product_component_1:
                self.assertEqual(line.dismantle_qty, 4.0)  # 2.0 * 2.0
                line.useful_qty = 3.0
            elif line.product_id == self.product_component_2:
                self.assertEqual(line.dismantle_qty, 6.0)  # 2.0 * 3.0
                line.useful_qty = 1.0

        # 4. Action Done
        scrap_management.action_done()
        self.assertEqual(scrap_management.state, 'done')
        self.assertEqual(scrap_order.state_management, 'dismantled')

        # Check Product Moves Action
        action = scrap_management.action_product_moves()
        self.assertEqual(action['res_model'], 'stock.move.line')
        self.assertEqual(action['domain'][0][2], scrap_management.scrap_management_number)
