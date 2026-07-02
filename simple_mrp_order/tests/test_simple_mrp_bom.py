# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase

class TestSimpleMRPBom(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSimpleMRPBom, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
            'is_storable': True,
        })

    def test_bom_creation(self):
        """Test basic BOM creation and line propagation"""
        bom = self.env['simple.mrp.bom'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
            'uom_id': self.product.uom_id.id,
            'line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 5.0,
                'uom_id': self.component.uom_id.id,
            })]
        })
        self.assertEqual(bom.product_id, self.product)
        self.assertEqual(len(bom.line_ids), 1)
        self.assertEqual(bom.line_ids[0].product_qty, 5.0)

    def test_bom_onchange_product(self):
        """Test onchange_product_id in BOM"""
        bom = self.env['simple.mrp.bom'].new({'product_id': self.product.id})
        bom._onchange_product_id()
        self.assertEqual(bom.uom_id, self.product.uom_id)

    def test_bom_line_onchange_product(self):
        """Test onchange_product_id in BOM line"""
        bom_line = self.env['simple.mrp.bom.line'].new({'product_id': self.component.id})
        bom_line.onchange_product_id()
        self.assertEqual(bom_line.uom_id, self.component.uom_id)
