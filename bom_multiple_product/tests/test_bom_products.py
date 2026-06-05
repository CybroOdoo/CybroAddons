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
class TestBomProducts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBomProducts, cls).setUpClass()
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.finished_product.id,
            'product_tmpl_id': cls.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        cls.component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'consu',
        })
        cls.component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'type': 'consu',
        })

    def test_action_add_components(self):
        """Test action_add_components on bom.products adds components to mrp.bom"""
        # Initially there should be no bom lines
        self.assertEqual(len(self.bom.bom_line_ids), 0)

        # Create the transient wizard
        wizard = self.env['bom.products'].create({
            'bom_id': self.bom.id,
            'product_ids': [(6, 0, [self.component_1.id, self.component_2.id])],
        })

        wizard.action_add_components()

        self.assertEqual(len(self.bom.bom_line_ids), 2)
        added_products = self.bom.bom_line_ids.mapped('product_id')
        self.assertIn(self.component_1, added_products)
        self.assertIn(self.component_2, added_products)
        for line in self.bom.bom_line_ids:
            self.assertEqual(line.product_qty, 1.0)
