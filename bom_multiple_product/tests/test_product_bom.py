# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductBom(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductBom, cls).setUpClass()
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })
        cls.component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'consu',
        })
        cls.component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'type': 'consu',
        })

    def test_action_create_bom(self):
        """Test action_create_bom on product.bom wizard creates a new mrp.bom successfully"""
        # Create transient wizard
        wizard = self.env['product.bom'].create({
            'product_id': self.finished_product.id,
            'quantity': 5.0,
            'uom_id': self.finished_product.uom_id.id,
            'product_ids': [(6, 0, [self.component_1.id, self.component_2.id])],
            'bom_type': 'normal',
        })

        action = wizard.action_create_bom()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.bom')
        self.assertEqual(action.get('view_mode'), 'form')
        
        bom_id = action.get('res_id')
        self.assertTrue(bom_id)

        bom = self.env['mrp.bom'].browse(bom_id)
        self.assertTrue(bom.exists())
        self.assertEqual(bom.product_id, self.finished_product)
        self.assertEqual(bom.product_tmpl_id, self.finished_product.product_tmpl_id)
        self.assertEqual(bom.product_qty, 5.0)
        self.assertEqual(bom.product_uom_id, self.finished_product.uom_id)
        self.assertEqual(bom.type, 'normal')
        
        self.assertEqual(len(bom.bom_line_ids), 2)
        added_products = bom.bom_line_ids.mapped('product_id')
        self.assertIn(self.component_1, added_products)
        self.assertIn(self.component_2, added_products)
        for line in bom.bom_line_ids:
            self.assertEqual(line.product_qty, 1.0)
